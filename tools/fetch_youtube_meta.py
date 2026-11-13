"""fetch_youtube_meta.py   reads the public facts of every course video from the TechVersation channel (read-only API calls).

For each video id in OnlineCourses/<course>/upload_progress.json it stores the chapters (from the description), the length and the
privacy status in src/data/youtube.json. The OAuth token stays where it is (OnlineCourses/PMP/youtube_token.json); nothing secret is written.
Run: python -X utf8 tools/fetch_youtube_meta.py
"""
import json
import re
from pathlib import Path

OC = Path(r"D:\Certifications\OnlineCourses")
TOKEN = OC / "PMP" / "youtube_token.json"
OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "youtube.json"


def ids():
    out = {}
    for c in ("CSM", "PMP", "KCNA", "AIGP"):
        d = json.loads((OC / c / "upload_progress.json").read_text(encoding="utf-8"))
        for k, v in d["videos"].items():
            out[v["id"]] = (c.lower(), k)
    for c, slug in (("AWS-CLF", "clf"), ("AWS-AIF", "aif"), ("AWS-SAA", "saa"), ("AWS-DEA", "dea"), ("Anthropic-CCAR-F", "ccar"), ("Anthropic-CCDV-F", "ccdv"), ("Anthropic-CCAO-F", "ccao"), ("Anthropic-CCAR-P", "ccarp"), ("CNCF-CKA", "cka"), ("AZ-900", "az900"), ("AI-901", "ai901"), ("Security-SY0-801", "sy0801"), ("SC-900", "sc900")):          # progress files like the first loop, but the site slug differs from the folder
        if not (OC / c / "upload_progress.json").exists():
            continue
        d = json.loads((OC / c / "upload_progress.json").read_text(encoding="utf-8"))
        for k, v in d["videos"].items():
            out[v["id"]] = (slug, k)
    for c, slug in (("CDMP", "cdmp"), ("TOGAF", "togaf"), ("AIGovernance", "aigov")):       # courses whose progress file lists one video per module
        d = json.loads((OC / c / "upload_progress.json").read_text(encoding="utf-8"))
        for k, v in d["uploaded"].items():
            out[v] = (slug, k)
    return out


def secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def main():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN), ["https://www.googleapis.com/auth/youtube"])
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)
    wanted = ids()
    keys = list(wanted)
    meta = {}
    for i in range(0, len(keys), 50):
        batch = keys[i:i + 50]
        r = yt.videos().list(part="snippet,contentDetails,status", id=",".join(batch)).execute()
        for it in r["items"]:
            chapters = []
            for line in it["snippet"]["description"].splitlines():
                m = re.match(r"^\s*(?:(\d+):)?(\d{1,2}):(\d\d)\s+(.+?)\s*$", line)
                if m:
                    chapters.append([int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3)), m.group(4)])
            meta[it["id"]] = dict(course=wanted[it["id"]][0], key=wanted[it["id"]][1], title=it["snippet"]["title"], seconds=secs(it["contentDetails"]["duration"]),
                                  published=it["snippet"]["publishedAt"], privacy=it["status"]["privacyStatus"], embeddable=it["status"].get("embeddable", True), chapters=chapters)
    ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    (OUT.parent / "channel.json").write_text(json.dumps(dict(id=ch["id"], title=ch["snippet"]["title"], handle=ch["snippet"].get("customUrl", "")), ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [k for k in keys if k not in meta]
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [(v["key"], v["privacy"]) for v in meta.values() if v["privacy"] != "public" or not v["embeddable"]]
    print(len(meta), "videos read;", len(missing), "missing:", missing[:5], "; not public or not embeddable:", bad[:5])
    print("with chapters:", sum(1 for v in meta.values() if v["chapters"]))


if __name__ == "__main__":
    main()
