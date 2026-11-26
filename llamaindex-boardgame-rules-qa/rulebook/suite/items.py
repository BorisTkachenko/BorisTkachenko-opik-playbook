"""The rule-level cases: one question per rule, each pinned to a game and a section."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleCase:
    question: str
    game: str            # the game whose rulebook governs the answer
    section: str         # the section number that must be cited ("" = rulebooks are silent)
    assertions: tuple[str, ...]


CASES: tuple[RuleCase, ...] = (
    RuleCase(
        "How many lantern tiles does each Lanternfall player start with?",
        "Lanternfall", "1",
        ("The answer states each player starts with 5 lantern tiles",
         "The answer cites Lanternfall, Section 1"),
    ),
    RuleCase(
        "In Saltmarsh Couriers, how many route cards do I draw and play on my turn?",
        "Saltmarsh Couriers", "2",
        ("The answer states you draw 2 route cards and play exactly 1",
         "The answer cites Saltmarsh Couriers, Section 2"),
    ),
    RuleCase(
        "How many points does a chain of five lit lanterns of one colour score in Lanternfall?",
        "Lanternfall", "3",
        ("The answer states 2 points per lit lantern plus a 6 point bonus for the chain, "
         "with the bonus counted once per chain (total 16)",
         "The answer cites Lanternfall, Section 3"),
    ),
    RuleCase(
        "I am holding two undelivered parcels when the storm marker reaches the last "
        "weather space in Saltmarsh Couriers. What do I lose?",
        "Saltmarsh Couriers", "3",
        ("The answer states a loss of 3 points per undelivered parcel, so 6 points in total",
         "The answer cites Saltmarsh Couriers, Section 3"),
    ),
    RuleCase(
        "In Quillfire Duel, both wizards reach 0 ink on the same turn. What now?",
        "Quillfire Duel", "3",
        ("The answer states the duel is a draw followed by one sudden-death round",
         "The answer cites Quillfire Duel, Section 3"),
    ),
    RuleCase(
        "In Quillfire Duel, may I re-roll after rolling three flames?",
        "Quillfire Duel", "4",
        ("The answer states that you may not re-roll after a triple flare, which deals 8 damage",
         "The answer cites Quillfire Duel, Section 4"),
    ),
    RuleCase(
        "What is the hand limit in Lanternfall?",
        "Lanternfall", "",
        ("The answer says the Lanternfall rulebook does not give a hand limit, and does not "
         "borrow a number from another game",),
    ),
    RuleCase(
        "Can I trade parcels with another courier in Saltmarsh Couriers?",
        "Saltmarsh Couriers", "",
        ("The answer says the rulebook does not cover trading parcels rather than inventing a rule",),
    ),
)

GLOBAL_ASSERTIONS = (
    "The answer only states rules that appear in the retrieved rulebook excerpts and never "
    "applies a rule from a different game than the one the question names",
    "The answer addresses the question that was asked",
)
