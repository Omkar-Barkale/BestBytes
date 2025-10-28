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

#pylint: disable = W0105
""" just prints movies and reviews to file to ensure other methods work, careful the review files are very large
def printAllMovies():
    if not baseDir.exists():
        print("No movies found.")
        return

def printAllMovies():
    if not baseDir.exists():
        print("No movies found.")
        return

    for movieFolder in baseDir.iterdir():
        if movieFolder.is_dir():
            movieName = movieFolder.name
            print(f"\n🎬 Movie: {movieName}")

            metadata = loadMetadata(movieName)
            if metadata:
                print("📄 Metadata:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
            else:
                print("📄 Metadata: Not found")

            reviews = loadReviews(movieName)
            if reviews:
                print("📝 Reviews:")
                for review in reviews:
                    user = review.get("User", "Unknown")
                    rating = review.get("User's Rating out of 10", "-")
                    title = review.get("Review Title", "").strip()
                    body = review.get("Review", "").strip()
                    
                    print(f"\n  🧑 User: {user}")
                    print(f"  ⭐ Rating: {rating}/10")
                    if title:
                        print(f"  📌 Title: {title}")
                    print(f"  🗒️ Review: {body[:300]}{'...' if len(body) > 300 else ''}")
            else:
                print("📝 Reviews: None")

if __name__ == "__main__":
    printAllMovies()
"""
