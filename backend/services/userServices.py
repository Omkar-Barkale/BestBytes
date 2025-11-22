import json
from pathlib import Path


USER_DATA_PATH = Path("backend/data/Users/userList.json")

def saveUserToDB(username, email, passwordHash, path: Path):
    """
    Save a single user into usersList.json
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if path.exists():
        try:
            with open(path, 'r') as jsonFile:
                data = json.load(jsonFile)
        except json.JSONDecodeError:
            data = {}

    data[username] = {
        "email": email,
        "password": passwordHash.decode("utf-8"),
        "isVerified": False
    }

    with open(path, 'w') as jsonFile:
        json.dump(data, jsonFile, indent=2)

def changeUserStatus(username:str, status:bool, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if path.exists():
        try:
            with open(path, 'r') as jsonFile:
                data = json.load(jsonFile)
                
        except json.JSONDecodeError:
            data = {}

    if username in data:
        data[username]["isVerified"] = status
        with open(path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=2)


    



def findUserInDB(username, path: Path = Path("backend/data/Users/userList.json")):

    data = {}
    if path.exists():
        try:
            with open(path, "r") as jsonFile:
                data = json.load(jsonFile)
        except json.JSONDecodeError:
            data = {}

    if username in data:
        return data[username]
                    
    raise ValueError(f"User '{username}' does not exist in DB")

def readAllUsers() -> dict:
    """
    Read all users from userList.json and return a dictionary.
    """
    if not USER_DATA_PATH.exists():
        return {}

    try:
        with open(USER_DATA_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}
