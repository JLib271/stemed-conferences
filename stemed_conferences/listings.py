"""Conference series kept by hand, one YAML file each in conferences/."""
import datetime as dt
import json
from pathlib import Path
from typing import List, Tuple

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .disciplines import DISCIPLINES

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "conferences"
SCHEMA = json.loads((ROOT / "schema" / "conference.schema.json").read_text(encoding="utf-8"))
# The allowed disciplines are the shared STEMEd+ list, not a copy in the schema file.
SCHEMA["properties"]["disciplines"]["items"] = {"enum": list(DISCIPLINES)}
REVIEW_AFTER_DAYS = 180
# Dates a partner announced should be confirmed on the meeting's own page before it starts.
CONFIRM_WITHIN_DAYS = 120

KIND_LABELS = {
    "education": "Education conference",
    "track": "Discipline meeting with education sessions",
    "field": "Field meeting (HPS, Human Dimensions, Science & Health Communication)",
}


def _plain(value):
    """YAML reads dates as date objects; the schema and the site want strings."""
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def _date_problems(data: dict) -> List[str]:
    problems = []
    for n, m in enumerate(data.get("meetings", [])):
        if m["end"] < m["start"]:
            problems.append(f"meetings.{n}: ends ({m['end']}) before it starts ({m['start']})")
        for d in m.get("deadlines", []):
            if d["date"] > m["end"]:
                problems.append(f"meetings.{n}: deadline '{d['label']}' ({d['date']}) is after the meeting ends")
    return problems


def load(folder: Path = FOLDER) -> Tuple[List[Tuple[str, dict]], List[str]]:
    """(slug, series) for every valid file, and a list of problems."""
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    entries, problems = [], []
    for path in sorted(folder.glob("*.yml")):
        try:
            data = _plain(yaml.safe_load(path.read_text(encoding="utf-8")))
        except yaml.YAMLError as exc:
            problems.append(f"{path.name}: not valid YAML ({exc})")
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        for e in errors:
            where = ".".join(str(p) for p in e.path) or "(file)"
            problems.append(f"{path.name}: {where}: {e.message}")
        if errors:
            continue
        extra = _date_problems(data)
        problems += [f"{path.name}: {p}" for p in extra]
        if not extra:
            entries.append((path.stem, data))
    return entries, problems


def _series_fields(slug: str, s: dict) -> dict:
    return {
        "series": slug,
        "series_name": s["name"],
        "short": s.get("short", ""),
        "sponsors": s["sponsors"],
        "sponsor_type": s["sponsor_type"],
        "funding_note": s.get("funding_note", ""),
        "kind": s["kind"],
        "disciplines": s.get("disciplines", []),
        "all_fields": not s.get("disciplines"),
        "travel_support": s.get("travel_support", ""),
        "travel_support_url": s.get("travel_support_url", ""),
    }


def to_records(slug: str, s: dict, today: dt.date) -> Tuple[dict, List[dict]]:
    """A record for the series and one for each meeting that has not ended."""
    today_s = today.isoformat()
    base = _series_fields(slug, s)
    meetings = []
    for m in sorted(s.get("meetings", []), key=lambda m: m["start"]):
        if m["end"] < today_s:
            continue
        deadlines = sorted(
            ({"label": d["label"], "date": d["date"], "kind": d.get("kind", "other"), "note": d.get("note", ""),
              "passed": d["date"] < today_s} for d in m.get("deadlines", [])),
            key=lambda d: d["date"])
        meetings.append(dict(base, **{
            "id": f"meeting:{slug}:{m['start']}",
            "name": m["name"],
            "start": m["start"],
            "end": m["end"],
            "city": m["city"],
            "country": m["country"],
            "venue": m.get("venue", ""),
            "format": m.get("format", "in person"),
            "url": m["url"],
            "dates_source": m["dates_source"],
            "note": m.get("note", ""),
            "deadlines": deadlines,
            "happening": m["start"] <= today_s,
            "file": f"conferences/{slug}.yml",
        }))
    review = []
    if s["checked"] < (today - dt.timedelta(days=REVIEW_AFTER_DAYS)).isoformat():
        review.append(f"last checked {s['checked']}")
    soon = (today + dt.timedelta(days=CONFIRM_WITHIN_DAYS)).isoformat()
    for m in meetings:
        if m["dates_source"] == "announced" and m["start"] <= soon:
            review.append(f"confirm {m['name']} on the meeting's own page")
    series = dict(base, **{
        "id": f"series:{slug}",
        "name": s["name"],
        "url": s["url"],
        "frequency": s["frequency"],
        "schedule": s["schedule"],
        "summary": s["summary"],
        "checked": s["checked"],
        "next": meetings[0]["id"] if meetings else "",
        "meetings": [m["id"] for m in meetings],
        "review": review,
        "file": f"conferences/{slug}.yml",
    })
    return series, meetings
