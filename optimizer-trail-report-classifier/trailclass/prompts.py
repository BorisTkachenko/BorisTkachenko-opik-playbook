"""The hand-written starting prompt.

It is the kind of first draft people write: the categories are mentioned in
passing in prose, nothing says which exact words to answer with, and nothing says what to do
when a report fits two categories at once.
"""

BASELINE_SYSTEM = """\
You work for the Ridgeback Hollow National Park ranger station. Visitors
send in trail reports. Look at each report and tell us which kind it is:
a hazard on the trail, a wildlife sighting, a facility problem, something
lost or found, a compliment, or something else. Reply with the category."""

USER_TEMPLATE = "{report}"
