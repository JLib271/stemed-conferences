"""Read the conference listings and write the website, feeds, and calendars.

    python -m stemed_conferences --out output --previous https://<owner>.github.io/<repo>
    python -m stemed_conferences --validate      # only check conferences/*.yml

Output (all static, served by GitHub Pages):
    index.html              searchable list of upcoming meetings
    conferences.json        everything listed; also tells the next run when each meeting was first seen
    feeds/new.xml           RSS of newly listed meetings
    feeds/meetings.ics      calendar of meeting dates
    feeds/deadlines.ics     calendar of proposal, registration, and travel-award deadlines
"""
import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen

from . import feeds, listings
from .disciplines import DISCIPLINES, FIELD_DISCIPLINES

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "STEMEd+ Conferences (https://github.com/JLib271/stemed-conferences)"
SPONSOR_TYPES = ["US society", "International society", "US federal agency"]


def load_config(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


def load_previous(previous: Optional[str]) -> List[dict]:
    """Meetings from the last published conferences.json (a URL or a local path). A missing
    or unreadable file just means a fresh start, e.g. on the very first run."""
    if not previous:
        return []
    try:
        if previous.startswith(("http://", "https://")):
            url = previous.rstrip("/") + "/conferences.json"
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as resp:
                data = json.load(resp)
        else:
            data = json.loads(Path(previous).read_text(encoding="utf-8"))
        return data.get("meetings", [])
    except Exception as exc:  # noqa: BLE001 - any failure means "start fresh"
        print(f"Note: no previous listings loaded from {previous} ({exc}).")
        return []


def run(out: Path, previous: Optional[str], today: dt.date, now: Optional[dt.datetime] = None) -> dict:
    now = now or dt.datetime.combine(today, dt.time(12), tzinfo=dt.timezone.utc)
    site = load_config("site.json")
    first_seen: Dict[str, str] = {m["id"]: m.get("first_seen", today.isoformat()) for m in load_previous(previous)}

    entries, problems = listings.load()
    if problems:
        raise SystemExit("Problems in conferences/:\n  " + "\n  ".join(problems))
    series, meetings = [], []
    for slug, data in entries:
        s, ms = listings.to_records(slug, data, today)
        series.append(s)
        meetings += ms
    for m in meetings:
        m["first_seen"] = first_seen.get(m["id"], today.isoformat())
    meetings.sort(key=lambda m: (m["start"], m["name"].lower()))
    series.sort(key=lambda s: s["name"].lower())

    countries = sorted({m["country"] for m in meetings})
    payload = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": today.isoformat(),
        "site": site,
        "disciplines": list(DISCIPLINES),
        "field_disciplines": list(FIELD_DISCIPLINES),
        "kinds": listings.KIND_LABELS,
        "sponsor_types": SPONSOR_TYPES,
        "countries": countries,
        "review": [{"title": s["name"], "file": s["file"], "why": s["review"]} for s in series if s["review"]],
        "series": series,
        "meetings": meetings,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "conferences.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                                          encoding="utf-8")
    shutil.copyfile(ROOT / "site" / "index.html", out / "index.html")
    for name in ("stemedplus-commons-logo.png", "stemedplus-commons-logo-white.png", "stemedplus-theme.css", "manrope.woff"):
        shutil.copyfile(ROOT / "site" / name, out / name)
    feeds.write_rss(out / "feeds" / "new.xml", meetings, site, now)
    feeds.write_ics(out / "feeds", meetings, site, now)
    print(f"Wrote {len(meetings)} upcoming meeting(s) from {len(series)} series; "
          f"{len(payload['review'])} series to re-check.")
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--previous", help="URL of the published site (or a local conferences.json)")
    ap.add_argument("--validate", action="store_true", help="only check conferences/*.yml")
    args = ap.parse_args(argv)
    if args.validate:
        entries, problems = listings.load()
        for p in problems:
            print(p)
        print(f"{len(entries)} valid file(s), {len(problems)} problem(s).")
        return 1 if problems else 0
    run(args.out, args.previous, dt.date.today())
    return 0


if __name__ == "__main__":
    sys.exit(main())
