"""notes_lib.py   converts the study summaries (Markdown) of CSM, PMP and CDMP into website notes.

Standardization (what every note gets): a title, an at-a-glance block, the original header lines kept under "Scope and sources", numbered
sections with a table of contents, callouts for "Exam angle" / "Exam tip" / "Old wording" / terminology warnings, "Beyond ..." tags,
diagrams in figures, cross-references from "Topic N" to the note, exam questions with the answer on demand, and the quick-reference card.
The wording of the summaries is not changed.
"""
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt

MD = MarkdownIt("commonmark", {"html": False}).enable("table")
inline = MD.renderInline


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", " and ")).strip("-")


def plain(s):
    s = re.sub(r"\*\*\[.*?\]\*\*", "", s)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------------------------------- tags and callouts
def tag_html(text):
    """'Beyond PMBOK 8 — exam practice' -> a badge and, where there is one, the qualifier next to it"""
    text = text.strip()
    m = re.match(r"(Beyond PMBOK 8|Beyond the Scrum Guide|Beyond the curriculum|Beyond the BoK|Beyond the guide|Old wording|Old name|Moving|Archived topic|Verify live|Dates)(.*)$", text)
    if not m:
        return f'<span class="tag tag-beyond">{text}</span>'
    base, rest = m.group(1), re.sub(r"^[\s—:;,.-]+", "", m.group(2)).strip()
    label = {"Beyond the Scrum Guide": "Beyond the Guide", "Beyond the guide": "Beyond the guide"}.get(base, base)
    cls = "tag-old" if base in ("Old wording", "Old name", "Moving", "Archived topic", "Verify live", "Dates") else "tag-beyond"
    q = f'<span class="tag-q">{rest}</span>' if rest else ""
    return f'<span class="tag {cls}" title="{text}">{label}</span>{q}'


def tag_label(text):
    base = re.match(r"(Beyond PMBOK 8|Beyond the Scrum Guide|Beyond the curriculum|Beyond the BoK|Beyond the guide|Old wording|Old name|Moving|Archived topic|Verify live|Dates)", text.strip())
    return {"Beyond the Scrum Guide": "Beyond the Guide", "Beyond the guide": "Beyond the guide"}.get(base.group(1), base.group(1)) if base else text.strip()


def callouts(html):
    def drop(inner, pattern):
        return re.sub(r"^(\s*<p>)\s*(?:<strong>)?" + pattern + r"(?:</strong>)?:?(?:</strong>)?\s*", r"\1", inner, count=1, flags=re.I)

    def rep(m):
        inner = m.group(1)
        head = re.sub(r"<[^>]+>", "", inner[:240])
        if re.match(r"\s*Exam angle", head):
            return '<div class="callout exam"><span class="lbl">Exam angle</span><div>' + drop(inner, "Exam angle") + "</div></div>"
        if re.match(r"\s*Exam tip", head, flags=re.I):
            return '<div class="callout exam"><span class="lbl">Exam tip</span><div>' + drop(inner, "Exam Tip") + "</div></div>"
        if re.match(r"\s*Watch the PMBOK", head):
            return '<div class="callout old"><span class="lbl">Terminology</span><div>' + inner + "</div></div>"
        if re.match(r"\s*\[Old wording\]", head):
            body = re.sub(r"<strong>\[Old wording\]</strong>\s*", "", inner, count=1)
            return '<div class="callout old"><span class="lbl">Old wording</span><div>' + body + "</div></div>"
        bm = re.match(r"\s*\[(Beyond[^\]]*)\]", head)
        if bm:
            body = re.sub(r"<strong>\[Beyond[^\]]*\]</strong>\s*", "", inner, count=1)
            return '<div class="callout beyond"><span class="lbl">' + tag_label(bm.group(1)) + "</span><div>" + body + "</div></div>"
        if re.match(r"\s*Case:", head):
            return '<div class="callout beyond"><span class="lbl">Running case</span><div>' + drop(inner, "Case") + "</div></div>"
        if re.match(r"\s*Note\b", head):
            return '<div class="callout"><span class="lbl">Note</span><div>' + drop(inner, "Note") + "</div></div>"
        return '<blockquote class="plain">' + inner + "</blockquote>"
    return re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", rep, html, flags=re.S)


# ---------------------------------------------------------------------------------------------------- questions with the answer on demand
def convert_qa(text):
    out, n_s, n_r = [], 0, 0
    for b in re.split(r"\n\s*\n", text.strip()):
        b = b.strip()
        if b.startswith("### "):
            out.append(f"<h3>{inline(b[4:])}</h3>")
            continue
        m = re.match(r"\*\*(S\d+)\.\*\*\s*(.+?)\n(A\. .+?)\n\*\*Answer:\s*([A-E](?:,\s*[A-E])*)\.\*\*\s*(.+)$", b, flags=re.S)
        if m:
            qid, q, opts, right, expl = m.groups()
            keys = set(re.findall(r"[A-E]", right))                      # one letter, or several for a select-two or select-three question
            lis = []
            for line in opts.splitlines():
                om = re.match(r"([A-E])\.\s+(.+)$", line.strip())
                lis.append(f'<li class="{"right" if om.group(1) in keys else ""}"><b>{om.group(1)}</b><span>{inline(om.group(2))}</span></li>')
            out.append(f'<div class="qa"><p class="q"><span class="qn">{qid}</span>{inline(q)}</p><ul class="opts">{"".join(lis)}</ul>'
                       f'<details><summary>Show the answer</summary><p><strong>Answer: {right}.</strong> {inline(expl)}</p></details></div>')
            n_s += 1
            continue
        m = re.match(r"\*\*(R\d+)\.\s*(.+?)\*\*\s*\nA:\s*(.+)$", b, flags=re.S)
        if m:
            rid, q, a = m.groups()
            out.append(f'<div class="qa recall"><p class="q"><span class="qn">{rid}</span>{inline(q)}</p><details><summary>Show the answer</summary><p>{inline(a)}</p></details></div>')
            n_r += 1
            continue
        if b == "---":
            continue
        out.append(MD.render(b))
    return "\n".join(out), n_s, n_r


# ---------------------------------------------------------------------------------------------------- cross-references
def link_topics(html, urls, current, word="Topic"):
    """'Topic 18' and 'Topics 4 and 5' in the text become links to those notes (not inside links, headings' ids or tags)"""
    def num_link(num):
        n = num.zfill(2)
        return f'<a class="xref" href="{urls[n]}">{num}</a>' if n in urls and n != current else num

    def text_sub(s):
        def one(m):
            return m.group(1) + (f'<a class="xref" href="{urls[m.group(2).zfill(2)]}">Topic {m.group(2)}</a>' if m.group(2).zfill(2) in urls and m.group(2).zfill(2) != current else f"Topic {m.group(2)}")
        s = re.sub(r"(\b)Topic (\d{1,2})\b", one, s)
        def many(m):
            nums = re.sub(r"\d{1,2}", lambda x: num_link(x.group(0)), m.group(2))
            return m.group(1) + nums
        s = re.sub(r"(\bTopics )((?:\d{1,2}(?:, and |, | and | or )?)+)", many, s)
        if word != "Topic":                                          # the notes of KCNA follow the course modules: "Module 3", "module 3"
            def mod(m):
                k = m.group(2).zfill(2)
                return m.group(1) + (f'<a class="xref" href="{urls[k]}">{m.group(2)}</a>' if k in urls and k != current else m.group(2))
            s = re.sub(r"(\b[Mm]odule )(\d{1,2})\b", mod, s)
        return s
    parts = re.split(r"(<[^>]+>)", html)
    out, depth_a, skip = [], 0, 0
    for p in parts:
        if p.startswith("<"):
            if re.match(r"<a\b", p): depth_a += 1
            elif p.startswith("</a"): depth_a = max(0, depth_a - 1)
            out.append(p)
        else:
            out.append(p if depth_a else text_sub(p))
    return "".join(out)


# ---------------------------------------------------------------------------------------------------- one note
def read_header(lines):
    """the quoted lines under the title: [(key, markdown)], and the index of the first section"""
    items, i, cur = [], 1, None
    while i < len(lines) and not lines[i].startswith("## "):
        ln = lines[i]
        m = re.match(r">\s*\*\*([^*]+?):\*\*\s*(.*)$", ln)
        if m:
            cur = [m.group(1).strip(), m.group(2).strip()]
            items.append(cur)
        elif ln.startswith(">") and cur and ln.strip(">").strip():
            cur[1] += " " + ln.strip(">").strip()
        i += 1
    return items, i


def read_header_bold(lines):
    """TOGAF guides: '**Duration:** ...' lines under the title"""
    items, i = [], 1
    while i < len(lines) and not lines[i].startswith("## "):
        m = re.match(r"\*\*([^*]+?):\*\*\s*(.*?)\s*$", lines[i])
        if m and m.group(2):
            items.append([m.group(1).strip(), m.group(2).strip()])
        i += 1
    return items, i


def title_of(path):
    first = path.read_text(encoding="utf-8").splitlines()[0]
    m = re.match(r"#\s*(Topic|Chapter|Week|Module)\s+(\d+):\s*(.+?)(?:\s+[—-]\s+(?:CSM|PMP|CDMP|KCNA|AIGP|CLF|AIF|SAA) Exam Summary)?\s*$", first)
    if m:
        return m.group(2).zfill(2), m.group(3)
    m = re.match(r"#\s*DMBOK2 Chapter\s+(\d+)\s*[—–-]\s*(.+?)\s*$", first)             # CDMP chapters 1 and 2 use this title line
    return m.group(1).zfill(2), m.group(2)


SCRUB_LOG = []          # what was taken out of personal study plans; written to a private report, never to the site


def apply_scrub(raw, rules):
    """remove the personal parts of a study plan: whole sections or subsections, single lines, and personal phrases inside lines"""
    out, removed, skip2, skip3 = [], [], False, False
    for ln in raw.split("\n"):
        if ln.startswith("## "):
            skip2, skip3 = bool(re.match(rules.get("drop_sections", r"(?!)"), ln[3:])), False
        elif ln.startswith("### "):
            skip3 = bool(re.match(rules.get("drop_subsections", r"(?!)"), ln[4:]))
        if skip2 or skip3 or any(re.match(p, ln) for p in rules.get("drop_lines", [])):
            removed.append(ln)
            continue
        for pat, rep in rules.get("replace", []):
            new = re.sub(pat, rep, ln)
            if new != ln:
                removed.append("[phrase] " + ln)
                ln = new
        out.append(ln)
    return "\n".join(out), removed


def convert_note(cfg, slug, path, group, urls, pub, entry=None):
    raw = path.read_text(encoding="utf-8")
    removed = []
    if entry:
        raw, removed = apply_scrub(raw, entry.get("scrub", {}))
    elif cfg.get("scrub"):
        raw, removed = apply_scrub(raw, cfg["scrub"])
    lines = raw.splitlines()
    num, title = (entry["num"], entry["title"]) if entry else title_of(path)
    header, start = (read_header_bold if (cfg.get("header") == "bold" or (entry and entry.get("header") == "bold")) else read_header)(lines)
    if entry and entry.get("drop_header"):
        header = []
    if removed:
        SCRUB_LOG.append((slug, num, title, removed))
    body_lines = lines[start:]
    extra = cfg.get("append", {}).get(num)
    if extra:                                    # a companion card goes at the end of the note, its title becomes a section
        ex = extra[0].read_text(encoding="utf-8").splitlines()
        body_lines += ["", "---", "", "## " + extra[1]] + [("### " + ln[3:]) if ln.startswith("## ") else ln for ln in ex[1:]]
    body_text = re.sub(r"^(\s*(?:[-*+]|\d+\.)\s+)#(?= )", r"\1\\#", "\n".join(body_lines), flags=re.M)      # "- # of policies" means "number of", not a heading
    sections = re.split(r"^(?=## )", body_text, flags=re.M)
    used_ids = set()
    html, toc = [], []
    counts = dict(tables=0, images=0, scenario=0, recall=0, sections=0)
    body_md = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        hm = re.match(r"##\s+(\d+)\.\s+(.+)", sec)
        n, stitle = (hm.group(1), hm.group(2)) if hm else ("", sec.splitlines()[0][3:])
        content = sec.split("\n", 1)[1] if "\n" in sec else ""
        content = re.sub(r"\n-{3,}\s*$", "", content.strip())
        body_md.append(stitle + "\n" + content)
        tag = ""
        tm = re.search(r"\s*\*\*\[(.+?)\]\*\*\s*$", stitle)
        if tm:
            tag, stitle = tm.group(1), stitle[:tm.start()]
        sid = f"s{n}" if n else "s-" + slugify(plain(stitle))[:48]
        while sid in used_ids:
            sid += "x"
        used_ids.add(sid)
        toc.append(dict(id=sid, title=plain(stitle), n=n))
        counts["sections"] += 1
        if cfg["qa"] and re.search(r"Exam Q&A", stitle):
            inner, ns, nr = convert_qa(content)
            counts["scenario"] += ns
            counts["recall"] += nr
        else:
            inner = MD.render(content)
        tagh = tag_html(tag) if tag else ""
        numh = '<span class="num">' + n + "</span>" if n else ""
        html.append(f'<section class="note-sec" id="{sid}"><h2>{numh}{inline(stitle)}{tagh}</h2>{inner}</section>')
    out = "\n".join(html)
    out = callouts(out)
    out = re.sub(r"<strong>\[((?:Beyond|Old wording|Old name|Moving|Archived topic)[^\]]*)\]</strong>", lambda m: tag_html(m.group(1)), out)
    counts["tables"] = out.count("<table>")
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    out = re.sub(r"<hr\s*/?>", "", out)

    def fig(m):
        alt, src, cap = m.group(2), m.group(1), (m.group(3) or m.group(2))
        fn = Path(src).name
        s = path.parent.parent / "diagrams" / fn
        if not s.exists():
            s = path.parent / "diagrams" / fn
        if not s.exists():
            s = path.parent.parent / "assets" / fn
        if s.exists():
            (pub / "img" / "notes" / slug).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s, pub / "img" / "notes" / slug / fn)
        else:
            print("MISSING DIAGRAM", slug, num, fn)
        counts["images"] += 1
        return f'<figure class="fig"><img src="%BASE%img/notes/{slug}/{fn}" alt="{alt}" loading="lazy"><figcaption>{cap}</figcaption></figure>'
    out = re.sub(r'<img src="([^"]+)" alt="([^"]*)"(?: title="([^"]*)")?\s*/?>', fig, out)
    out = link_topics(out, urls, num, cfg.get("link_word", "Topic"))
    # review checklists: "- [ ] item" becomes a tick box
    out = re.sub(r"<li>\[( |x)\]\s*", lambda m: '<li class="task"><input type="checkbox" data-task' + (" checked" if m.group(1) == "x" else "") + ' aria-label="Mark as done"> ', out)
    # links between the weekly guides point to the notes
    def wk(m):
        k = re.search(r"Week_(\d)", m.group(1))
        return 'href="' + urls[k.group(1).zfill(2)] + '"' if k and k.group(1).zfill(2) in urls else m.group(0)
    out = re.sub(r'href="([^"]*Week_\d[^"]*\.md)(?:#[^"]*)?"', wk, out)
    out = re.sub(r'href="[^"]*Quick_Reference_Week_1\.md"', lambda m: 'href="' + urls.get("01", "#") + '"', out)
    head_html = [dict(key=k, html=link_topics(inline(v), urls, num, cfg.get("link_word", "Topic"))) for k, v in header if k not in ("Key",)]
    meta = dict((k, plain(v)) for k, v in header)
    los = []
    for lo in re.findall(r"\b(?:CSM|SF) \d+\.\d+", meta.get("LO", "")):
        if lo not in los:
            los.append(lo)
    words = len(re.findall(r"\w+", raw))
    # completeness: the words of the source against the words of the page (the page adds only labels)
    src_words = len(re.findall(r"[A-Za-z0-9]+", re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", "\n".join(body_md))))
    page_words = len(re.findall(r"[A-Za-z0-9]+", re.sub(r"<[^>]+>", " ", re.sub(r'<img [^>]*alt="([^"]*)"[^>]*>', r" \1 ", re.sub(r"<figcaption>.*?</figcaption>", "", out))).replace("&quot;", '"').replace("&amp;", "&")))      # the alt text of a figure counts as page text
    src_tables = sum(1 for tok in MD.parse("\n".join(body_md)) if tok.type == "table_open")      # counted by the parser, which also finds tables without a leading pipe
    src_images = len(re.findall(r"!\[[^\]]*\]\([^)]*\)", "\n".join(body_md)))
    return dict(num=num, slug=f"{num}-{slugify(title)}", title=title, group=group, tasks=out.count("data-task"), los=los, lo_text=meta.get("LO", ""), guide=meta.get("Scrum Guide", ""),
                sequence=meta.get("Sequence", ""), header=head_html, minutes=max(3, round(words / 220)), toc=toc, html=out,
                check=dict(src_words=src_words, page_words=page_words, src_tables=src_tables, tables=counts["tables"], src_images=src_images, images=counts["images"],
                           src_scenario=len(re.findall(r"^\*\*S\d+\.\*\*", "\n".join(body_md), flags=re.M)), scenario=counts["scenario"],
                           src_recall=len(re.findall(r"^\*\*R\d+\.", "\n".join(body_md), flags=re.M)), recall=counts["recall"], src_sections=len([s for s in sections if s.strip()]), sections=counts["sections"]))


def module_plan(plan_path):
    """PMP: the course plan lists which summary topics each video module covers, and the exam domain of the module"""
    out = {}
    for ln in plan_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d\d)\s*\|[^|]*\|\s*([\d, ]+?)\s*\|\s*([^|]*?)\s*\|", ln)
        if m and re.fullmatch(r"[\d, ]+", m.group(2)):
            for t in re.findall(r"\d+", m.group(2)):
                out[t.zfill(2)] = (m.group(1), re.sub(r"\*+", "", m.group(3)).strip())
    return out


def build_notes(cfg, slug, institute, modules, data_dir, pub):
    base = cfg["root"]
    files = sorted(base.rglob(cfg["glob"]))
    extras = cfg.get("extras", [])
    urls = {}
    for f in files:
        n, t = title_of(f)
        urls[n] = f"%BASE%{institute}/{slug}/notes/{n}-{slugify(t)}/"
    for ex in extras:
        urls[ex["num"]] = f"%BASE%{institute}/{slug}/notes/{ex['num']}-{slugify(ex['title'])}/"
    plan = module_plan(cfg["plan"]) if cfg.get("plan") else {}
    d = data_dir / "notes" / slug
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    metas, kind = [], cfg.get("kind", "Topic")
    short = {"Topic": "Topic", "Chapter": "Ch", "Week": "Week"}.get(kind, kind)

    def finish(n, modnums, domain, ref, tn, of):
        mods = [m for x in modnums for m in modules if m["num"] == x]      # the order of the list: the first is the main lecture
        mod = mods[0] if mods else None
        n["modules"] = [m["num"] for m in mods]
        n["module"] = dict(num=mod["num"], slug=mod["slug"], title=mod["title"]) if mod else None
        n["domain"] = domain
        n["ref"], n["tn"], n["of"] = ref, tn, of
        n["position"] = f"{ref} of {of}"
        n["kind"] = kind
        (d / f"{n['num']}.json").write_text(__import__("json").dumps(n, ensure_ascii=False), encoding="utf-8")
        metas.append({k: v for k, v in n.items() if k in ("num", "slug", "title", "group", "los", "minutes", "domain", "check", "modules", "tasks", "ref", "tn", "of")} | dict(module=n["module"]["num"] if n["module"] else None))

    for f in files:
        group = re.sub(r"^\d+_", "", f.parent.name).replace("_", " ") if f.parent != base else "Chapters"
        nn = title_of(f)[0]
        if cfg.get("groups"):
            group = next((g for g, nums in cfg["groups"] if nn in nums), group)
        n = convert_note(cfg, slug, f, group, urls, pub)
        if cfg.get("group_from"):
            item = next((h for h in n["header"] if h["key"] == cfg["group_from"]), None)
            n["group"] = (cfg.get("group_default", {}).get(n["num"], group) if cfg.get("group_full") and not re.sub(r"<[^>]+>", "", item["html"]).startswith("Domain") else re.sub(r"\s*\(.*?\)\s*$", "", re.sub(r"<[^>]+>", "", item["html"])).strip() if cfg.get("group_full") else re.sub(r"<[^>]+>", "", item["html"]).split(":")[0].strip()) if item else cfg.get("group_default", {}).get(n["num"], group)
        if cfg.get("modules_of"):
            modnums, domain = cfg["modules_of"].get(n["num"], ([], ""))
        else:
            one, domain = plan.get(n["num"], (n["num"] if not plan else None, ""))
            modnums = [one] if one else []
        finish(n, modnums, domain, f"{kind} {int(n['num'])}", f"{short} {n['num']}", len(files))
    for k, ex in enumerate(extras, 1):          # single files with their own title, group and lecture
        n = convert_note(cfg, slug, ex["path"], ex["group"], urls, pub, entry=ex)
        finish(n, ex["modules"], "", f"{ex['label']} {k}", f"{ex['short']} {k}", len(extras))
    return metas
