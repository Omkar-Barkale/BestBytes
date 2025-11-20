from pathlib import Path
from typing import Dict, Any, List
import json, csv
import os

# Base directory where all movie folders are stored, ie data file
baseDir = Path(__file__).resolve().parents[1] / "data"

#returns path to movie folder
def getMovieDir(movieName: str) -> Path:
    return baseDir / movieName

#builds the full path to data/<movieName>/metadata.json
def loadMetadata(movieName: str) -> Dict[str, Any]:
    path = getMovieDir(movieName) / "metadata.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
#builds full path to access revies of movies
def loadReviews(movieName: str) -> List[Dict[str, str]]:
    path = getMovieDir(movieName) / "movieReviews.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

#saves movie to files, checks to see if there is a file with the movies name, if not it creates one as well
def saveMetadata(movieName: str, metadata: Dict[str, Any]) -> None:
    path = getMovieDir(movieName) / "metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def saveReviews(movieName: str, reviews: List[Dict[str, str]]) -> None:
    path = getMovieDir(movieName) / "movieReviews.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    if reviews:
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
            writer.writeheader()
            writer.writerows(reviews)
        os.replace(tmp, path)
    elif path.exists():
        path.unlink()



