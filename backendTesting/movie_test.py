import pytest
from pydantic import ValidationError
from backend.schemas.movie import movie
from backend.schemas.movieReviews import movieReviews

# demo payload
VALID_JOKER = {
    "title": "Joker",
    "movieIMDbRating": 8.4,
    "totalRatingCount": 1213550,
    "totalUserReviews": "11.3K",
    "totalCriticReviews": "697",
    "metaScore": "59",
    "movieGenres": ["Crime", "Drama", "Thriller"],
    "directors": ["Todd Phillips"],
    "datePublished": "2019-10-04",
    "creators": ["Todd Phillips", "Scott Silver", "Bob Kane"],
    "mainStars": ["Joaquin Phoenix", "Robert De Niro", "Zazie Beetz"],
    "description": (
        "A mentally troubled stand-up comedian embarks on a downward spiral "
        "that leads to the creation of an iconic villain."
    ),
    "reviews": []
}

# desc length check
def test_description_too_long():
    data = VALID_JOKER.copy()
    data["description"] = "A" * 501

    with pytest.raises(ValidationError):
        movie(**data)


def test_description_max_length_allowed():
    data = VALID_JOKER.copy()
    data["description"] = "A" * 500

    obj = movie(**data)
    assert len(obj.description) == 500

# genre must be string
def test_invalid_genres_type():
    data = VALID_JOKER.copy()
    data["movieGenres"] = "Crime"  # not a list

    with pytest.raises(ValidationError):
        movie(**data)


def test_genres_list_with_invalid_types():
    data = VALID_JOKER.copy()
    data["movieGenres"] = ["Crime", 123]  # invalid entry

    with pytest.raises(ValidationError):
        movie(**data)

# rating must be a float value
def test_invalid_rating_type():
    data = VALID_JOKER.copy()
    data["movieIMDbRating"] = "notANumber"

    with pytest.raises(ValidationError):
        movie(**data)

# required fields missing
def test_missing_required_field():
    data = VALID_JOKER.copy()
    del data["title"]

    with pytest.raises(ValidationError):
        movie(**data)

# nested review validation
def test_invalid_review_in_list():
    data = VALID_JOKER.copy()
    data["reviews"] = ["NotReviewObject"]  # invalid

    with pytest.raises(ValidationError):
        movie(**data)


def test_valid_nested_review():
    review = movieReviews(
        dateOfReview="2025-02-01",
        user="khushi",
        usefulnessVote=5,
        totalVotes=10,
        userRatingOutOf10=9.0,
        reviewTitle="Amazing!!",
        review="Loved it!"
    )

    data = VALID_JOKER.copy()
    data["reviews"] = [review]

    obj = movie(**data)

    assert len(obj.reviews) == 1
    assert obj.reviews[0].user == "khushi"
    assert obj.reviews[0].userRatingOutOf10 == 9.0

# valid movie object check
def test_valid_joker_movie_schema():
    review = movieReviews(
        dateOfReview="2025-01-01",
        user="khushi",
        usefulnessVote=3,
        totalVotes=5,
        userRatingOutOf10=8.5,
        reviewTitle="Very Good",
        review="Great acting!"
    )

    data = VALID_JOKER.copy()
    data["reviews"] = [review]

    obj = movie(**data)

    assert obj.title == "Joker"
    assert obj.movieIMDbRating == 8.4
    assert isinstance(obj.reviews, list)
    assert obj.reviews[0].reviewTitle == "Very Good"
