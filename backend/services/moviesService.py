import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from typing import List
from fastapi import HTTPException

from schemas.movie import movie, movieCreate, movieUpdate, movieFilter
from schemas.movieReviews import movieReviews, movieReviewsCreate
from repositories.itemsRepo import loadMetadata, loadReviews, saveMetadata, saveReviews

baseDir = Path(__file__).resolve().parents[1] / "data" # basDir is now pointing to data folder 

#creates a movies list and adds reviews to each 
def listMovies() -> List[movie]:
    if not baseDir.exists(): #checks if data folder exists
        return []
    movies: List[movie] = [] #will hold movie objects
    for movieFolder in baseDir.iterdir(): #returns iterator over all items in data/
        if movieFolder.is_dir():
            metadata = loadMetadata(movieFolder.name)
            reviews = loadReviews(movieFolder.name)
            if metadata:
                movies.append(movie(**metadata, reviews=reviews))
                print(f"Loaded movie: {movieFolder.name} -> {movies[-1]}")
    return movies

def getMovieByName(title: str) -> movie:
    movieDir = baseDir / title #create /data/movie name dir
    if not movieDir.exists(): # checls if movieDir exists
        raise HTTPException(status_code = 404, detail = "Movie {Title} not found")


    metadata = loadMetadata(title)
    reviews = loadReviews(title)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"No metadata for {title}")
    
    return movie(**metadata, reviews = reviews)

def createMovie(payload: movieCreate) -> movie:
    movieDir = baseDir / payload.title #creates path for new movie title
    if movieDir.exists():
        raise HTTPException(status_code=409, detail=f"Movie {payload.title} already exists")
    
    saveMetadata(payload.title, payload.dict()) #creates movie folder if it doesnt exists and metadata.json
    saveReviews(payload.title,[])#creates Moviereviews.csv
    return movie(**payload.dict(), reviews = [])

def updateMovie(title: str, payload: movieUpdate) -> movie:
    """Update an existing movie's metadata."""
    movieDir = baseDir / title
    if not movieDir.exists():
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    saveMetadata(title, payload.dict())
    reviews = loadReviews(title)
    return movie(**payload.dict(), reviews=reviews)


def deleteMovie(title: str) -> None:
    """Delete a movie folder and all its files."""
    movieDir = baseDir / title
    if not movieDir.exists():
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    for file in movieDir.iterdir():
        file.unlink()
    movieDir.rmdir()


def addReview(title: str, payload: movieReviewsCreate) -> movieReviews:
    """Add a review to a movie's CSV file."""
    movieDir = baseDir / title
    if not movieDir.exists():
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    reviews = loadReviews(title)
    newReview = payload.dict()
    reviews.append(newReview)
    saveReviews(title, reviews)
    return movieReviews(**newReview)



def searchMovies(filters: movieFilter) -> List[movie]:
    """Filter movies based on metadata only (ignoring reviews for now)."""
    if not baseDir.exists():
        return []

    results: List[movie] = []

    for movieFolder in baseDir.iterdir():
        if not movieFolder.is_dir(): #iterates through list
            continue

        metadata = loadMetadata(movieFolder.name)
        if not metadata:
            continue

        # Build movie object without reviews
        m = movie(**{k: v for k, v in metadata.items() if k != "reviews"}, reviews=[]) #creates movie object without reviews
        include = True#included in list until proven otherwise

        # --- Title ---
        if filters.title and filters.title.lower() not in m.title.lower():#checks if title exists of if it's a substring
            include = False

        # --- Genres ---
        if getattr(filters, "genres", None):
            if not any(
                g.lower() in [mg.lower() for mg in m.movieGenres] for g in filters.genres #list all movie genres, then check if any filter movie genres match
            ):
                include = False

        # --- Directors ---
        if getattr(filters, "directors", None):
            if not any(
                d.lower() in [md.lower() for md in m.directors] for d in filters.directors
            ):
                include = False

        # --- IMDb Rating ---
        if filters.min_rating is not None and m.movieIMDbRating < filters.min_rating:
            include = False
        if filters.max_rating is not None and m.movieIMDbRating > filters.max_rating:
            include = False

        # --- Year ---
        if filters.year and str(filters.year) not in m.datePublished:
            include = False

        if include:
            results.append(m)

    return results


