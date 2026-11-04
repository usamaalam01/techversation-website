# Techversation website

Free certification exam prep: video lectures from the TechVersation YouTube channel, standardized study notes, glossaries, slide decks and a study planner. Static site built with Astro, searched with Pagefind. No server, no database, no accounts.

## Run it

```powershell
cd D:\Techversation
npm install                 # once
npm run build               # builds dist\ and the search index
npm run preview             # http://localhost:4321/
python -X utf8 tools\validate_site.py     # 600+ checks on the built site
```

Light is the default look. The Light / Dark switch is in the header; the choice is remembered in the browser. For a quick look add `?theme=dark` to any address.

## Where the content comes from

The course folders live in the private Certifications repo (`D:\Certifications`). Nothing is copied by hand; two scripts do it, and only website-ready material reaches this project (no source PDFs, no secrets):

| Script | What it does |
|---|---|
| `tools\fetch_youtube_meta.py` | Reads the public facts of every video (length, chapters, privacy, upload date) and the channel handle from YouTube, read-only. Writes `src\data\youtube.json` and `channel.json`. Needs the OAuth token that the course upload scripts already use (it stays in the Certifications repo). |
| `tools\export_content.py` | Builds `src\data\` (courses, modules, transcripts, notes, glossaries) and `public\` (covers, module thumbnails, CSM diagrams, slide decks) from the course folders. Verifies every CSM glossary definition against the 2020 Scrum Guide text. |
| `..\Certifications\OnlineCourses\make_course_covers.py` | The generic course covers (exam name, no module or part). CDMP uses its own banner. |

**Add a course:** build it in `OnlineCourses\<COURSE>` as usual, add one entry to `COURSES` (and to `INSTITUTES` if the institute is new) in `tools\export_content.py`, then `python tools\fetch_youtube_meta.py`, `python tools\export_content.py`, `npm run build`, `python tools\validate_site.py`.

## Structure

- `src\pages\` home, `[institute]\` (institute page), `[institute]\[cert]\` (course page), `...\video\[module]\` (module page), `...\notes\[topic]\` (study note), `search`, `study-plan`, about, disclaimer, privacy, 404, `robots.txt`.
- `src\scripts\` small browser scripts: theme switch and menu (`common.ts`), home picker and request form, course tabs and progress, module player, notes, search (Pagefind), study plan.
- `src\styles\global.css` the design tokens (light first, dark under `[data-theme="dark"]`) and all components; one accent color per course.
- `design\mockup\` the approved HTML mockup, kept for reference.

## Rules the validator enforces

Every video id on its page and public/embeddable on YouTube; a transcript for every part; every deck file present; one h1, a title and a description, a canonical link and the independence notice on every page; no year in a title, description or headline; the word "certified" absent from the site's own text; internal links and images resolve; JSON-LD parses; sitemap and search index built; no PDF, secret, local path or e-mail address in the output; course cards use the generic covers, never a module thumbnail.

## What is done and what is not

- Done: 7 courses (CSM, PMP, KCNA, AIGP, CDMP, TOGAF and the AI Governance training course), 109 modules, 160 videos (35 hours) with transcripts, 97 slide decks, 73 study notes (CSM 14 topics, PMP 35 topics, CDMP 14 chapters and 2 Specialist notes, TOGAF 8 weekly guides), glossaries for CSM (16 terms, the Guide's own sentences) and KCNA (106 terms), exam facts for CSM and KCNA with their sources, study planner, search, progress saved in the browser. 203 pages.
- Study notes (`tools\notes_lib.py`): the wording of the summaries is not changed. Every note gets the same at-a-glance block, a collapsible "Scope and sources" block holding the original header lines, numbered sections with a table of contents, callouts (Exam angle, Exam tip, Old wording, Terminology), "Beyond ..." tags, diagrams as figures (152 in all), "Topic N" cross-references turned into links, exam questions with the answer on demand, and the quick-reference card. Navigation: a button and a tab on the course page (filter, "Study order" and "Exam domain" views), the list of all notes beside every note, previous/next, and a link from each video module to its topics (PMP's module-to-topic map comes from `OnlineCourses\PMP\COURSE_PLAN.md`).
- The export compares every note with its source (words, tables, diagrams, questions, sections) and the validator repeats the comparison on the built pages.
- Overlap check (`tools\overlap_check.py`, the report `tools\overlap_report.md` is generated and not committed): PMP notes against the PMBOK Guide 8th Edition, 1.2% of 8-word sequences, longest identical passage 29 words, none flagged. CDMP notes against the DMBOK 2nd Edition, 5.4%, one chapter flagged (Chapter 5: the data modeling definition and the model-quality question list, 78 and 94 words). Reword or mark them as quotations before deployment.
- TOGAF: the 8 weekly study guides (`TOGAF\week1` to `week8`), with the Week 1 quick-reference card appended to Week 1, ASCII diagrams kept exactly, review checklists as tick boxes (kept in the browser) and links between the weeks turned into links between the notes. Which lectures each week goes with is an editorial choice made in `NOTES["togaf"]["modules_of"]` in `tools\export_content.py`. The guides were written around TOGAF 9 with notes on the 10th edition, while the course is TOGAF 10: the guides say so in their own "Read first" section.
- DAMA Specialist exam notes: the two Specialist study plans (`DAMA\CDMP-Practitioner`: Data Governance and Stewardship, Reference and Master Data) are published as notes 15 and 16 of the CDMP course. They were written for one candidate, so the personal parts (name, score, strengths and gaps, the weekly schedule with its personal tasks, changelog, study-materials list) are removed by `_PLAN_SCRUB` in `tools\export_content.py`; every removal is listed in `tools\_private\scrub_report.md` (git-ignored, never published). The validator fails the build if the candidate's name or employer appears in the output.
- Training courses: `institute: "training"` (hidden from the institute picker) gives `/training/<course>/`. AI Governance is the first; Prompt Engineering and Spec-Driven Development are "coming soon" cards.
- AIGP and KCNA notes come later (the user's decision).
- Exam facts for PMP, AIGP and CDMP, and fee and prerequisite lines for all, are added with their official source and a checked-on date.
- Comments: the module page has a "Discuss on YouTube" link; Giscus comments need a public GitHub repo with Discussions and are added at launch.
- Request form: opens the visitor's e-mail app with the request ready to send (no backend). A form service (for example Web3Forms) can replace it.
- Fonts load from Google Fonts for now; self-hosting them is a small follow-up (the privacy page says so).
- Domain: `astro.config.mjs` has a placeholder `site`; set it when the domain is registered. No analytics yet.
- Narration shows as spoken in the transcripts. The validator warns where the narration says "certified" (CDMP and CSM module 0) or speaks a year (CDMP 00, 01, 02, 13; PMP 00, 03), because those are in the published videos.
