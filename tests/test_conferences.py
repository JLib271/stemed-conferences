import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from stemed_conferences import build, feeds, listings

TODAY = dt.date(2026, 11, 9)

SERIES = {
    "name": "Example Society Annual Meeting",
    "short": "ESAM",
    "sponsors": ["Example Society"],
    "sponsor_type": "US society",
    "kind": "education",
    "disciplines": ["Physics"],
    "url": "https://example.org/meeting",
    "frequency": "annual",
    "schedule": "Every March.",
    "travel_support": "Student travel awards.",
    "summary": "A meeting about physics teaching and learning.",
    "checked": "2026-11-01",
    "meetings": [
        {"name": "ESAM 2026", "start": "2026-03-01", "end": "2026-03-03", "city": "Austin, Texas", "country": "USA",
         "url": "https://example.org/2026", "dates_source": "official"},
        {"name": "ESAM 2027", "start": "2027-03-01", "end": "2027-03-03", "city": "Lyon", "country": "France",
         "format": "hybrid", "url": "https://example.org/2027", "dates_source": "announced",
         "deadlines": [{"label": "Proposals due", "date": "2026-10-01", "kind": "proposal"},
                       {"label": "Travel awards due", "date": "2026-12-01", "kind": "travel"}]},
    ],
}


def write(folder: Path, name: str, data: dict) -> None:
    import yaml
    (folder / f"{name}.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ListingTests(unittest.TestCase):
    def test_every_listing_is_valid(self):
        entries, problems = listings.load()
        self.assertEqual(problems, [])
        self.assertGreater(len(entries), 30)

    def test_listings_use_https_and_known_kinds(self):
        for slug, s in listings.load()[0]:
            self.assertTrue(s["url"].startswith("https://"), slug)
            self.assertIn(s["kind"], listings.KIND_LABELS)
            for m in s.get("meetings", []):
                self.assertTrue(m["url"].startswith("https://"), slug)

    def test_field_meetings_are_in_field_disciplines(self):
        from stemed_conferences.disciplines import FIELD_DISCIPLINES
        for slug, s in listings.load()[0]:
            if s["kind"] == "field":
                self.assertTrue(set(s.get("disciplines", [])) & set(FIELD_DISCIPLINES), slug)

    def test_bad_dates_and_unknown_disciplines_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = json.loads(json.dumps(SERIES))
            bad["meetings"][1]["end"] = "2027-02-01"
            write(Path(tmp), "bad", bad)
            odd = dict(SERIES, disciplines=["Astrology"])
            write(Path(tmp), "odd", odd)
            entries, problems = listings.load(Path(tmp))
            self.assertEqual(entries, [])
            self.assertTrue(any("ends" in p for p in problems))
            self.assertTrue(any("odd.yml" in p for p in problems))

    def test_records_hide_past_meetings_and_mark_passed_deadlines(self):
        series, meetings = listings.to_records("esam", SERIES, TODAY)
        self.assertEqual([m["name"] for m in meetings], ["ESAM 2027"])
        self.assertEqual([d["passed"] for d in meetings[0]["deadlines"]], [True, False])
        self.assertEqual(series["next"], "meeting:esam:2027-03-01")
        self.assertFalse(meetings[0]["all_fields"])
        self.assertEqual(meetings[0]["travel_support"], "Student travel awards.")

    def test_announced_dates_are_flagged_as_the_meeting_nears(self):
        series, _ = listings.to_records("esam", SERIES, dt.date(2026, 12, 15))
        self.assertTrue(any("confirm ESAM 2027" in r for r in series["review"]))
        series, _ = listings.to_records("esam", SERIES, dt.date(2026, 6, 1))
        self.assertFalse(any("confirm" in r for r in series["review"]))

    def test_old_checks_are_flagged(self):
        series, _ = listings.to_records("esam", dict(SERIES, checked="2025-01-01"), TODAY)
        self.assertIn("last checked 2025-01-01", series["review"])


class FeedTests(unittest.TestCase):
    def setUp(self):
        _, self.meetings = listings.to_records("esam", SERIES, TODAY)
        for m in self.meetings:
            m["first_seen"] = "2026-11-09"
        self.site = {"title": "STEMEd+ Conferences", "site_url": "https://example.org/", "tagline": "t"}
        self.now = dt.datetime(2026, 11, 9, 12, tzinfo=dt.timezone.utc)

    def test_dates_and_places_read_naturally(self):
        m = self.meetings[0]
        self.assertEqual(feeds.when(m), "March 1–3, 2027")
        self.assertEqual(feeds.place(m), "Lyon, France and online")

    def test_calendars_hold_meetings_and_open_deadlines_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds.write_ics(Path(tmp), self.meetings, self.site, self.now)
            meetings = (Path(tmp) / "meetings.ics").read_bytes().decode()
            deadlines = (Path(tmp) / "deadlines.ics").read_bytes().decode()
        self.assertIn("DTSTART;VALUE=DATE:20270301", meetings)
        self.assertIn("DTEND;VALUE=DATE:20270304", meetings)
        self.assertIn("Travel awards due", deadlines)
        self.assertNotIn("Proposals due", deadlines)
        for text in (meetings, deadlines):
            for line in text.split("\r\n"):
                self.assertLessEqual(len(line.encode("utf-8")), 75)

    def test_rss_lists_meetings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "new.xml"
            feeds.write_rss(path, self.meetings, self.site, self.now)
            text = path.read_text()
        self.assertIn("<title>ESAM 2027</title>", text)
        self.assertIn("Travel support", text)


class BuildTests(unittest.TestCase):
    def test_build_writes_the_site_and_keeps_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            first = build.run(out, None, TODAY)
            some = first["meetings"][0]["id"]
            previous = Path(tmp) / "previous.json"
            data = json.loads((out / "conferences.json").read_text())
            for m in data["meetings"]:
                if m["id"] == some:
                    m["first_seen"] = "2026-01-01"
            previous.write_text(json.dumps(data))
            second = build.run(Path(tmp) / "out2", str(previous), TODAY)
            self.assertEqual({m["id"]: m["first_seen"] for m in second["meetings"]}[some], "2026-01-01")
            for name in ("index.html", "conferences.json", "stemedplus-commons-logo.png",
                         "feeds/new.xml", "feeds/meetings.ics", "feeds/deadlines.ics"):
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
