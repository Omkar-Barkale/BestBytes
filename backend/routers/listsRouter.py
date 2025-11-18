from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter()

userMovieLists: Dict[str, Dict[str, List[str]]] = {}

# create new list
@router.post("/create")
def createList(username: str, listName: str):
    """Create a new movie list for a user."""
    userMovieLists.setdefault(username.lower(), {})
    if listName in userMovieLists[username.lower()]:
        raise HTTPException(status_code=400, detail="List already exists")
    userMovieLists[username.lower()][listName] = []
    return {"message": f"List '{listName}' created for {username}"}

# add movie to list
@router.post("/add")
def addMovieToList(username: str, listName: str, movieTitle: str):
    """Add a movie to a user's list."""
    if username.lower() not in userMovieLists:
        raise HTTPException(status_code=404, detail="User has no lists yet")
    if listName not in userMovieLists[username.lower()]:
        raise HTTPException(status_code=404, detail="List not found")

    if movieTitle in userMovieLists[username.lower()][listName]:
        raise HTTPException(status_code=400, detail="Movie already in list")

    userMovieLists[username.lower()][listName].append(movieTitle)
    return {"message": f"Added '{movieTitle}' to list '{listName}'"}

# view all lists
@router.get("/{username}")
def viewAllLists(username: str):
    """Return all movie lists for a user."""
    if username.lower() not in userMovieLists or not userMovieLists[username.lower()]:
        raise HTTPException(status_code=404, detail="No lists found for this user")
    return userMovieLists[username.lower()]

# delete movie from list
@router.delete("/remove")
def removeMovieFromList(username: str, listName: str, movieTitle: str):
    """Remove a movie from a user's list."""
    if username.lower() not in userMovieLists:
        raise HTTPException(status_code=404, detail="User not found")
    if listName not in userMovieLists[username.lower()]:
        raise HTTPException(status_code=404, detail="List not found")
    if movieTitle not in userMovieLists[username.lower()][listName]:
        raise HTTPException(status_code=404, detail="Movie not in list")

    userMovieLists[username.lower()][listName].remove(movieTitle)
    return {"message": f"Removed '{movieTitle}' from list '{listName}'"}
