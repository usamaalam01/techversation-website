# Techversation design mockup

Static HTML mockup of the website, built before development so the design can be reviewed. Open `index.html` in a browser (it loads the fonts from Google Fonts, so it needs internet for the exact look).

## Pages

| File | What it shows |
|---|---|
| `index.html` | Landing page: hero with the Institute to Certification picker and search, featured courses, institutes, how it works, training (coming soon), request a course, YouTube subscribe |
| `certification.html?c=csm` | A certification: exam fact card, progress, tabs for Video course, Study notes, Glossary, Downloads, Study plan. Try `c=pmp`, `kcna`, `aigp`, `cdmp` |
| `module.html?c=csm&m=05` | A module: video, parts, transcript, chapters, downloads, discussion, mark as done, sidebar, previous/next. Any module number works |
| `notes.html` | A study note in the standard layout (CSM Topic 07, an excerpt of the real summary) |
| `search.html?q=sprint` | Search with institute and type filters, over all the real module titles, notes and the sample glossary |
| `study-plan.html?c=csm` | Study-plan generator: exam date, hours per week, include notes; uses the real video lengths |

Add `?theme=light` or `?theme=dark` to any page to force a theme. The sun/moon button switches it and remembers the choice.

## What is real and what is sample

- Real: course, module and video-part titles, YouTube video IDs, video lengths, thumbnails, the CSM summary titles and learning objectives, reading times, the Topic 07 text, the narration transcript of CSM Module 05, KCNA and CSM exam numbers from the course files.
- Sample: the glossary (12 CSM terms), chapter timestamps (scaled from the slide timings), the "4 of 19 modules done" starting progress, every download (marked "At launch"), the discussion box, the subscribe link, the request form (nothing is sent).
- Not checked yet: the CSM prerequisite and fee line in the exam card. Exam facts get a source and a "checked on" date before launch.
- Every video link opens YouTube in a new tab. The live site loads the player in place.

## Design

Dark navy base from the logo, with one accent color per course taken from its thumbnails (CSM copper, PMP gold, KCNA emerald, AIGP blue, CDMP violet). The logo's ring gradient is used only on the finder, progress and key panels. Fonts: Bricolage Grotesque for headings, IBM Plex Sans for text, IBM Plex Mono for facts and labels. Institutes appear as plain names with a short initials tile, no logos.

## Files

`assets/styles.css`, `assets/app.js` (behavior), `assets/data.js` (generated), `assets/img/` (resized thumbnails), `assets/logo.jpg` (channel avatar, 160 px; replace with the original), `_tools/build_mock_data.py` (rebuilds `data.js` and the images from the course folders in `D:\Certifications`).
