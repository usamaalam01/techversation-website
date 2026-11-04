"""Rebuilds assets/img (resized thumbnails) and assets/data.js of the mockup from the course files in D:\Certifications.
Run: python -X utf8 _tools\build_mock_data.py   (assets/logo.jpg is kept as it is)"""
import json, re, shutil, sys
from pathlib import Path
from PIL import Image

REPO = Path(r"D:\Certifications")
OC = REPO / "OnlineCourses"
OUT = Path(r"D:\Techversation\mockup")
IMG = OUT / "assets" / "img"
IMG.mkdir(parents=True, exist_ok=True)

COURSES = {
    "csm": dict(folder="CSM", institute="scrum-alliance", short="CSM", name="ScrumMaster",
                title="CSM Exam Prep Masterclass", accent="c-csm",
                desc="The Scrum Guide and the CSM learning objectives, from Scrum theory to situational questions.",
                notes=REPO / "CSM" / "markdown", noteglob="Topic_*.md"),
    "pmp": dict(folder="PMP", institute="pmi", short="PMP", name="Project Management Professional",
                title="PMP Exam Prep Masterclass", accent="c-pmp",
                desc="The three exam domains and the formulas, from predictive and agile delivery to ethics and AI.",
                notes=REPO / "PMP" / "markdown", noteglob="Topic_*.md"),
    "kcna": dict(folder="KCNA", institute="linux-foundation", short="KCNA", name="Kubernetes and Cloud Native Associate",
                 title="KCNA Exam Prep Masterclass", accent="c-kcna",
                 desc="Kubernetes, containers, security, delivery and observability, with the Harbor Books running case.",
                 notes=None),
    "aigp": dict(folder="AIGP", institute="iapp", short="AIGP", name="AI Governance Professional",
                 title="AIGP Exam Prep Masterclass", accent="c-aigp",
                 desc="AI governance from foundations and laws to design, release and monitoring of AI systems.",
                 notes=None),
    "cdmp": dict(folder="CDMP", institute="dama", short="CDMP", name="Data Management Professional",
                 title="CDMP Exam Prep Masterclass", accent="c-cdmp",
                 desc="The fourteen DMBOK knowledge areas: governance, architecture, modeling, quality and more.",
                 notes=REPO / "DAMA" / "CDMP-Associate" / "markdown", noteglob="Chapter_*.md"),
}


def read_lengths(course_folder):
    """module -> {part: (title, 'm:ss')} from VIDEOS.md, where it has the table."""
    p = OC / course_folder / "VIDEOS.md"
    out = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*[\d-]+\s*\|\s*(\d+:\d+)\s*\|", line)
        if m:
            out.setdefault(m.group(1).zfill(2), {})[int(m.group(2))] = (m.group(3), m.group(4))
    return out


def cdmp_file(num):
    d = OC / "CDMP" / "Youtube-thumbnails"
    n = lambda f: int(re.search(r"\((\d+)\)", f.name).group(1))
    first = sorted(d.glob("ChatGPT Image Jun 21, 2026, 01_02_*.png"), key=n)      # modules 00-09
    second = sorted(d.glob("ChatGPT Image Jun 21, 2026, 01_06_*.png"), key=n)     # modules 10-14
    return (first + second)[int(num)]


def thumb(course, key, dest):
    src = OC / course / "thumbnails" / "3d" / f"{key}.png"
    if course == "CDMP":
        src = cdmp_file(key[:2])
    if not src.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB").resize((480, 270), Image.LANCZOS)
    im.save(dest, "JPEG", quality=76, optimize=True)
    return True


def parse_scripts(path):
    """Slide scripts: [{n, title, secs, text}] with [PAUSE] markers removed."""
    t = path.read_text(encoding="utf-8")
    parts = re.split(r"^### Script — Slide (\d+): (.+)$", t, flags=re.M)
    out = []
    for i in range(1, len(parts), 3):
        n, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        m = re.search(r"\*\(~(\d+) seconds?\)\*", body)
        secs = int(m.group(1)) if m else 20
        body = re.sub(r"\*\(~[^)]*\)\*", "", body)
        body = re.sub(r"\[PAUSE[^\]]*\]", "", body)
        body = body.split("\n---")[0]
        text = " ".join(x.strip() for x in body.strip().split("\n\n"))
        out.append(dict(n=n, title=re.sub(r"\s*\*\*\[.*?\]\*\*", "", title), secs=secs, text=text))
    return out


data = dict(courses={}, institutes=[], notes={}, transcripts={}, glossary={})

for slug, c in COURSES.items():
    prog = json.loads((OC / c["folder"] / "upload_progress.json").read_text(encoding="utf-8"))
    if slug == "cdmp":
        vids = {k: dict(id=v) for k, v in prog["uploaded"].items()}
        playlist = prog["playlist_id"]
    else:
        vids = prog["videos"]
        playlist = prog["playlist_id"]
    lengths = read_lengths(c["folder"])
    mods = {}
    for key, v in vids.items():
        m = re.match(r"(\d\d)-(.+?)(?:-part-(\d+))?$", key)
        num, folder_rest, part = m.group(1), m.group(2), int(m.group(3) or 1)
        mods.setdefault(num, dict(num=num, folder=key.split("-part-")[0], parts=[]))
        pl = lengths.get(num, {}).get(part)
        mods[num]["parts"].append(dict(part=part, id=v["id"], len=pl[1] if pl else None, title=pl[0] if pl else None, key=key))
    for num, mod in sorted(mods.items()):
        sp = OC / c["folder"] / mod["folder"] / "scripts.md"
        title = mod["folder"][3:].replace("-", " ")
        if sp.exists():
            mm = re.match(r"# Module \d+: (.+?) — Speaker Scripts", sp.read_text(encoding="utf-8").splitlines()[0])
            if mm:
                title = mm.group(1)
        mod["title"] = title
        mod["parts"].sort(key=lambda x: x["part"])
        got = False
        for p in mod["parts"]:
            ok = thumb(c["folder"], p["key"], IMG / slug / f"{p['key']}.jpg")
            p["img"] = f"assets/img/{slug}/{p['key']}.jpg" if ok else None
            got = got or ok
        mod["img"] = mod["parts"][0]["img"]
        for p in mod["parts"]:
            p.pop("key")
    modlist = [mods[k] for k in sorted(mods)]
    total_videos = sum(len(m["parts"]) for m in modlist)
    secs = 0
    have_len = all(p["len"] for m in modlist for p in m["parts"])
    if have_len:
        for m in modlist:
            for p in m["parts"]:
                mm_, ss_ = p["len"].split(":")
                secs += int(mm_) * 60 + int(ss_)
    hero = None
    if slug == "cdmp":
        hp = OC / "CDMP" / "Youtube-thumbnails" / "ChatGPT Image Jun 21, 2026, 01_03_53 AM.png"
        (IMG / "cdmp").mkdir(parents=True, exist_ok=True)
        Image.open(hp).convert("RGB").resize((480, 270), Image.LANCZOS).save(IMG / "cdmp" / "hero.jpg", "JPEG", quality=76, optimize=True)
        hero = "assets/img/cdmp/hero.jpg"
    data["courses"][slug] = dict(hero=hero, slug=slug, institute=c["institute"], short=c["short"], name=c["name"], title=c["title"],
                                 accent=c["accent"], desc=c["desc"], playlist=playlist, modules=modlist,
                                 videos=total_videos, minutes=round(secs / 60) if have_len else None, status="live")

    # study notes
    if c["notes"]:
        topics = []
        for f in sorted(c["notes"].rglob(c["noteglob"])):
            txt = f.read_text(encoding="utf-8")
            first = txt.splitlines()[0].lstrip("# ").strip()
            first = re.sub(r"\s+[—-]\s+.*Exam Summary$", "", first)
            first = re.sub(r"^(Topic|Chapter) \d+:\s*", "", first)
            n = re.search(r"(?:Topic|Chapter)_(\d+)", f.name).group(1)
            group = f.parent.name if f.parent != c["notes"] else "Chapters"
            group = re.sub(r"^\d+_", "", group).replace("_", " ")
            los = []
            for lo in re.findall(r"\b(?:CSM|SF) \d+\.\d+", txt[:1500]):
                if lo not in los:
                    los.append(lo)
            words = len(re.findall(r"\w+", txt))
            topics.append(dict(num=n, title=first, group=group, mins=max(3, round(words / 220)), los=los))
        data["notes"][slug] = topics

# institutes
data["institutes"] = [
    dict(id="pmi", name="PMI", full="Project Management Institute", mono="PMI", certs=["pmp"]),
    dict(id="scrum-alliance", name="Scrum Alliance", full="Scrum Alliance", mono="SA", certs=["csm"]),
    dict(id="iapp", name="IAPP", full="International Association of Privacy Professionals", mono="IAPP", certs=["aigp"]),
    dict(id="linux-foundation", name="Linux Foundation", full="The Linux Foundation and CNCF", mono="LF", certs=["kcna"]),
    dict(id="dama", name="DAMA International", full="Data Management Association International", mono="DAMA", certs=["cdmp"]),
    dict(id="the-open-group", name="The Open Group", full="The Open Group", mono="TOG", certs=[], soon=["togaf"]),
]
data["soon"] = [
    dict(slug="togaf", institute="the-open-group", short="TOGAF", name="Enterprise Architecture", kind="Certification",
         desc="The ADM, the content framework and governance. Course modules are written; videos come next."),
    dict(slug="prompt", institute=None, short="Prompt Engineering", name="Training", kind="Training",
         desc="Zero-shot to agent prompting, structured output and how to evaluate prompts."),
    dict(slug="sdd", institute=None, short="Spec-Driven Development", name="Training", kind="Training",
         desc="Write specs first and build with an AI coding assistant, in four phases."),
    dict(slug="aigov", institute=None, short="AI Governance", name="Training", kind="Training",
         desc="Risk, regulation and a governance program for teams that build or buy AI."),
]

# facts (only where the course files carry a verified statement)
data["facts"] = dict(
    csm=dict(questions="50", time="60 min", pass_="37 correct (74%)", prereq="A 2-day course with a Scrum Alliance trainer",
             fee="See the official site", source="scrumalliance.org"),
    kcna=dict(questions="60", time="90 min", pass_="75%", prereq="None", fee="See the official site", source="training.linuxfoundation.org"),
)

# real transcript of CSM module 05 (both parts), with chapter timestamps scaled to the real part lengths
sc = parse_scripts(OC / "CSM" / "05-Scrum-Master" / "scripts.md")
csm05 = [m for m in data["courses"]["csm"]["modules"] if m["num"] == "05"][0]
splits = {1: range(1, 14), 2: range(14, 26)}
tr = {}
for part, rng in splits.items():
    slides = [s for s in sc if s["n"] in rng]
    total = sum(s["secs"] for s in slides) or 1
    real = [p for p in csm05["parts"] if p["part"] == part][0]["len"]
    rm, rs = real.split(":")
    realsecs = int(rm) * 60 + int(rs)
    t = 0.0
    items = []
    for s in slides:
        items.append(dict(at=round(t), title=s["title"], text=s["text"]))
        t += s["secs"] * realsecs / total
    tr[str(part)] = items
data["transcripts"]["csm-05"] = tr

# glossary sample (CSM): short definitions after the Scrum Guide, with the module that teaches the term
data["glossary"]["csm"] = [
    ("Scrum", "A lightweight framework that helps people, teams and organizations generate value through adaptive solutions for complex problems.", "01"),
    ("Empiricism", "Knowledge comes from experience and from making decisions based on what is observed: transparency, inspection and adaptation.", "01"),
    ("Sprint", "A fixed-length event of one month or less, in which all the work to create the Increment happens.", "06"),
    ("Product Goal", "A long-term objective for the Scrum Team, held in the Product Backlog. The team commits to it.", "10"),
    ("Sprint Goal", "The single objective for the Sprint. It is created in Sprint Planning and added to the Sprint Backlog.", "11"),
    ("Sprint Backlog", "The Sprint Goal, the Product Backlog items selected for the Sprint and the plan for delivering them.", "11"),
    ("Increment", "A concrete step toward the Product Goal. Each Increment is additive and usable.", "12"),
    ("Definition of Done", "A formal description of the state of the Increment when it meets the quality measures required for the product.", "12"),
    ("Developers", "The people in the Scrum Team who are committed to creating any aspect of a usable Increment each Sprint.", "03"),
    ("Product Owner", "Accountable for maximizing the value of the product resulting from the work of the Scrum Team.", "04"),
    ("Scrum Master", "Accountable for establishing Scrum and for the Scrum Team's effectiveness.", "05"),
    ("Daily Scrum", "A 15-minute event for the Developers to inspect progress toward the Sprint Goal and adapt the Sprint Backlog.", "08"),
]

(OUT / "assets" / "data.js").write_text("window.TV = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print({k: (v["videos"], len(v["modules"]), v["minutes"]) for k, v in data["courses"].items()})
print({k: len(v) for k, v in data["notes"].items()})
print(sum(1 for _ in IMG.rglob("*.jpg")), "images", sum(f.stat().st_size for f in IMG.rglob("*.jpg")) // 1024, "KB")
