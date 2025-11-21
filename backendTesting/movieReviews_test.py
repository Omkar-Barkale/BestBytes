import pytest
from pydantic import ValidationError
from backend.schemas.movieReviews import movieReviews


# valid payload
VALID_REVIEW = {
    "dateOfReview": "2025-01-01",
    "user": "khushi",
    "usefulnessVote": 5,
    "totalVotes": 10,
    "userRatingOutOf10": 8.5,
    "reviewTitle": "Great movie!",
    "review": "Loved every scene."
}

# rating tests

def test_rating_below_zero():
    data = VALID_REVIEW.copy()
    data["userRatingOutOf10"] = -1
    with pytest.raises(ValidationError):
        movieReviews(**data)


def test_rating_above_ten():
    data = VALID_REVIEW.copy()
    data["userRatingOutOf10"] = 10.1
    with pytest.raises(ValidationError):
        movieReviews(**data)


def test_rating_not_number():
    data = VALID_REVIEW.copy()
    data["userRatingOutOf10"] = "invalid"
    with pytest.raises(ValidationError):
        movieReviews(**data)

# title tests

def test_review_title_too_long():
    data = VALID_REVIEW.copy()
    data["reviewTitle"] = "A" * 201   # 201 characters
    with pytest.raises(ValidationError):
        movieReviews(**data)


def test_review_title_max_length_allowed():
    data = VALID_REVIEW.copy()
    data["reviewTitle"] = "A" * 200
    obj = movieReviews(**data)
    assert obj.reviewTitle == data["reviewTitle"]


# review tests

def test_review_body_too_long():
    data = VALID_REVIEW.copy()
    data["review"] = "A" * 5001
    with pytest.raises(ValidationError):
        movieReviews(**data)


def test_review_body_max_length():
    data = VALID_REVIEW.copy()
    data["review"] = "A" * 5000
    obj = movieReviews(**data)
    assert obj.review == data["review"]


# valid obj test

def test_valid_review_object():
    obj = movieReviews(**VALID_REVIEW)
    assert obj.user == "khushi"
    assert obj.userRatingOutOf10 == 8.5
    assert obj.reviewTitle == "Great movie!"
