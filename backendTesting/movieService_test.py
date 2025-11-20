import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from backend.repositories import itemsRepo
from backend.services.moviesService import (
    listMovies,
    getMovieByName,
    createMovie,
    updateMovie,
    deleteMovie,
    addReview,
    searchMovies
)
from backend.schemas.movie import movie, movieCreate, movieUpdate, movieFilter
from backend.schemas.movieReviews import movieReviewsCreate

#pylint: disable = function-naming-style, method-naming-style


def testListMoviesEmpty(tmp_path):
    with patch("backend.services.moviesService.baseDir", tmp_path):
        result = listMovies()
        assert result == []

