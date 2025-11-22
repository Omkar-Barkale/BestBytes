import os
import json
from fastapi import APIRouter, HTTPException
from backend.schemas.movie import movieCreate
from backend.users.user import User

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

# add new movie

# - Adds a new movie folder under DATA_PATH and creates a metadata.json file.
# - Returns 400 if the movie already exists.
# - Returns 500 for permission issues or unexpected IO errors.
# - In Swagger, provide all required movie fields in JSON.

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

# - Deletes the movie folder and its metadata.json file.
# - Returns 404 if the folder does not exist.
# - Returns 500 for permission issues or OS errors during deletion.
# - Be careful: deletes all files inside the folder before removing it.
# - Swagger: Just input the movie title in the path.

@router.delete("/delete-movie/{title}")
def deleteMovie(title: str):
    """Delete a movie folder and its metadata file."""
    folderPath = os.path.join(DATA_PATH, title)
    if not os.path.exists(folderPath):
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
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

# - Assigns penalty points to a user.
# - Returns 404 if the user does not exist.
# - Each user has a 'penalties' list; new penalties are appended.
# - Returns 500 if the internal logic fails (e.g., User.usersDb not set properly).
# - Swagger requires query params:
#     - username (string)
#     - points (integer)
#     - reason (string)
# - Example URL: /admin/penalty?username=khushi&points=2&reason=hate%20speech
# - Make sure the user exists in User.usersDb before testing.

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