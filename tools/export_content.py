"""export_content.py   builds the website content from the course folders in D:\\Certifications (the private repo).

Writes only website-ready material: JSON data, converted study notes, resized images and the slide decks. No source PDFs, no secrets.
  src/data/site.json                  institutes, courses, modules, parts (YouTube ids, lengths, chapters), facts
  src/data/transcripts/<course>/NN.json   narration scripts per module and part
  src/data/notes/<course>/NN.json     standardized study notes (CSM so far)
  src/data/glossary/<course>.json     key terms (CSM, KCNA)
  public/img/covers, public/img/modules, public/img/notes, public/downloads
Run: python -X utf8 tools/export_content.py     (after tools/fetch_youtube_meta.py)
"""
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notes_lib import build_notes, SCRUB_LOG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPO = Path(r"D:\Certifications")
OC = REPO / "OnlineCourses"
DATA = ROOT / "src" / "data"
PUB = ROOT / "public"
YT = json.loads((DATA / "youtube.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COURSES = {
    "csm": dict(folder="CSM", institute="scrum-alliance", short="CSM", name="ScrumMaster", title="CSM Exam Prep Masterclass", accent="c-csm",
                desc="The Scrum Guide and the CSM learning objectives, from Scrum theory to situational questions.",
                audience="Anyone preparing for the CSM exam: new Scrum Masters, Product Owners, Developers and managers who work with Scrum teams.",
                sources="The Scrum Guide (November 2020), the Agile Manifesto, the Scrum values and the official CSM learning objectives."),
    "pmp": dict(folder="PMP", institute="pmi", short="PMP", name="Project Management Professional", title="PMP Exam Prep Masterclass", accent="c-pmp",
                desc="The three exam domains and the formulas, from predictive and agile delivery to ethics and AI.",
                audience="Project managers preparing for the PMP exam under the current Exam Content Outline.",
                sources="The PMBOK Guide, 8th Edition and the current PMP Exam Content Outline."),
    "kcna": dict(folder="KCNA", institute="linux-foundation", short="KCNA", name="Kubernetes and Cloud Native Associate", title="KCNA Exam Prep Masterclass", accent="c-kcna",
                 desc="Kubernetes, containers, security, delivery and observability, with the Harbor Books running case.",
                 audience="Engineers, students and career changers preparing for the KCNA exam. No hands-on cluster is needed.",
                 sources="The official KCNA curriculum, the Kubernetes documentation and the CNCF landscape."),
    "aigp": dict(folder="AIGP", institute="iapp", short="AIGP", name="AI Governance Professional", title="AIGP Exam Prep Masterclass", accent="c-aigp",
                 desc="AI governance from foundations and laws to design, release and monitoring of AI systems.",
                 audience="Privacy, legal, risk and technology professionals preparing for the AIGP exam.",
                 sources="The AIGP Body of Knowledge, the laws and standards it names, and their public texts."),
    "cdmp": dict(folder="CDMP", institute="dama", short="CDMP", name="Data Management Professional", title="CDMP Exam Prep Masterclass", accent="c-cdmp",
                 desc="The fourteen DMBOK knowledge areas: governance, architecture, modeling, quality and more.",
                 audience="Data professionals preparing for the CDMP Associate exam.",
                 sources="DAMA-DMBOK, 2nd Edition, and the CDMP exam guidance."),
    "togaf": dict(folder="TOGAF", institute="the-open-group", short="TOGAF", name="TOGAF Enterprise Architecture", title="TOGAF 10 Associate Masterclass", accent="c-togaf",
                  desc="Enterprise architecture and the TOGAF Standard: the ADM, the content framework, governance and the exam.",
                  audience="Architects, analysts and managers preparing for the TOGAF Foundation (Level 1) exam.",
                  sources="The TOGAF Standard, 10th Edition (The Open Group) and the weekly study guides."),
    "clf": dict(folder="AWS-CLF", institute="aws", short="CLF-C02", name="AWS Cloud Practitioner", title="AWS Cloud Practitioner (CLF-C02) Exam Prep Masterclass", accent="c-clf",
                desc="Cloud concepts, security, core AWS services, pricing and support, with the Lantern and Loom running case.",
                audience="Beginners, students, sales and project staff, and career changers preparing for the AWS Cloud Practitioner exam. No hands-on experience is needed.",
                sources="The official AWS Cloud Practitioner (CLF-C02) exam guide and AWS's own documentation."),
    "aif": dict(folder="AWS-AIF", institute="aws", short="AIF-C01", name="AWS AI Practitioner", title="AWS AI Practitioner (AIF-C01) Exam Prep Masterclass", accent="c-aif",
                desc="AI, machine learning and generative AI on AWS: foundation models, prompt engineering, responsible AI and security.",
                audience="Anyone preparing for the AWS AI Practitioner exam, with or without a technical background.",
                sources="The official AWS AI Practitioner (AIF-C01) exam guide and AWS's own documentation."),
    "saa": dict(folder="AWS-SAA", institute="aws", short="SAA-C03", name="AWS Solutions Architect Associate", title="AWS Solutions Architect Associate (SAA-C03) Exam Prep Masterclass", accent="c-saa",
                desc="Secure, resilient, high-performing and cost-optimized architectures, with the Lantern and Loom running case.",
                audience="Engineers and architects preparing for the AWS Solutions Architect Associate exam.",
                sources="The official AWS Solutions Architect Associate (SAA-C03) exam guide and AWS's own documentation."),
    "aigov": dict(folder="AIGovernance", institute="training", kind="training", topic="AI", short="AI Governance", name="AI Governance Masterclass", title="AI Governance Masterclass", accent="c-aigov",
                  desc="From principles and risk to laws, frameworks and a working governance program, built around one running case.",
                  audience="Anyone who builds, buys or oversees AI: governance, risk, legal, product and engineering teams.",
                  sources="Public laws, standards and frameworks, such as the NIST AI Risk Management Framework and ISO/IEC 42001, and the course's own running case."),
}
INSTITUTES = [
    dict(id="pmi", name="PMI", full="Project Management Institute", mono="PMI", certs=["pmp"]),
    dict(id="scrum-alliance", name="Scrum Alliance", full="Scrum Alliance", mono="SA", certs=["csm"]),
    dict(id="iapp", name="IAPP", full="International Association of Privacy Professionals", mono="IAPP", certs=["aigp"]),
    dict(id="linux-foundation", name="Linux Foundation", full="The Linux Foundation and CNCF", mono="LF", certs=["kcna"]),
    dict(id="dama", name="DAMA International", full="Data Management Association International", mono="DAMA", certs=["cdmp"]),
    dict(id="the-open-group", name="The Open Group", full="The Open Group", mono="TOG", certs=["togaf"]),
    dict(id="aws", name="AWS", full="Amazon Web Services", mono="AWS", certs=["clf", "aif", "saa"]),
    dict(id="training", name="Training", full="Techversation training courses", mono="TV", certs=[], hidden=True),
]
SOON = []      # 'coming soon' cards (slug, institute, short, name, kind, desc); none at the moment
# exam facts: only where the course files carry a statement; the fee and the prerequisite are checked at the source before launch
FACTS = dict(
    csm=dict(questions="50", time="60 min", passing="37 correct (74%)", source="scrumalliance.org", url="https://www.scrumalliance.org/get-certified/scrum-master-track/certified-scrummaster"),
    clf=dict(questions="65", time="90 min", passing="700 of 1,000", source="aws.amazon.com/certification", url="https://aws.amazon.com/certification/"),
    aif=dict(questions="65", time="90 min", passing="700 of 1,000", source="aws.amazon.com/certification", url="https://aws.amazon.com/certification/"),
    saa=dict(questions="65", time="130 min", passing="720 of 1,000", source="aws.amazon.com/certification", url="https://aws.amazon.com/certification/"),
    kcna=dict(questions="60", time="90 min", passing="75%", source="training.linuxfoundation.org", url="https://training.linuxfoundation.org/certification/kubernetes-cloud-native-associate/"),
)


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", " and ")).strip("-")
    return s


def plain(s):
    s = re.sub(r"\*\*\[.*?\]\*\*", "", s)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------------------------------- modules and transcripts
def parse_slides(path):
    """({slide number: part}, [(part, title)], {slide number: title})"""
    part, parts, slide_part, titles = 1, [], {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"<!--\s*PART\s+(\d+)\s*:?\s*(.*?)\s*-->", line)
        if m:
            part = int(m.group(1))
            parts.append((part, m.group(2)))
            continue
        m = re.match(r"##\s+SLIDE\s+(\d+):\s*(.+)$", line)
        if m:
            slide_part[int(m.group(1))] = part
            titles[int(m.group(1))] = plain(m.group(2))
    if not parts:
        parts = [(1, "")]
    return slide_part, parts, titles


def parse_scripts(path):
    t = path.read_text(encoding="utf-8")
    first = t.splitlines()[0]
    m = re.match(r"#\s*Module\s+\d+:\s*(.+?)\s*[—-]+\s*Speaker Scripts", first)
    title = m.group(1) if m else None
    chunks = re.split(r"^###\s+Script\s*[—-]\s*Slide\s+(\d+):\s*(.+)$", t, flags=re.M)
    out = {}
    for i in range(1, len(chunks), 3):
        body = chunks[i + 2]
        body = re.sub(r"\*\(~[^)]*\)\*", "", body)
        body = re.sub(r"\[PAUSE[^\]]*\]", "", body)
        body = body.split("\n---")[0]
        text = " ".join(plain(x) for x in body.strip().split("\n\n") if x.strip())
        out[int(chunks[i])] = dict(title=plain(chunks[i + 1]), text=text)
    return title, out


def small_image(src, dest, size=(480, 270)):
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").resize(size, Image.LANCZOS).save(dest, "JPEG", quality=78, optimize=True)


def cdmp_thumb(num):
    d = OC / "CDMP" / "Youtube-thumbnails"
    n = lambda f: int(re.search(r"\((\d+)\)", f.name).group(1))
    fs = sorted(d.glob("ChatGPT Image Jun 21, 2026, 01_02_*.png"), key=n) + sorted(d.glob("ChatGPT Image Jun 21, 2026, 01_06_*.png"), key=n)
    return fs[int(num)]


def build_course(slug, c):
    folder = OC / c["folder"]
    prog = json.loads((folder / "upload_progress.json").read_text(encoding="utf-8"))
    vids = {k: v["id"] for k, v in prog["videos"].items()} if "videos" in prog else dict(prog["uploaded"])
    modules, warns = [], []
    for mdir in sorted(p for p in folder.iterdir() if p.is_dir() and re.match(r"\d\d-", p.name)):
        num = mdir.name[:2]
        if not (mdir / "scripts.md").exists() or not (mdir / "slides.md").exists():
            warns.append(f"{slug} {mdir.name}: no scripts.md or slides.md")
            continue
        title, scripts = parse_scripts(mdir / "scripts.md")
        slide_part, parts_meta, slide_titles = parse_slides(mdir / "slides.md")
        title = title or mdir.name[3:].replace("-", " ")
        mslug = f"{num}-{slugify(title)}"
        parts, transcripts = [], {}
        for pn, ptitle in parts_meta:
            key = f"{mdir.name}-part-{pn}"
            vid = vids.get(key) or (vids.get(mdir.name) if pn == 1 else None)
            if not vid:
                warns.append(f"{slug} {key}: no video id")
                continue
            ym = YT.get(vid, {})
            sections = [dict(title=scripts[n]["title"], text=scripts[n]["text"]) for n in sorted(scripts) if slide_part.get(n, 1) == pn and scripts[n]["text"]]
            chapters = ym.get("chapters") or []
            if chapters and len(chapters) == len(sections):                       # one chapter per slide: the transcript gets its time stamps
                for s, ch in zip(sections, chapters):
                    s["at"] = ch[0]
            thumb = None
            src = cdmp_thumb(num) if slug == "cdmp" else folder / "thumbnails" / "3d" / f"{key}.png"
            if slug in ("togaf", "aigov"):                                       # the images that are on the YouTube videos (fetched once into public/img/modules)
                if (PUB / f"img/modules/{slug}/{num}-{pn}.jpg").exists():
                    thumb = f"img/modules/{slug}/{num}-{pn}.jpg"
            elif src.exists():
                thumb = f"img/modules/{slug}/{num}-{pn}.jpg"
                small_image(src, PUB / thumb)
            parts.append(dict(part=pn, id=vid, title=ptitle or title, seconds=ym.get("seconds"), chapters=chapters, published=ym.get("published"), thumb=thumb))
            transcripts[str(pn)] = sections
        if not parts:
            continue
        deck = mdir / f"{mdir.name}.pptx"
        dl = None
        if deck.exists():
            dl = f"downloads/{slug}/{mslug}.pptx"
            (PUB / dl).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(deck, PUB / dl)
        out = DATA / "transcripts" / slug / f"{num}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(transcripts, ensure_ascii=False), encoding="utf-8")
        modules.append(dict(num=num, slug=mslug, title=title, desc=parts[0]["title"], parts=parts, deck=dl, deck_kb=round(deck.stat().st_size / 1024) if deck.exists() else None,
                            seconds=sum(p["seconds"] or 0 for p in parts), words=sum(len(s["text"].split()) for p in transcripts.values() for s in p)))
    cover = f"img/covers/{slug}.jpg"
    src = OC / "CDMP" / "Youtube-thumbnails" / "ChatGPT Image Jun 21, 2026, 01_03_53 AM.png" if slug == "cdmp" else folder / "thumbnails" / "covers" / f"{c['folder']}-cover.png"
    (PUB / cover).parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").resize((960, 540), Image.LANCZOS).save(PUB / cover, "JPEG", quality=82, optimize=True)
    course = dict(kind=c.get("kind", "certification"), topic=c.get("topic"), slug=slug, institute=c["institute"], short=c["short"], name=c["name"], title=c["title"], accent=c["accent"], desc=c["desc"], audience=c["audience"],
                  sources=c["sources"], playlist=prog["playlist_id"], cover=cover, modules=modules, facts=FACTS.get(slug),
                  videos=sum(len(m["parts"]) for m in modules), seconds=sum(m["seconds"] for m in modules))
    return course, warns


# ---------------------------------------------------------------------------------------------------- study notes
# The Specialist study plans were written for one candidate, so their personal parts are taken out before anything is published (the name, score, strengths and gaps,
# the weekly schedule with its personal tasks, the changelog). The rules that find those parts name the personal details themselves, so they live in
# tools/_private/plan_scrub.py, which is git-ignored and never published. Every removal is listed in tools/_private/scrub_report.md. Without that file the
# Specialist notes are skipped.
try:
    from _private.plan_scrub import PLAN_SCRUB as _PLAN_SCRUB
except ImportError:
    _PLAN_SCRUB = None
SPECIALIST = [
    dict(path=REPO / "DAMA" / "CDMP-Practitioner" / "data-governance" / "DG_Specialist_Study_Plan.md", num="15", title="Data Governance and Stewardship Specialist: Reference Notes",
         group="Specialist exam notes", label="Specialist", short="Spec", modules=["03"], header="bold", drop_header=True, scrub=_PLAN_SCRUB),
    dict(path=REPO / "DAMA" / "CDMP-Practitioner" / "master-data-management" / "MDM_Specialist_Study_Plan.md", num="16", title="Reference and Master Data Specialist: Reference Notes",
         group="Specialist exam notes", label="Specialist", short="Spec", modules=["10"], header="bold", drop_header=True, scrub=_PLAN_SCRUB),
]
if not _PLAN_SCRUB:
    print("tools/_private/plan_scrub.py not found: the Specialist notes are skipped")
    SPECIALIST = []
NOTES = {
    "csm": dict(root=REPO / "CSM" / "markdown", glob="Topic_*.md", qa=True),
    "pmp": dict(root=REPO / "PMP" / "markdown", glob="Topic_*.md", qa=True, plan=OC / "PMP" / "COURSE_PLAN.md"),
    "cdmp": dict(root=REPO / "DAMA" / "CDMP-Associate" / "markdown", glob="Chapter_*.md", qa=False, kind="Chapter", extras=SPECIALIST),
    # KCNA: generated from the verified course slides by OnlineCourses\KCNA\make_study_notes.py (one note per module); the group is the exam domain of the module
    "kcna": dict(root=OC / "KCNA" / "study-notes", glob="Module_*.md", qa=True, kind="Module", link_word="Module", group_from="Curriculum",
                 group_default={"00": "Start here", "15": "Review and exam day", "16": "Review and exam day"}),
    # AIGP: generated from the verified course slides by OnlineCourses\AIGP\make_study_notes.py (one note per module); the group is the domain of the Body of Knowledge
    "aigp": dict(root=OC / "AIGP" / "study-notes", glob="Module_*.md", qa=True, kind="Module", link_word="Module", group_from="Domain",
                 group_default={"00": "Start here", "14": "Review and exam day", "15": "Review and exam day"}),
    "togaf": dict(root=REPO / "TOGAF", glob="week*/Week_*.md", qa=False, header="bold", kind="Week",
                  scrub=dict(drop_lines=[r"\d+\. \*\*Apply to your experience\.\*\*"]),      # one prompt in Week 1 is about the author's own work history
                  append={"01": (REPO / "TOGAF" / "week1" / "Quick_Reference_Week_1.md", "Quick Reference Card for Week 1")},
                  groups=[("Learn the framework (Weeks 1 to 4)", {"01", "02", "03", "04"}), ("Apply it (Weeks 5 and 6)", {"05", "06"}), ("Practice and exam day (Weeks 7 and 8)", {"07", "08"})],
                  # which video modules each weekly guide goes with: an editorial choice for navigation, by topic
                  modules_of={"01": (["01", "02"], ""), "02": (["03", "04", "05"], ""), "03": (["06", "05", "12", "09"], ""), "04": (["08", "13", "10", "09"], ""),
                              "05": (["04"], ""), "06": (["07", "11", "14"], ""), "07": (["14"], ""), "08": (["14"], "")}),
}


# ---------------------------------------------------------------------------------------------------- glossaries
CSM_TERMS = [   # (term, module, the Scrum Guide's own sentence); every sentence is checked against the Guide text
    ("Scrum", "01", "Scrum is a lightweight framework that helps people, teams and organizations generate value through adaptive solutions for complex problems."),
    ("Empiricism", "01", "Empiricism asserts that knowledge comes from experience and making decisions based on what is observed."),
    ("Scrum Team", "03", "The Scrum Team consists of one Scrum Master, one Product Owner, and Developers."),
    ("Product Owner", "04", "The Product Owner is accountable for maximizing the value of the product resulting from the work of the Scrum Team."),
    ("Scrum Master", "05", "The Scrum Master is accountable for establishing Scrum as defined in the Scrum Guide."),
    ("Sprint", "06", "Sprints are the heartbeat of Scrum, where ideas are turned into value."),
    ("Sprint Planning", "07", "Sprint Planning initiates the Sprint by laying out the work to be performed for the Sprint."),
    ("Daily Scrum", "08", "The purpose of the Daily Scrum is to inspect progress toward the Sprint Goal and adapt the Sprint Backlog as necessary, adjusting the upcoming planned work."),
    ("Sprint Review", "09", "The purpose of the Sprint Review is to inspect the outcome of the Sprint and determine future adaptations."),
    ("Sprint Retrospective", "09", "The purpose of the Sprint Retrospective is to plan ways to increase quality and effectiveness."),
    ("Product Backlog", "10", "The Product Backlog is an emergent, ordered list of what is needed to improve the product."),
    ("Product Goal", "10", "The Product Goal describes a future state of the product which can serve as a target for the Scrum Team to plan against."),
    ("Sprint Backlog", "11", "The Sprint Backlog is composed of the Sprint Goal (why), the set of Product Backlog items selected for the Sprint (what), as well as an actionable plan for delivering the Increment (how)."),
    ("Sprint Goal", "11", "The Sprint Goal is the single objective for the Sprint."),
    ("Increment", "12", "An Increment is a concrete stepping stone toward the Product Goal."),
    ("Definition of Done", "12", "The Definition of Done is a formal description of the state of the Increment when it meets the quality measures required for the product."),
]


def build_glossary(slug, mods):
    if slug == "csm":
        guide = re.sub(r"\s+", " ", (ROOT / "tools" / "_guide2020.txt").read_text(encoding="utf-8")).replace("’", "'").replace("“", '"').replace("”", '"')
        out = []
        for term, mod, sent in CSM_TERMS:
            if sent.replace("’", "'") not in guide:
                raise SystemExit(f"glossary sentence not in the Scrum Guide: {term}")
            out.append(dict(term=term, text=sent, module=mod, group="From the Scrum Guide"))
        return sorted(out, key=lambda x: x["term"].lower()), "Definitions are the Scrum Guide's own sentences. The Scrum Guide, by Ken Schwaber and Jeff Sutherland, is licensed under CC BY-SA 4.0."
    if slug == "kcna":
        t = (OC / "KCNA" / "15-Quick-Reference-Recap" / "glossary.md").read_text(encoding="utf-8")
        out, group = [], ""
        for ln in t.splitlines():
            if ln.startswith("## "):
                group = ln[3:].strip()
            m = re.match(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+(?:\s+and\s+\d+)*)\s*\|\s*$", ln)     # "2 and 6": the first module is the link
            if m and m.group(1) != "Term":
                out.append(dict(term=plain(m.group(1)), text=plain(m.group(2)), module=re.match(r"\d+", m.group(3)).group(0).zfill(2), group=group))
        return out, ""
    return None, ""


def main():
    site = dict(institutes=INSTITUTES, soon=SOON, courses=[])
    allwarn = []
    for slug, c in COURSES.items():
        course, warns = build_course(slug, c)
        allwarn += warns
        notes = build_notes(NOTES[slug], slug, c["institute"], course["modules"], DATA, PUB) if slug in NOTES else None
        course["notes"] = notes
        g, note = build_glossary(slug, course["modules"])
        if g:
            (DATA / "glossary").mkdir(parents=True, exist_ok=True)
            (DATA / "glossary" / f"{slug}.json").write_text(json.dumps(dict(terms=g, note=note), ensure_ascii=False), encoding="utf-8")
        course["glossary"] = len(g) if g else 0
        site["courses"].append(course)
        print(f"{slug}: {len(course['modules'])} modules, {course['videos']} videos, {course['seconds'] // 60} min, notes {len(notes) if notes else 0}, glossary {course['glossary']}")
    (DATA / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=1), encoding="utf-8")
    priv = ROOT / "tools" / "_private"
    priv.mkdir(exist_ok=True)
    rep = ["# What was taken out of the personal study plans", "", "Private: this file is not published and is git-ignored.", ""]
    for slug_, num_, title_, lines_ in SCRUB_LOG:
        rep += [f"## {slug_} {num_}: {title_}", "", f"{len(lines_)} lines or phrases removed.", ""] + ["    " + x[:300] for x in lines_ if x.strip()] + [""]
    (priv / "scrub_report.md").write_text("\n".join(rep), encoding="utf-8")
    for w in allwarn:
        print("WARN", w)


if __name__ == "__main__":
    main()
