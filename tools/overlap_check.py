"""overlap_check.py   how much of the PMP and CDMP summaries is word-for-word the source book?

Measures, per note, the share of 8-word sequences that also occur in the book's text, and the longest passage (in words) that is identical.
The books stay in the private repo; the report (tools/overlap_report.md) names only numbers and note titles.
Limits: the text comes from the PDF extraction (hyphenation and ligatures can hide a match), so the numbers are a floor, not a ceiling.
Run: python -X utf8 tools/overlap_check.py
"""
import re
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Certifications")
ROOT = Path(__file__).resolve().parent.parent
N = 8
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES = {
    "PMP": dict(pdfs=[REPO / "PMP" / "pmbokguide_eighthed_eng.pdf"], notes=(REPO / "PMP" / "markdown", "Topic_*.md"), book="PMBOK Guide, 8th Edition"),
    "CDMP": dict(pdfs=[REPO / "DAMA" / "DAMA DMBOK 2nd Edition.pdf"], notes=(REPO / "DAMA" / "CDMP-Associate" / "markdown", "Chapter_*.md"), book="DAMA-DMBOK, 2nd Edition",
                 extra=[REPO / "DAMA" / "CDMP-Practitioner" / "data-governance" / "DG_Specialist_Study_Plan.md", REPO / "DAMA" / "CDMP-Practitioner" / "master-data-management" / "MDM_Specialist_Study_Plan.md"]),
    # AIGP: the IAPP documents and the IIA paper are copyrighted; the laws (EU AI Act, GDPR) and the US and EU public texts (NIST, EDPB) are not checked here
    "AIGP": dict(pdfs=[REPO / "OnlineCourses" / "AIGP" / "_source" / "AIGP_BoK_v2.1.pdf", REPO / "OnlineCourses" / "AIGP" / "AIGP_Cert_BOK_13March2026_FINAL.pdf", REPO / "OnlineCourses" / "AIGP" / "AIGP FSG.pdf",
                      REPO / "OnlineCourses" / "AIGP" / "_source" / "IAPP_Certification_Handbook_3Dec25.pdf", REPO / "OnlineCourses" / "AIGP" / "_source" / "primary" / "IIA_three_lines.pdf"],
                 notes=(REPO / "OnlineCourses" / "AIGP" / "study-notes", "Module_*.md"), book="IAPP AIGP Body of Knowledge v2.1, Study Guide and Candidate Handbook, and the IIA Three Lines Model"),
    "TOGAF": dict(pdfs=sorted((REPO / "TOGAF" / "extracted").glob("C220-Part*.txt")), notes=(REPO / "TOGAF", "week*/Week_*.md"), book="The TOGAF Standard, 10th Edition, Parts 0 to 5 (the guides were written around TOGAF 9, so part of their wording follows the older edition)"),
}


def pdf_text(path):
    if str(path).endswith(".txt"):
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    try:
        import fitz  # PyMuPDF
        return "\n".join(p.get_text() for p in fitz.open(str(path)))
    except ImportError:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)


def words(s):
    s = s.lower().replace("\u00ad", "").replace("-\n", "")
    return re.findall(r"[a-z0-9]+", s)


def note_words(md):
    body = md.split("\n## ", 1)[-1] if "\n## " in md else md
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    body = re.sub(r"\*\*\[[^\]]*\]\*\*", " ", body)
    return words(body)


def main():
    out = ["# Overlap of the summaries with their source books", "",
           f"Method: share of {N}-word sequences of each note that also occur in the book text, and the longest identical passage. Text comes from PDF extraction, so the numbers are a floor. Flag: overlap of 15% or more, or a passage of 40 words or more.", ""]
    only = [a.upper() for a in sys.argv[1:]]
    for course, cfg in SOURCES.items():
        if only and course not in only:
            continue
        t0 = time.time()
        src = []
        for p in cfg["pdfs"]:
            src += words(pdf_text(p))
        grams = {}
        for i in range(len(src) - N + 1):
            grams.setdefault(" ".join(src[i:i + N]), i)
        print(course, len(src), "source words,", len(grams), "sequences,", round(time.time() - t0), "s")
        rows = []
        for f in sorted(cfg["notes"][0].rglob(cfg["notes"][1])) + cfg.get("extra", []):
            md = f.read_text(encoding="utf-8")
            title = md.splitlines()[0].lstrip("# ").strip()
            w = note_words(md)
            hit = [(" ".join(w[i:i + N]) in grams) for i in range(max(0, len(w) - N + 1))]
            share = sum(hit) / max(1, len(hit))
            # longest run: consecutive matching windows chain into one passage of N - 1 + run words
            best = cur = 0
            for h in hit:
                cur = cur + 1 if h else 0
                best = max(best, cur)
            longest = best + N - 1 if best else 0
            runs = 0
            cur = 0
            for h in hit + [False]:
                if h:
                    cur += 1
                else:
                    if cur + N - 1 >= 25:
                        runs += 1
                    cur = 0
            rows.append((title, len(w), share, longest, runs))
        tot = sum(r[1] for r in rows)
        avg = sum(r[1] * r[2] for r in rows) / tot
        flagged = [r for r in rows if r[2] >= 0.15 or r[3] >= 40]
        out += [f"## {course}: {cfg['book']}", "", f"{len(rows)} notes, {tot:,} words, {len(src):,} words of source text. Words-weighted overlap: **{avg:.1%}**. Flagged: **{len(flagged)}**.", "",
                "| Note | Words | Overlap | Longest identical passage (words) | Passages of 25+ words |", "|---|---|---|---|---|"]
        for title, n, share, longest, runs in rows:
            mark = " **flag**" if (share >= 0.15 or longest >= 40) else ""
            out.append(f"| {title} | {n:,} | {share:.1%} | {longest} | {runs}{mark} |")
        out.append("")
        print(f"  weighted overlap {avg:.1%}, flagged {len(flagged)} of {len(rows)}, max {max(r[2] for r in rows):.1%}, longest passage {max(r[3] for r in rows)} words")
    (ROOT / "tools" / ("overlap_report.md" if not only else "overlap_report.md")).write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
