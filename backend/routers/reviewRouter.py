import os
import json
from fastapi import APIRouter, HTTPException
from typing import List
from schemas.movie import movie
from schemas.movieReviews import movieReviews,movieReviewsCreate ,movieReviewsUpdate

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

movieReviews_memory = {}


# helper to get review
def getReviewsForMovie(title: str) -> List[movieReviews]:
    """Return reviews for a given movie title."""
    return movieReviews_memory.get(title.lower(), [])


# list all reviews for a movie
@router.get("/{title}/reviews", response_model=List[movieReviews])
def getAllReviewsForMovie(title: str):
    """Return all reviews for a specific movie."""
    movie_folder = os.path.join(DATA_PATH, title)
    if not os.path.exists(movie_folder):
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    reviews = getReviewsForMovie(title)
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this movie")
    return reviews


# list all reviews by a user
@router.get("/user/{username}", response_model=List[movieReviews])
def getReviewsByUser(username: str):
    """Return all reviews written by a specific user across all movies."""
    userReviews = []
    for reviews in movieReviews_memory.values():
        for r in reviews:
            if r.user.lower() == username.lower():
                userReviews.append(r)

    if not userReviews:
        raise HTTPException(status_code=404, detail="No reviews found for this user")
    return userReviews


# update review
@router.put("/{title}/review/{index}", response_model=movieReviews)
def updateReview(title: str, index: int, updated_data: movieReviewsUpdate):
    """Update an existing review by index for a specific movie."""
    reviews = movieReviews_memory.get(title.lower(), [])
    if not reviews or index >= len(reviews):
        raise HTTPException(status_code=404, detail="Review not found")

    updatedReview = movieReviews(**updated_data.dict())
    reviews[index] = updatedReview
    movieReviews_memory[title.lower()] = reviews
    return updatedReview


# delete review
@router.delete("/{title}/review/{index}")
def deleteReview(title: str, index: int):
    """Delete a review by index for a specific movie."""
    reviews = movieReviews_memory.get(title.lower(), [])
    if not reviews or index >= len(reviews):
        raise HTTPException(status_code=404, detail="Review not found")

    removed = reviews.pop(index)
    movieReviews_memory[title.lower()] = reviews
    return {"message": f"Deleted review '{removed.reviewTitle}' by {removed.user}"}