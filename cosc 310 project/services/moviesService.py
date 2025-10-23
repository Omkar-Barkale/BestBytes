import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import uuid
from typing import List, Dict, Any
from fastapi import HTTPException

from schemas.movie import movie
from schemas.movieReviews import movieReviews  # assuming this is correct
from repositories.itemsRepo import loadMetadata, loadReviews

baseDir = Path(__file__).resolve().parents[1] / "data"

#creates a movies list and adds reviews to each 
def listMovies() -> List[movie]:
    if not baseDir.exists():
        return []
    movies = []
    for movieFolder in baseDir.iterdir():
        if movieFolder.is_dir():
            metadata = loadMetadata(movieFolder.name)
            reviews = loadReviews(movieFolder.name)
            if metadata:
                movies.append(movie(**metadata, reviews=reviews))
                print(f"Loaded movie: {movieFolder.name} -> {movies[-1]}")
    return movies

if __name__ == "__main__":
    listMovies()



