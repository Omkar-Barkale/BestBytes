from pydantic import BaseModel, Field

class movieReviews(BaseModel):
    dateOfReview: str
    user: str
    usefulnessVote: int
    totalVotes: int
    userRatingOutOf10: float = Field(..., ge = 0, le =  10)
    reviewTitle: str = Field(..., max_length = 200)
    review: str = Field(..., max_length = 5000)

class movieReviewsCreate(BaseModel):
    dateOfReview: str
    user: str
    usefulnessVote: int
    totalVotes: int
    userRatingOutOf10: float = Field(..., ge = 0, le =  10)
    reviewTitle: str = Field(..., max_length = 200)
    review: str = Field(..., max_length = 5000)

class movieReviewsUpdate(BaseModel):
    dateOfReview: str
    user: str
    usefulnessVote: int
    totalVotes: int
    userRatingOutOf10: float = Field(..., ge = 0, le =  10)
    reviewTitle: str = Field(..., max_length = 200)
    review: str = Field(..., max_length = 5000)
