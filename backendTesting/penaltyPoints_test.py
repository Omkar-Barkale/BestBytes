import datetime
from backend.users.penaltyPoints import PenaltyPoint
from backend.users.user import User


def test_penalty_point_creation():
    user = User("xyz", "xyz@example.com", "pass123")
    reason = "Late submission"

    pp = PenaltyPoint(points=2, user=user, reason=reason)

    # Check values
    assert pp.points == 2
    assert pp.user == user
    assert pp.reason == "Late submission"

    # Check types
    assert isinstance(pp.points, int)
    assert isinstance(pp.user, User)
    assert isinstance(pp.reason, str)


def test_penalty_point_date_is_set():
    user = User("xyz", "xyz@example.com", "pass123")

    before = datetime.datetime.now()
    pp = PenaltyPoint(points=1, user=user, reason="Test reason")
    after = datetime.datetime.now()

    # dateIssued should be between before and after timestamps
    assert before <= pp.dateIssued <= after


def test_penalty_point_multiple_creations_have_different_timestamps():
    user = User("xyz", "xyz@example.com", "pass123")

    pp1 = PenaltyPoint(points=1, user=user, reason="Reason 1")
    pp2 = PenaltyPoint(points=1, user=user, reason="Reason 2")

    assert pp1.dateIssued != pp2.dateIssued
