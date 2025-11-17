from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter()

user_movie_lists: Dict[str, Dict[str, List[str]]] = {}

# create new list
@router.post("/create")
def create_list(username: str, list_name: str):
    """Create a new movie list for a user."""
    user_movie_lists.setdefault(username.lower(), {})
    if list_name in user_movie_lists[username.lower()]:
        raise HTTPException(status_code=400, detail="List already exists")
    user_movie_lists[username.lower()][list_name] = []
    return {"message": f"List '{list_name}' created for {username}"}

# add movie to list
@router.post("/add")
def add_movie_to_list(username: str, list_name: str, movie_title: str):
    """Add a movie to a user's list."""
    if username.lower() not in user_movie_lists:
        raise HTTPException(status_code=404, detail="User has no lists yet")
    if list_name not in user_movie_lists[username.lower()]:
        raise HTTPException(status_code=404, detail="List not found")

    if movie_title in user_movie_lists[username.lower()][list_name]:
        raise HTTPException(status_code=400, detail="Movie already in list")

    user_movie_lists[username.lower()][list_name].append(movie_title)
    return {"message": f"Added '{movie_title}' to list '{list_name}'"}

# view all lists
@router.get("/{username}")
def view_all_lists(username: str):
    """Return all movie lists for a user."""
    if username.lower() not in user_movie_lists or not user_movie_lists[username.lower()]:
        raise HTTPException(status_code=404, detail="No lists found for this user")
    return user_movie_lists[username.lower()]

# delete movie from list
@router.delete("/remove")
def remove_movie_from_list(username: str, list_name: str, movie_title: str):
    """Remove a movie from a user's list."""
    if username.lower() not in user_movie_lists:
        raise HTTPException(status_code=404, detail="User not found")
    if list_name not in user_movie_lists[username.lower()]:
        raise HTTPException(status_code=404, detail="List not found")
    if movie_title not in user_movie_lists[username.lower()][list_name]:
        raise HTTPException(status_code=404, detail="Movie not in list")

    user_movie_lists[username.lower()][list_name].remove(movie_title)
    return {"message": f"Removed '{movie_title}' from list '{list_name}'"}
