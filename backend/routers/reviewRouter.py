import os
import json
from fastapi import APIRouter, HTTPException
from typing import List
from schemas.movie import movie
from schemas.movieReviews import movieReviews, movieReviewsCreate, movieReviewsUpdate

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

movie_reviews_memory = {}


# helper to get review
def get_reviews_for_movie(title: str) -> List[movieReviews]:
    """Return reviews for a given movie title."""
    return movie_reviews_memory.get(title.lower(), [])


# list all reviews for a movie
@router.get("/{title}/reviews", response_model=List[movieReviews])
def get_all_reviews_for_movie(title: str):
    """Return all reviews for a specific movie."""
    movie_folder = os.path.join(DATA_PATH, title)
    if not os.path.exists(movie_folder):
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    reviews = get_reviews_for_movie(title)
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this movie")
    return reviews


# list all reviews by a user
@router.get("/user/{username}", response_model=List[movieReviews])
def get_reviews_by_user(username: str):
    """Return all reviews written by a specific user across all movies."""
    user_reviews = []
    for reviews in movie_reviews_memory.values():
        for r in reviews:
            if r.user.lower() == username.lower():
                user_reviews.append(r)

    if not user_reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this user")
    return user_reviews


# update review
@router.put("/{title}/review/{index}", response_model=movieReviews)
def update_review(title: str, index: int, updated_data: movieReviewsUpdate):
    """Update an existing review by index for a specific movie."""
    reviews = movie_reviews_memory.get(title.lower(), [])
    if not reviews or index >= len(reviews):
        raise HTTPException(status_code=404, detail="Review not found")

    updated_review = movieReviews(**updated_data.dict())
    reviews[index] = updated_review
    movie_reviews_memory[title.lower()] = reviews
    return updated_review


# delete review
@router.delete("/{title}/review/{index}")
def delete_review(title: str, index: int):
    """Delete a review by index for a specific movie."""
    reviews = movie_reviews_memory.get(title.lower(), [])
    if not reviews or index >= len(reviews):
        raise HTTPException(status_code=404, detail="Review not found")

    removed = reviews.pop(index)
    movie_reviews_memory[title.lower()] = reviews
    return {"message": f"Deleted review '{removed.reviewTitle}' by {removed.user}"}