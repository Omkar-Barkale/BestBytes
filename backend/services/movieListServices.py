import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from typing import List, Dict
from fastapi import HTTPException
import json

from schemas.movie import movie

def saveMovieList(list : List[movie], user: str, listName: str, path: Path):
    data = {}
    path.mkdir(parents= True, exist_ok= True)
    path = path/"movieLists.json"

    if path.exists():
        with open(path,'r+') as jsonFile:
            try:
                data = json.load(jsonFile)
            except json.JSONDecodeError:
                 data = {}
            jsonFile.close()
    
    if user not in data:
        data[user] = {}

    data[user][listName] = list

    with open(path, 'w') as jsonFile:
        json.dump(data,jsonFile)
        jsonFile.close()

def saveAllUsers(users: Dict[str, Dict], path: Path):
    """Save all users to user.json."""
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "user.json"

    with open(file_path, "w") as f:
        json.dump(users, f, indent=4)


def readAllUsers(path: Path) -> Dict[str, Dict]:
    """Read all users from user.json and return as a dict."""
    data = {}
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "user.json"

    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    return data

