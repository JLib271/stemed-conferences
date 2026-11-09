# Adding or updating a conference

Each conference series is one YAML file in `conferences/`, named for the series (for example `narst.yml`).
The full list of fields, with descriptions, is in `schema/conference.schema.json`.

## Before you add a meeting

1. **Check who runs it.** The society, association, or US federal agency must be named on its own website as
   running or funding the meeting. Look up the sponsor itself, not only the meeting page.
2. **Leave out anything you are unsure about,** including anything run by a for-profit conference company,
   anything that looks predatory (pay-to-present with little review, very broad topics, many unrelated
   "conferences" from one organizer), and meetings run only by a university or company.
3. **Check it fits STEM+ education:** an education conference, a discipline meeting with education sessions,
   divisions, or tracks, or a meeting in History & Philosophy of Science, Human Dimensions, or
   Science & Health Communication.

## Example

```yaml
name: NARST Annual International Conference
short: NARST
sponsors: [NARST (National Association for Research in Science Teaching)]
sponsor_type: US society            # US society | International society | US federal agency
kind: education                     # education | track | field
disciplines: [Science Education]    # leave out for meetings open to all STEM+ fields
url: https://narst.org/conferences
frequency: annual                   # annual | twice a year | biennial | quadrennial | irregular
schedule: Every March or April; proposals are usually due in mid-August.
travel_support: Graduate student travel awards.      # only if the sponsor offers it
travel_support_url: https://example.org/awards
summary: The main research meeting for science education researchers.
checked: 2026-11-09                 # the day you checked the sponsor's pages
meetings:
  - name: NARST 2027
    start: 2027-03-14
    end: 2027-03-17
    city: Boston, Massachusetts
    country: USA
    venue: Sheraton Boston
    format: hybrid                  # in person | hybrid | online
    url: https://narst.org/conferences/2027-annual-conference
    dates_source: official          # official: on the meeting page; announced: announced, not yet on the page
    deadlines:
      - {label: Proposals due, date: 2026-08-15, kind: proposal}   # proposal | registration | travel | other
```

Quote any label that contains a comma: `{label: "Posters, demos, and panels due", date: 2026-09-30}`.

Past meetings can stay in the file; the site hides them. When new dates are announced, add a meeting and update
`checked`. Then run:

```sh
python -m stemed_conferences --validate
python -m unittest discover -s tests -t .
```

Write summaries in your own words. Listings are shared under CC BY 4.0.
