import uuid
import threading
from datetime import datetime
from typing import Optional

class admin:
    
    #fcn assignPenalty
    
    # {movie_id: {"title": str, "addedBy": Admin}}
    # {review_id: {"movieId": str, "content": str, "user": User}}
    # {user_id: {"penalty": str, "assignedBy": Admin, "timestamp": datetime}}
    
    moviesDb = {}
    reviewsDb = {}
    penaltiesDb = {}

    #initializing an admin acc
    
    def __init__(self, username: str, email: str):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.role = "admin"
        self.createdAt = datetime.now()
        
    # admin class features:
    
    # addMovie
    def addMovie():
        return
    
    # removeMovie
    def removeMovie():
        return
        
    
    # removeReview
    def removeReview():
        return
    
    # viewMovies
    def viewMovies():
        return
    