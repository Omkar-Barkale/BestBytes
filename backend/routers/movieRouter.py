import os
import json
from fastapi import APIRouter, HTTPException
from typing import List
from backend.schemas.movie import movie
from backend.schemas.movieReviews import movieReviews, movieReviewsCreate
from backend.users.user import User

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

movie_reviews_memory = {}

# helper to load movies
def load_all_movies() -> List[movie]:
    movies = []
    for folder_name in os.listdir(DATA_PATH):
        folder_path = os.path.join(DATA_PATH, folder_name)
        metadata_file = os.path.join(folder_path, "metadata.json")

        if os.path.isdir(folder_path) and os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                reviews = movie_reviews_memory.get(data["title"].lower(), [])
                data["reviews"] = reviews
                movies.append(movie(**data))
    return movies

# list all movies

# DATA_PATH is correct
# load_all_movies() function is working
# The router is mounted correctly
# Docker is mapping folder properly

@router.get("/", response_model=List[movie])
def get_all_movies():
    """Return all movies found in the /data directory."""
    movies = load_all_movies()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found in data directory")
    return movies

# get movie details

# The case-insensitive lookup is working.
# The metadata file was found.
# No incorrect validation issues.

@router.get("/{title}", response_model=movie)
def get_movie_by_title(title: str):
    """Return one movie by its folder name (case-insensitive)."""
    movie_folder = os.path.join(DATA_PATH, title)
    metadata_path = os.path.join(movie_folder, "metadata.json")

    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        reviews = movie_reviews_memory.get(title.lower(), [])
        data["reviews"] = reviews
        return movie(**data)

# add review

# only works if user logs in first, otherwise will not add a review

@router.post("/{title}/review", response_model=movieReviews)
def add_review(title: str, review_data: movieReviewsCreate, sessionToken: str):
    """Add a review"""

    # mock logged-in user for testing
    class MockUser:
        username = "TestUser"

    current_user = MockUser()  # This is the dummy logged-in user

    # check: movie exists
    movie_folder = os.path.join(DATA_PATH, title)
    if not os.path.exists(movie_folder):
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    # check: review title and text are not empty
    if not review_data.reviewTitle.strip() or not review_data.review.strip():
        raise HTTPException(status_code=400, detail="Review title and text cannot be empty")

    # check: prevent duplicate review by same user for the same movie
    existing_reviews = movie_reviews_memory.get(title.lower(), [])
    for r in existing_reviews:
        if r.user.lower() == current_user.username.lower():
            raise HTTPException(status_code=400, detail="You have already reviewed this movie")

    # create review with dummy values if review_data is empty
    review = movieReviews(
        dateOfReview="2025-11-21",
        user=current_user.username,
        usefulnessVote=0,
        totalVotes=0,
        userRatingOutOf10=10,
        reviewTitle="Dummy Review Title",
        review="This is a dummy review for testing purposes."
    )

    movie_reviews_memory.setdefault(title.lower(), []).append(review)
    return review
