"""RSS of newly listed meetings, and two calendars: one of meetings, one of deadlines."""
import datetime as dt
from email.utils import format_datetime
from pathlib import Path
from typing import List
from xml.etree import ElementTree as ET


def place(m: dict) -> str:
    if m["format"] == "online":
        return "Online"
    where = m["city"] if m["country"] in ("USA", "United States") else f"{m['city']}, {m['country']}"
    return where + (" and online" if m["format"] == "hybrid" else "")


def when(m: dict) -> str:
    s, e = dt.date.fromisoformat(m["start"]), dt.date.fromisoformat(m["end"])
    if s == e:
        return f"{s:%B} {s.day}, {s.year}"
    if (s.year, s.month) == (e.year, e.month):
        return f"{s:%B} {s.day}–{e.day}, {s.year}"
    if s.year == e.year:
        return f"{s:%B} {s.day} – {e:%B} {e.day}, {s.year}"
    return f"{s:%B} {s.day}, {s.year} – {e:%B} {e.day}, {e.year}"


def describe(m: dict) -> str:
    parts = [f"{when(m)}, {place(m)}", " and ".join(m["sponsors"])]
    upcoming = [d for d in m["deadlines"] if not d["passed"]]
    if upcoming:
        d = upcoming[0]
        parts.append(f"{d['label']}: {d['date']}")
    if m.get("travel_support"):
        parts.append("Travel support: " + m["travel_support"])
    if m["dates_source"] == "announced":
        parts.append("Dates announced; confirm on the meeting page")
    return ". ".join(p.rstrip(".") for p in parts if p) + "."


def write_rss(path: Path, meetings: List[dict], site: dict, now: dt.datetime) -> None:
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = f"{site['title']}: newly listed meetings"
    ET.SubElement(ch, "link").text = site["site_url"]
    ET.SubElement(ch, "description").text = site["tagline"]
    ET.SubElement(ch, "lastBuildDate").text = format_datetime(now)
    newest = sorted(meetings, key=lambda m: (m["first_seen"], m["id"]), reverse=True)[: site.get("feed_size", 100)]
    for m in newest:
        e = ET.SubElement(ch, "item")
        ET.SubElement(e, "title").text = m["name"]
        ET.SubElement(e, "link").text = m["url"]
        ET.SubElement(e, "guid", isPermaLink="false").text = m["id"]
        ET.SubElement(e, "description").text = describe(m)
        day = dt.datetime.fromisoformat(m["first_seen"]).replace(tzinfo=dt.timezone.utc)
        ET.SubElement(e, "pubDate").text = format_datetime(day)
        for d in m["disciplines"]:
            ET.SubElement(e, "category").text = d
        ET.SubElement(e, "category").text = m["sponsor_type"]
    ET.indent(rss)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding="utf-8") + b"\n")


def _ics_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> List[str]:
    """iCalendar lines are at most 75 octets; longer ones continue with a leading space."""
    out, data = [], line.encode("utf-8")
    while len(data) > 75:
        cut = 75 if not out else 74
        while cut and (data[cut] & 0xC0) == 0x80:   # do not split a UTF-8 character
            cut -= 1
        out.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    out.append(data.decode("utf-8"))
    return [out[0]] + [" " + s for s in out[1:]]


def _event(uid: str, stamp: str, start: str, end: str, summary: str, description: str, url: str,
           location: str = "") -> List[str]:
    last = (dt.date.fromisoformat(end) + dt.timedelta(days=1)).strftime("%Y%m%d")
    lines = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}",
             f"DTSTART;VALUE=DATE:{start.replace('-', '')}", f"DTEND;VALUE=DATE:{last}",
             "SUMMARY:" + _ics_text(summary)]
    if location:
        lines.append("LOCATION:" + _ics_text(location))
    lines += ["DESCRIPTION:" + _ics_text(description), "URL:" + url, "END:VEVENT"]
    return [part for line in lines for part in _fold(line)]


def meeting_event(m: dict, stamp: str) -> List[str]:
    location = ", ".join(x for x in (m["venue"], place(m)) if x)
    return _event(f"{m['id'].replace(':', '-')}@stemed-conferences", stamp, m["start"], m["end"], m["name"],
                  f"{describe(m)} Always confirm on the meeting page: {m['url']}", m["url"], location)


def deadline_event(m: dict, d: dict, stamp: str) -> List[str]:
    slug = "".join(c if c.isalnum() else "-" for c in d["label"].lower()).strip("-")
    note = (d["note"] + " ") if d.get("note") else ""
    return _event(f"{m['id'].replace(':', '-')}-{slug}-{d['date']}@stemed-conferences", stamp, d["date"], d["date"],
                  f"{d['label']}: {m['name']}",
                  f"{note}{m['name']}, {when(m)}, {place(m)}. Always confirm on the meeting page: {m['url']}", m["url"])


def _calendar(name: str, about: str, events: List[List[str]]) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//STEMEd+//Conferences//EN", "CALSCALE:GREGORIAN"]
    lines += _fold("X-WR-CALNAME:" + _ics_text(name)) + _fold("X-WR-CALDESC:" + _ics_text(about))
    for ev in events:
        lines += ev
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def write_ics(folder: Path, meetings: List[dict], site: dict, now: dt.datetime) -> None:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meetings.ics").write_bytes(_calendar(
        f"{site['title']}: meetings", "STEM+ education conferences. Always confirm dates on the meeting page.",
        [meeting_event(m, stamp) for m in meetings]))
    (folder / "deadlines.ics").write_bytes(_calendar(
        f"{site['title']}: deadlines",
        "Proposal, registration, and travel-award deadlines for STEM+ education conferences. Always confirm on the meeting page.",
        [deadline_event(m, d, stamp) for m in meetings for d in m["deadlines"] if not d["passed"]]))
