"""validate_site.py   checks the built site (dist/) against the data and the standing rules. Exit code 1 if anything fails.

Run after `npm run build`:  python -X utf8 tools/validate_site.py
"""
import json
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DATA = ROOT / "src" / "data"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
yt = json.loads((DATA / "youtube.json").read_text(encoding="utf-8"))
fails, warns, passes = [], [], []


def check(ok, name, detail=""):
    (passes if ok else fails).append(f"{name}{(': ' + detail) if detail and not ok else ''}")


def warn(ok, name, detail=""):
    if not ok:
        warns.append(f"{name}: {detail}")


pages = {p.relative_to(DIST).as_posix(): p for p in DIST.rglob("*.html")}
html = {k: p.read_text(encoding="utf-8") for k, p in pages.items()}


def without_transcript(h):
    """the narration is shown as spoken in the video and the study notes as written, so words in them are judged separately from the site's own text"""
    i = h.find('id="p-tr"')
    if i >= 0:
        m = re.search(r'id="p-(?!tr")[a-z]+" role="tabpanel"', h[i + 10:])
        h = h[:i] + (h[i + 10 + m.start():] if m else "")
    a = h.find('<div class="prose"')
    if a >= 0:
        b = h.find('<div class="pn"', a)
        h = h[:a] + (h[b:] if b > 0 else "")
    return h


def text_of(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)))


# ---------------------------------------------------------------- page inventory
n_mod = sum(len(c["modules"]) for c in site["courses"])
n_notes = sum(len(c["notes"] or []) for c in site["courses"])
expected = 1 + len(site["institutes"]) + len(site["courses"]) + n_mod + n_notes + 6   # home, institutes, courses, modules, notes, search/plan/about/disclaimer/privacy/404
check(len(pages) == expected, "page count", f"{len(pages)} built, {expected} expected")
for c in site["courses"]:
    check(f"{c['institute']}/{c['slug']}/index.html" in pages, f"{c['slug']} course page")
    for m in c["modules"]:
        check(f"{c['institute']}/{c['slug']}/video/{m['slug']}/index.html" in pages, f"{c['slug']} module {m['num']} page")
    for n in c["notes"] or []:
        check(f"{c['institute']}/{c['slug']}/notes/{n['slug']}/index.html" in pages, f"{c['slug']} note {n['num']} page")

# ---------------------------------------------------------------- videos: every id is on its page and public
for c in site["courses"]:
    for m in c["modules"]:
        h = html.get(f"{c['institute']}/{c['slug']}/video/{m['slug']}/index.html", "")
        for p in m["parts"]:
            check(p["id"] in h, f"{c['slug']} {m['num']} part {p['part']} video id on the page")
            meta = yt.get(p["id"])
            check(bool(meta) and meta["privacy"] == "public" and meta["embeddable"], f"{c['slug']} {m['num']} part {p['part']} public and embeddable on YouTube")
            tr = json.loads((DATA / "transcripts" / c["slug"] / f"{m['num']}.json").read_text(encoding="utf-8")).get(str(p["part"]), [])
            check(len(tr) > 0, f"{c['slug']} {m['num']} part {p['part']} has a transcript")
        if m["deck"]:
            f = DIST / m["deck"]
            check(f.exists() and abs(f.stat().st_size / 1024 - m["deck_kb"]) < 2, f"{c['slug']} {m['num']} deck file", str(f))

# ---------------------------------------------------------------- study notes: everything of the source is on the page
nbad = []
for c in site["courses"]:
    for n in c["notes"] or []:
        k = n["check"]
        h = html.get(f"{c['institute']}/{c['slug']}/notes/{n['slug']}/index.html", "")
        ratio = k["page_words"] / max(1, k["src_words"])
        if not 0.97 <= ratio <= 1.12: nbad.append(f"{c['slug']} {n['num']}: words {k['src_words']} -> {k['page_words']}")
        for a_, b_ in (("src_tables", "tables"), ("src_images", "images"), ("src_scenario", "scenario"), ("src_recall", "recall"), ("src_sections", "sections")):
            if k[a_] != k[b_]: nbad.append(f"{c['slug']} {n['num']}: {b_} {k[a_]} -> {k[b_]}")
        n_fig, n_tab, n_qa = h.count('<figure class="fig">'), h.count("<table>"), h.count('class="qa')
        if n_fig != k["src_images"]: nbad.append(f"{c['slug']} {n['num']}: {n_fig} figures on the page, {k['src_images']} in the source")
        if n_tab != k["src_tables"]: nbad.append(f"{c['slug']} {n['num']}: {n_tab} tables on the page, {k['src_tables']} in the source")
        if n_qa != k["src_scenario"] + k["src_recall"]: nbad.append(f"{c['slug']} {n['num']}: {n_qa} questions on the page, {k['src_scenario'] + k['src_recall']} in the source")
        for fig in re.findall(r'<img src="([^"]+)" alt="[^"]*" loading="lazy"><figcaption>', h):
            if not (DIST / fig.lstrip("/")).exists(): nbad.append(f"{c['slug']} {n['num']}: diagram file missing {fig}")
check(not nbad, "study notes carry all text, tables, diagrams, questions and sections of their sources", "; ".join(nbad[:6]) + f" ({len(nbad)} problems)")
tot = {k: sum(n["check"][k] for c in site["courses"] for n in (c["notes"] or [])) for k in ("images", "tables", "scenario", "recall")}
print("notes carry", tot)

# ---------------------------------------------------------------- per-page basics
titles, bad = Counter(), []
for k, h in html.items():
    t = re.search(r"<title>(.*?)</title>", h, flags=re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', h)
    title = unescape(t.group(1)).strip() if t else ""
    titles[title] += 1
    h1 = re.findall(r"<h1[ >]", h)
    if not title: bad.append(f"{k}: no title")
    if not d or len(d.group(1)) < 40: bad.append(f"{k}: description missing or short")
    if len(h1) != 1: bad.append(f"{k}: {len(h1)} h1")
    if 'rel="canonical"' not in h: bad.append(f"{k}: no canonical link")
    if 'lang="en"' not in h: bad.append(f"{k}: no lang")
    if 'data-theme="light"' not in h or 'data-theme-set="dark"' not in h or 'data-theme-set="light"' not in h: bad.append(f"{k}: light default or the theme switch missing")
    for im in re.findall(r"<img\b[^>]*>", h):
        if " alt=" not in im: bad.append(f"{k}: image without alt: {im[:70]}")
    if "independent learning site" not in h: bad.append(f"{k}: independence notice missing")
    for pat in (r"\[object Object\]", r"\bNaN\b", r"lorem ipsum", r"\bTODO\b"):
        if re.search(pat, text_of(without_transcript(h))): bad.append(f"{k}: contains '{pat}'")
    # standing rules for what a visitor reads in the title, the description and the headline
    head = " ".join([title, d.group(1) if d else "", " ".join(re.findall(r"<h1[^>]*>(.*?)</h1>", h, flags=re.S))])
    if re.search(r"\b20[12]\d\b", re.sub(r"<[^>]+>", "", head)): bad.append(f"{k}: a year in the title, description or headline")
check(not bad, "per-page checks (title, description, one h1, canonical, lang, light default and switch, alt text, notice, no placeholders, no year in the head)", "; ".join(bad[:8]) + (f" (+{len(bad) - 8} more)" if len(bad) > 8 else ""))
dups = [t for t, n in titles.items() if n > 1]
check(not dups, "unique page titles", str(dups[:3]))

# ---------------------------------------------------------------- words we never use
hits = [(k, m.group(0)) for k, h in html.items() for m in re.finditer(r"certified", text_of(without_transcript(h)), flags=re.I)]
check(not hits, "the word 'certified' does not appear in the site's own text, titles or descriptions", str(hits[:3]))
spoken = sorted({k.split("/")[1] + " " + k.split("/")[3][:2] for k, h in html.items() if ("/video/" in k or "/notes/" in k) and re.search(r"certified", text_of(h), flags=re.I) and not re.search(r"certified", text_of(without_transcript(h)), flags=re.I)})
warn(not spoken, "the word 'certified' is in the narration (shown as spoken in the transcript) or in the study notes (as written) of", ", ".join(spoken))
years = sorted({k.split("/")[1] + " " + k.split("/")[3][:2] for k, h in html.items() if "/video/" in k and re.search(r"\b20[12]\d\b", text_of(h))})
warn(not years, "a year is spoken in the narration of", ", ".join(years))

# ---------------------------------------------------------------- links and files
broken = []
for k, h in html.items():
    base = "/" + k.rsplit("index.html", 1)[0] if k.endswith("index.html") else "/" + k
    scan = re.sub(r"<script(?![^>]*\bsrc=)[^>]*>.*?</script>", " ", h, flags=re.S)       # script bodies are code, not links
    for attr, url in re.findall(r'\b(href|src)="([^"]+)"', scan):
        if url.startswith(("http", "mailto:", "data:", "#", "tel:")):
            continue
        path = url.split("#")[0].split("?")[0]
        if not path:
            continue
        if not path.startswith("/"):
            path = base + path
        f = DIST / path.lstrip("/")
        if not (f.is_file() or (f / "index.html").is_file()):
            broken.append(f"{k} -> {url}")
check(not broken, "internal links and images resolve", "; ".join(sorted(set(broken))[:6]) + f" ({len(set(broken))} broken)")

# in-page anchors of the notes (table of contents)
bad_anchor = []
for c in site["courses"]:
    for n in c["notes"] or []:
        h = html.get(f"{c['institute']}/{c['slug']}/notes/{n['slug']}/index.html", "")
        for a in re.findall(r'<a href="#([^"]+)"', h):
            if f'id="{a}"' not in h:
                bad_anchor.append(f"{n['num']}#{a}")
check(not bad_anchor, "table-of-contents anchors exist", str(bad_anchor[:5]))

# ---------------------------------------------------------------- structured data, sitemap, search index, robots
bad_ld = 0
for k, h in html.items():
    for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, flags=re.S):
        try:
            json.loads(unescape(blob))
        except Exception:
            bad_ld += 1
check(bad_ld == 0, "JSON-LD blocks parse", f"{bad_ld} invalid")
sm = "".join(p.read_text(encoding="utf-8") for p in DIST.glob("sitemap-*.xml"))
check(sm.count("<loc>") >= len(pages) - 1, "sitemap lists the pages", f"{sm.count('<loc>')} urls for {len(pages)} pages")
check((DIST / "robots.txt").exists(), "robots.txt")
pf = DIST / "pagefind" / "pagefind-entry.json"
if pf.exists():
    e = json.loads(pf.read_text(encoding="utf-8"))
    n_idx = sum(l["page_count"] for l in e["languages"].values())
    check(n_idx == 1 + 0 + len(site["courses"]) + n_mod + n_notes or n_idx > 0, "search index built", f"{n_idx} pages")
    check(n_idx == len(site["courses"]) + n_mod + n_notes, "search index covers courses, modules and notes", f"{n_idx} indexed, {len(site['courses']) + n_mod + n_notes} expected")
else:
    check(False, "search index built", "dist/pagefind missing (run npm run build)")

# ---------------------------------------------------------------- nothing private in the output
leak = []
# personal details (the owner's name, employer ...) are listed in a private file that is not published
PRIVATE = ROOT / "tools" / "_private" / "personal_terms.txt"
PERSONAL = tuple(x.strip() for x in PRIVATE.read_text(encoding="utf-8").splitlines() if x.strip()) if PRIVATE.exists() else ()
for f in DIST.rglob("*"):
    if f.is_file() and f.suffix.lower() in (".html", ".js", ".json", ".css", ".txt", ".xml"):
        s = f.read_text(encoding="utf-8", errors="ignore")
        for pat in ("client_secret", "youtube_token", "refresh_token", "ya29.", "AIza", "D:\\\\Certifications", "D:/Certifications", "usamaalam@gmail.com" ) + PERSONAL:
            if pat in s:
                leak.append(f"{f.relative_to(DIST).as_posix()}: {pat}")
check(not leak, "no secrets, local paths or the owner's email address in the output", "; ".join(leak[:5]))
pdfs = [p.relative_to(DIST).as_posix() for p in DIST.rglob("*.pdf")]
check(not pdfs, "no PDF in the output", str(pdfs[:3]))
big = [p.relative_to(DIST).as_posix() for p in DIST.rglob("*") if p.is_file() and p.stat().st_size > 20 * 1024 * 1024]
check(not big, "no file over 20 MB (hosting limit is 25 MB)", str(big))

# ---------------------------------------------------------------- the generic covers
for c in site["courses"]:
    check((DIST / c["cover"]).exists(), f"{c['slug']} cover image")
home = html.get("index.html", "")
for c in site["courses"]:
    check(c["cover"] in home, f"{c['slug']} card uses the generic cover")
    check(not re.search(r"img/modules/" + c["slug"], home), f"{c['slug']}: no module thumbnail on the home page")

print(f"{len(passes)} checks passed, {len(fails)} failed, {len(warns)} warnings")
for f in fails:
    print("FAIL", f)
for w in warns:
    print("WARN", w)
sys.exit(1 if fails else 0)
