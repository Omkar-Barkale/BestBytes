from pydantic import BaseModel, Field
from typing import List, Optional
from .movieReviews import movieReviews

class movie(BaseModel):
    title: str
    movieIMDbRating: float
    totalRatingCount: int
    totalUserReviews: str
    totalCriticReviews: str
    metaScore: str
    movieGenres: List[str]
    directors: List[str]
    datePublished: str
    creators: List[str]
    mainStars: List[str]
    description: str = Field(..., max_length=500)
    reviews: List[movieReviews] = []

class movieCreate(BaseModel):
    title: str
    movieIMDbRating: float
    totalRatingCount: int
    totalUserReviews: str
    totalCriticReviews: str
    metaScore: str
    movieGenres: List[str]
    directors: List[str]
    datePublished: str
    creators: List[str]
    mainStars: List[str]
    description: str = Field(..., max_length=500)

class movieUpdate(BaseModel):
    title: str
    movieIMDbRating: float
    totalRatingCount: int
    totalUserReviews: str
    totalCriticReviews: str
    metaScore: str
    movieGenres: List[str]
    directors: List[str]
    datePublished: str
    creators: List[str]
    mainStars: List[str]
    description: str = Field(..., max_length=500)

class movieFilter(BaseModel):
    title: Optional[str] = None
    genres: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    year: Optional[int] = None