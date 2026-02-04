import pytest
from budget_tracker import BudgetTracker, BudgetExceededError

def test_budget_deduction_and_reset():
    tracker = BudgetTracker()
    tracker.reset(1.00)  # start with $1.00

    # deduct $0.30 -> should succeed
    tracker.deduct(0.30)
    assert abs(tracker.remaining - 0.70) < 1e-6

    # deduct $0.70 -> should bring to zero
    tracker.deduct(0.70)
    assert abs(tracker.remaining) < 1e-6

    # any further deduction should raise
    with pytest.raises(BudgetExceededError):
        tracker.deduct(0.01)

    # reset works
    tracker.reset(2.0)
    assert abs(tracker.remaining - 2.0) < 1e-6