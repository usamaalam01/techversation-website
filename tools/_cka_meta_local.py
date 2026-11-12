"""_cka_meta_local.py   adds the CKA videos to src/data/youtube.json WITHOUT the YouTube Data API (its daily quota was used up).

Source of each field:
  title, chapters   the text the upload script wrote to YouTube (build_items() of the CKA course folder; the chapter times are read from the rendered clips)
  seconds           the length of the local MP4 (ffprobe)
  published         the publish time YouTube reported when the videos were listed after the upload (CNCF-CKA/_dups.json)
  privacy/embeddable  YouTube's public oEmbed endpoint answers 200 only for a video that is public or unlisted and embeddable
Run tools/fetch_youtube_meta.py later (when the quota is back) to replace these values with the ones read from the API."""
import json
import re
import subprocess
import sys
import urllib.request
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
OC = Path(r"D:\Certifications\OnlineCourses")
CKA = OC / "CNCF-CKA"
OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "youtube.json"
sys.path.insert(0, str(CKA))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os  # noqa: E402
os.chdir(CKA)
import upload_to_youtube as U  # noqa: E402

prog = json.loads((CKA / "upload_progress.json").read_text(encoding="utf-8"))
vids = {k: v["id"] for k, v in prog["videos"].items()}
dups = json.loads((CKA / "_dups.json").read_text(encoding="utf-8"))
published = {}
for title, lst in dups.items():
    for p, vid in lst:
        published[vid] = p
items = {i["key"]: i for i in U.build_items()}
meta = json.loads(OUT.read_text(encoding="utf-8"))
ok = bad = 0
for key, vid in vids.items():
    it = items[key]
    mp4 = it["video"]
    dur = subprocess.run([U.FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    chapters = []
    for line in it["body"].splitlines():
        m = re.match(r"^\s*(?:(\d+):)?(\d{1,2}):(\d\d)\s+(.+?)\s*$", line)
        if m:
            chapters.append([int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3)), m.group(4)])
    try:
        r = urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json", timeout=30)
        embeddable = r.status == 200
    except Exception as e:  # 401 = private, 404 = missing, 403 = embedding off
        embeddable = False
        print("oembed failed", key, vid, e)
    ok += embeddable
    bad += (not embeddable)
    meta[vid] = dict(course="cka", key=key, title=it["title"], seconds=int(round(float(dur))), published=published.get(vid, "2026-11-11T09:00:00Z"),
                     privacy="public" if embeddable else "unknown", embeddable=embeddable, chapters=chapters)
OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{ok} CKA videos public and embeddable by oEmbed, {bad} not; with chapters: {sum(1 for v in meta.values() if v['course'] == 'cka' and v['chapters'])}")
