import uuid
import threading
from datetime import datetime
from backend.schemas.user import user


class admin(user):
    
    #class variables:
    
    # {movie_id: {"title": str, "addedBy": Admin}}
    # {review_id: {"movieId": str, "content": str, "user": User}}
    # {user_id: {"penalty": str, "assignedBy": Admin, "timestamp": datetime}}
    
    moviesDb = {}
    reviewsDb = {}
    penaltiesDb = {}

    #initializing an admin acc
    
    def __init__(self, username: str, email: str, password: str):
        super().__init__(username, email, password)
        
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.role = "admin"
        self.createdAt = datetime.now()
        
    _lock = threading.Lock() # thread safety so only one admin can modify stuff at a time
        
    # admin class features:
    
    # assignPenalty
    def assignPenalty(cls, userId: str, points: int, reason: str, assignedBy: 'admin'):
        with cls._lock:
            if userId not in cls.penaltiesDb:
                cls.penaltiesDb[userId] = []

            cls.penaltiesDb[userId].append({
                "points": points,
                "reason": reason,
                "assignedBy": assignedBy.username,
                "timestamp": datetime.now()
            })
        
            print(
                f"{points} penalty points assigned to {userId} by {assignedBy.username}. "
                f"Reason: {reason}"
            )
            return True

        
    # addMovie
    def addMovie(cls, title: str, addedBy: 'admin'):
        with cls._lock:
            movieId = str(uuid.uuid4())
            cls.moviesDb[movieId] = {
                "title": title,
                "addedBy": addedBy.username,
                "addedAt": datetime.now()
            }
            print(f"The movie '{title}' was added by {addedBy.username}. \nTotal movies: {len(cls.moviesDb)}")
            return movieId


    # removeMovie
    def removeMovie(cls, movieId: str, removedBy: 'admin'):
        with cls._lock:
            if movieId in cls.moviesDb:
                movieTitle = cls.moviesDb[movieId]["title"]
                del cls.moviesDb[movieId]
                print(f"The movie title '{movieTitle}' was deleted by {removedBy.username}.")
                return True
            else:
                print(f"The Movie Id {movieId} was not found.")


    # removeReview
    def removeReview(cls, reviewId: str, deletedBy: 'admin'):
        with cls._lock:
            if reviewId in cls.reviewsDb:
                del cls.reviewsDb[reviewId]
                print(f" The review Id {reviewId} was deleted by {deletedBy.username}.")
                return True
            
            print(f"The review Id {reviewId} was not found.")
            return False


    # viewMovies
    def viewMovies(cls):
        with cls._lock:
            for movieId, details in cls.moviesDb.items():
                print(f"{movieId}: {details['title']} \nThis was added by {details['addedBy']})")

            
    # viewPenalties
    def viewPenalties(cls):
        with cls._lock:
            for userId, details in cls.penaltiesDb.items():
                print(f"User {userId}: {details['penalty']} \nThis penalty was assigned by {details['assignedBy']})")
