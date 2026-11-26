"""Fictional rulebooks as plain data: game -> ordered (section number, title, text).

Every section opens with the game name so a retrieved chunk is self-describing
even when the PDF page break lands in the middle of a section.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Section:
    number: str
    title: str
    text: str


@dataclass(frozen=True)
class Rulebook:
    slug: str
    title: str
    tagline: str
    sections: tuple[Section, ...]


LANTERNFALL = Rulebook(
    slug="lanternfall",
    title="Lanternfall",
    tagline="A tile-laying game for 2 to 4 players, about 30 minutes.",
    sections=(
        Section("1", "Setup", (
            "Lanternfall setup. Each player takes 5 lantern tiles from the bag and 3 wick "
            "tokens. Reveal 6 tiles face up beside the bag as the harbor row. Place the "
            "starting dock tile in the middle of the table. The player who most recently "
            "lit a candle goes first."
        )),
        Section("2", "Turn order", (
            "Lanternfall turn order. Play passes clockwise. A turn has three steps in this "
            "order: Place one lantern tile touching the table edge-to-edge, Light it by "
            "spending one wick token, then Refill your hand to 5 tiles from the harbor row "
            "or the bag. You may skip the Light step, but an unlit lantern scores nothing."
        )),
        Section("3", "Scoring", (
            "Lanternfall scoring. Each lit lantern scores 2 points. A connected chain of 4 "
            "or more lit lanterns of the same colour scores a bonus of 6 points, counted "
            "once per chain, not once per lantern. The game ends when the bag is empty; "
            "finish the current round so that everyone has had the same number of turns."
        )),
        Section("4", "Edge cases", (
            "Lanternfall edge cases. If you cannot legally place any tile, discard one tile "
            "and lose one wick token instead of taking a turn. If you have no wick tokens "
            "left you may still place tiles but cannot light them. A tie on points is "
            "broken by the most wick tokens remaining; if still tied, the players share "
            "the victory."
        )),
    ),
)

SALTMARSH = Rulebook(
    slug="saltmarsh-couriers",
    title="Saltmarsh Couriers",
    tagline="A card-driven delivery race for 2 to 5 players, about 45 minutes.",
    sections=(
        Section("1", "Setup", (
            "Saltmarsh Couriers setup. Deal 8 route cards to each player. Place 4 parcel "
            "tags face up on the quay, each showing a delivery value from 3 to 9. Put the "
            "storm marker on the first space of the weather track. The oldest player "
            "starts as lead courier."
        )),
        Section("2", "Turn order", (
            "Saltmarsh Couriers turn order. Play passes to the left. On your turn first "
            "draw 2 route cards, then play exactly 1 route card to move your barge along "
            "that route, then you may deliver a parcel if your barge sits on its "
            "destination. After delivering, advance the storm marker one space."
        )),
        Section("3", "Scoring", (
            "Saltmarsh Couriers scoring. Each delivered parcel scores the value printed on "
            "its tag. If the storm marker reaches the last weather space while you hold an "
            "undelivered parcel, you lose 3 points per undelivered parcel. The game ends "
            "after the 10th delivery in total across all players."
        )),
        Section("4", "Edge cases", (
            "Saltmarsh Couriers edge cases. The hand limit is 7 route cards, checked at the "
            "end of your turn: discard down to 7. When the draw deck runs out, shuffle the "
            "discard pile once to make a new deck; if the deck runs out a second time the "
            "game ends immediately. If two couriers could deliver the same parcel, the one "
            "who reached the destination first takes it."
        )),
    ),
)

QUILLFIRE = Rulebook(
    slug="quillfire-duel",
    title="Quillfire Duel",
    tagline="A two-player dice duel between rival wizards, about 20 minutes.",
    sections=(
        Section("1", "Setup", (
            "Quillfire Duel setup. Each wizard starts with 20 ink points and takes 3 spell "
            "dice. Place the 6 glyph tokens in a pool between you. The wizard with the "
            "messier handwriting goes first; if that cannot be settled, roll a die and "
            "the higher roll goes first."
        )),
        Section("2", "Turn order", (
            "Quillfire Duel turn order. Wizards alternate turns. On your turn roll all 3 "
            "spell dice, set aside any you like, and re-roll the rest, up to 2 re-rolls "
            "in total. Then resolve each die: a flame deals 2 ink damage, a feather "
            "restores 1 ink, and a blot does nothing."
        )),
        Section("3", "Scoring", (
            "Quillfire Duel scoring. There are no points: a duel is won by reducing the "
            "opposing wizard's ink to 0. Ink can never rise above its starting 20. If a "
            "turn leaves both wizards at 0 ink at the same time, the duel is a draw and "
            "you play one sudden-death round."
        )),
        Section("4", "Edge cases", (
            "Quillfire Duel edge cases. Rolling three flames is a triple flare: deal 8 "
            "ink damage in place of the usual 6, and you may not re-roll afterwards. A "
            "die that lands off the table is re-rolled without using up a re-roll. A "
            "glyph token may be spent once per duel to turn any one die to a flame."
        )),
    ),
)

RULEBOOKS = (LANTERNFALL, SALTMARSH, QUILLFIRE)
