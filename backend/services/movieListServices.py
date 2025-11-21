import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from typing import List
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