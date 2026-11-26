"""Check the optimizer's winner on held-out reports, then publish it."""


def should_publish(baseline_validation: float, winner_validation: float) -> bool:
    """Only a winner that beats the baseline on reports the optimizer never saw ships."""
    return winner_validation > baseline_validation
