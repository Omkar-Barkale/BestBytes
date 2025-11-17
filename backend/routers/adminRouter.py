import os
import json
from fastapi import APIRouter, HTTPException
from schemas.movie import movieCreate
from users.user import User

router = APIRouter()

# load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

# add new movie
@router.post("/add-movie")
def add_movie(movie_data: movieCreate):
    """Add a new movie folder and metadata file."""
    folder_path = os.path.join(DATA_PATH, movie_data.title)
    if os.path.exists(folder_path):
        raise HTTPException(status_code=400, detail="Movie already exists")

    os.makedirs(folder_path, exist_ok=True)
    metadata_path = os.path.join(folder_path, "metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(movie_data.dict(), f, indent=4)

    return {"message": f"Movie '{movie_data.title}' added successfully."}

# delete movie
@router.delete("/delete-movie/{title}")
def delete_movie(title: str):
    """Delete a movie folder and its metadata file."""
    folder_path = os.path.join(DATA_PATH, title)
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Movie not found")

    for file_name in os.listdir(folder_path):
        os.remove(os.path.join(folder_path, file_name))
    os.rmdir(folder_path)

    return {"message": f"Movie '{title}' deleted successfully."}

# assign penalty to user
@router.post("/penalty")
def assign_penalty(username: str, points: int, reason: str):
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