# STEMEd+ Conferences

Upcoming meetings, proposal deadlines, and travel support for STEM+ education, in one place:
**https://jlib271.github.io/stemed-conferences/**

STEMEd+ Conferences is part of [STEMEd+ Commons](https://stemedplus.hcommons.org/), with
[STEMEd+ Jobs](https://jlib271.github.io/stemed-jobs/), [STEMEd+ Funding](https://jlib271.github.io/stemed-funding/),
the [STEMEd+ Digest](https://jlib271.github.io/STEMEd-Digest/), [STEMEd+ Professional Learning](https://jlib271.github.io/stemed-professional-learning/), and the
[STEM+ Education Research Graduate Programs](https://jlib271.github.io/stem-ed-research-programs/) list.

## What is listed

- **Who runs it.** Only meetings run by a scholarly or professional society or association (in the US or
  internationally), or funded by a US federal agency such as NSF. Meetings run by for-profit conference
  companies are not listed, and neither is anything that might be predatory. **If we are not sure, we leave it out.**
- **What it covers.** Three types:
  - education conferences (NARST, AERA, ASEE, SIGCSE, RUME, ...);
  - discipline meetings with education sessions, divisions, or tracks (ACS, AGU, GSA, JMM, APS, ...);
  - meetings in the field-scope disciplines, History & Philosophy of Science, Human Dimensions, and
    Science & Health Communication, which cover those fields themselves (HSS, PSA, 4S, IASNR, ICA, PCST, ...).
- **What it shows.** Dates and place, proposal and registration deadlines, travel awards and student support,
  and how often each meeting runs. Meetings whose next dates are not announced stay listed under
  "Recurring meetings" so you know what is coming.
- **Disciplines** come from the list shared across STEMEd+ Commons, kept in
  [HuMeta](https://github.com/JLib271/HuMeta) (`standard/humeta/stemedplus_disciplines.json`). Each build
  refreshes the copy in `stemed_conferences/stemedplus_disciplines.json`, and keeps the stored copy if the
  download fails or HuMeta's version is older.

Dates come from each sponsor's own pages. A meeting marked **Confirm dates** was announced by the sponsor
or a partner society, but its own page does not show the dates yet. Always confirm before you submit or travel.

### Considered but not listed

Meetings we looked at and left out because they are run by companies or universities rather than a society or
federal agency, or because we could not confirm who runs them: ICEEL, CSEDU, SXSW EDU, the CDIO conference,
and Pathways: Human Dimensions of Wildlife (run by a university department). General K-12 leadership and policy
meetings (AASA, ASCD, CoSN, AEFP) are outside the STEM+ scope.

## Feeds and calendars

| | |
|---|---|
| `feeds/meetings.ics` | Every listed meeting, for Google Calendar, Outlook, or Apple Calendar ("add calendar from URL") |
| `feeds/deadlines.ics` | Proposal, registration, and travel-award deadlines that have not passed |
| `feeds/new.xml` | RSS of newly listed meetings |
| `conferences.json` | Everything on the site, for reuse |

## Add or correct a listing

- [Suggest a conference](https://github.com/JLib271/stemed-conferences/issues/new?template=suggest_conference.yml)
- [Report new dates or a correction](https://github.com/JLib271/stemed-conferences/issues/new?template=update_conference.yml)
- No GitHub account? Email the maintainer, Julie Libarkin, at libarkin@msu.edu.

To edit directly, see [CONTRIBUTING.md](CONTRIBUTING.md). Each series is one YAML file in `conferences/`,
checked against `schema/conference.schema.json`.

## How it works

A GitHub Actions workflow (`.github/workflows/update.yml`) runs every day and on every push:

1. refreshes the shared discipline list from HuMeta;
2. runs the tests and checks every file in `conferences/`;
3. builds the site into `output/` and publishes it to GitHub Pages. Meetings that have ended drop off,
   deadlines that have passed are marked, and the date each meeting was first listed is carried over from
   the published `conferences.json` for the RSS feed.

The footer's "For maintainers" box lists files to re-check: any not checked in 180 days, and any meeting with
announced (not yet official) dates that starts within 120 days.

Run it locally:

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -t .
python -m stemed_conferences --validate
python -m stemed_conferences --out output    # then open output/index.html through a local web server
```

To publish: Settings → Pages → Source: **GitHub Actions**.

## License

Code: MIT ([LICENSE](LICENSE)). Listings in `conferences/`: CC BY 4.0 ([conferences/LICENSE.md](conferences/LICENSE.md)).
