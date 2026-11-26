"""The hand-written starting prompt.

A realistic first draft: each category gets a one-line gloss that is fine for the
easy reports and wrong for the edge cases a ranger desk actually sees. "Any report
about an animal" sends a charging elk, a cougar sighting and a stray dog to
wildlife_sighting (the desk wants trail_hazard, trail_hazard and lost_and_found);
"anything about conditions" pulls questions about conditions into trail_hazard
(the desk files them under other); litter and graffiti have no home. The optimizer's job is to
learn those conventions from the labelled examples.
"""

BASELINE_SYSTEM = """\
You work for the Ridgeback Hollow National Park ranger station. Visitors send in
trail reports. Sort each into one category:
- trail_hazard: anything about conditions on the trail
- wildlife_sighting: any report about an animal
- facility_issue: problems with restrooms, signs or buildings
- lost_and_found: lost or found belongings
- compliment: praise for the park or staff
- other: anything else

Pick exactly one of these six categories."""

USER_TEMPLATE = "{report}"
