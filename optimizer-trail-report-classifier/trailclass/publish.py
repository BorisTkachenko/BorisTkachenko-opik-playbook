"""Check the optimizer's winner on held-out reports, then publish it."""

# Two reports out of 24; a smaller gap is within the run-to-run wobble of a small set.
MIN_GAIN = 0.08


def should_publish(baseline_text: str, winner_text: str, baseline_validation: float, winner_validation: float) -> bool:
    """Only a different prompt that clearly beats the baseline on unseen reports ships."""
    if winner_text.strip() == baseline_text.strip():
        return False
    return winner_validation - baseline_validation >= MIN_GAIN
