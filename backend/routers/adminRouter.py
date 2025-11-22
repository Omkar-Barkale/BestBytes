import os
import json
from fastapi import APIRouter, HTTPException
from backend.schemas.movie import movieCreate
from backend.users.user import User

from backend.routers.reviewRouter import router, movieReviews_memory
from backend.schemas.movieReviews import movieReviews

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

# stores user movie lists (for check in deleteMovie)
userMovieLists = {}

# add new movie
@router.post("/add-movie")
def addMovie(movieData: movieCreate):
    """Add a new movie folder and metadata file."""
    folderPath = os.path.join(DATA_PATH, movieData.title)
    if os.path.exists(folderPath):
        raise HTTPException(status_code=400, detail="Movie already exists")

    try:
        os.makedirs(folderPath, exist_ok=True)
        metadataPath = os.path.join(folderPath, "metadata.json")

        with open(metadataPath, "w", encoding="utf-8") as f:
            json.dump(movieData.model_dump(), f, indent=4)

        return {"message": f"Movie '{movieData.title}' added successfully."}
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Unable to create movie folder")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"IO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
# delete movie
@router.delete("/delete-movie/{title}")
def deleteMovie(title: str, sessionToken: str):
    """Delete a movie folder and its metadata file."""
    
    # CHECK: User authentication and admin authorization
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to delete movies")
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete movies")
    
    folderPath = os.path.join(DATA_PATH, title)
    # CHECK: Movie exists
    if not os.path.exists(folderPath):
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
        # CHECK: Delete all files inside movie folder
        for fileName in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, fileName))
        os.rmdir(folderPath)
        
        

        return {"message": f"Movie '{title}' deleted successfully."}
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Unable to delete movie")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Error deleting movie: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# assign penalty to user
@router.post("/penalty")
def assignPenalty(username: str, points: int, reason: str):
    """Assign penalty points to a user."""
    if username not in User.usersDb:
        raise HTTPException(status_code=404, detail="User not found")

    user = User.usersDb[username]

    if not hasattr(user, "penalties"):
        user.penalties = []

    user.penalties.append({"points": points, "reason": reason})
    return {
        "message": f"Assigned {points} penalty points to {username}",
        "totalPenalties": len(user.penalties),
    }