from fastapi import APIRouter, HTTPException
from typing import Dict, List
from backend.users.user import User

router = APIRouter()

userMovieLists: Dict[str, Dict[str, List[str]]] = {}


# create new list
@router.post("/create")
def createList(username: str, listName: str, sessionToken: str):
    """Create a new movie list for a user."""
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to Create Lists")

    userMovieLists.setdefault(username.lower(), {})
    if listName in userMovieLists[username.lower()]:
        raise HTTPException(status_code=400, detail="List already exists")
    userMovieLists[username.lower()][listName] = []
    return {"message": f"List '{listName}' created for {username}"}

# add movie to list
@router.post("/add")
def addMovieToList(username: str, listName: str, movieTitle: str, sessionToken: str):
    """Add a movie to a user's list."""
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to Add to Lists")

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
def viewAllLists(username: str, sessionToken: str):
    """Return all movie lists for a user."""
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to View Lists")
    if username.lower() not in userMovieLists or not userMovieLists[username.lower()]:
        raise HTTPException(status_code=404, detail="No lists found for this user")
    return userMovieLists[username.lower()]

# delete movie from list
@router.delete("/remove")
def removeMovieFromList(username: str, listName: str, movieTitle: str, sessionToken: str):
    """Remove a movie from a user's list."""
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to Delete Lists")
    if username.lower() not in userMovieLists:
        raise HTTPException(status_code=404, detail="User not found")
    if listName not in userMovieLists[username.lower()]:
        raise HTTPException(status_code=404, detail="List not found")
    if movieTitle not in userMovieLists[username.lower()][listName]:
        raise HTTPException(status_code=404, detail="Movie not in list")

    userMovieLists[username.lower()][listName].remove(movieTitle)
    return {"message": f"Removed '{movieTitle}' from list '{listName}'"}

# delete entire list
@router.delete("/delete")
def deleteList(username: str, listName: str, sessionToken: str):
    """Delete an entire movie list for a user."""
    current_user = User.getCurrentUser(User, sessionToken)
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required to Delete Lists")

    username_key = username.lower()

    if username_key not in userMovieLists:
        raise HTTPException(status_code=404, detail="User not found")

    if listName not in userMovieLists[username_key]:
        raise HTTPException(status_code=404, detail="List not found")

    del userMovieLists[username_key][listName]
    return {"message": f"Deleted list '{listName}' for {username}"}
