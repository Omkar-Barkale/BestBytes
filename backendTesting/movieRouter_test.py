import pytest
import json
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch

from backend.routers.movieRouter import router, load_all_movies

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Example Joker metadata used everywhere in tests
JOKER_METADATA = {
    "title": "Joker",
    "movieIMDbRating": 8.4,
    "totalRatingCount": 1213550,
    "totalUserReviews": "11.3K",
    "totalCriticReviews": "697",
    "metaScore": "59",
    "movieGenres": ["Crime", "Drama", "Thriller"],
    "directors": ["Todd Phillips"],
    "datePublished": "2019-10-04",
    "creators": ["Todd Phillips", "Scott Silver", "Bob Kane"],
    "mainStars": ["Joaquin Phoenix", "Robert De Niro", "Zazie Beetz"],
    "description": "A mentally troubled stand-up comedian embarks on a downward spiral that leads to the creation of an iconic villain.",
    "duration": 122,
    "reviews": []
}


class TestLoadMovies:
    """Tests for load_all_movies() helper + GET / endpoint"""

    def test_load_movies_success(self, tmp_path, monkeypatch):
        """Test loading a valid movie folder with metadata.json"""

        # Create fake directory
        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()

        # Create metadata.json
        metadata_file = movie_dir / "metadata.json"
        metadata_file.write_text(json.dumps(JOKER_METADATA), encoding="utf-8")

        # Patch DATA_PATH in movieRouter
        monkeypatch.setattr(
            "backend.routers.movieRouter.DATA_PATH",
            str(tmp_path)
        )

        movies = load_all_movies()
        assert len(movies) == 1
        assert movies[0].title == "Joker"

    def test_load_movies_multiple(self, tmp_path, monkeypatch):
        """Test loading multiple movies"""
        for name in ["Joker", "Batman", "Inception"]:
            mdir = tmp_path / name
            mdir.mkdir()
            (mdir / "metadata.json").write_text(
                json.dumps({**JOKER_METADATA, "title": name}),
                encoding="utf-8"
            )

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        movies = load_all_movies()
        assert len(movies) == 3
        titles = [m.title for m in movies]
        assert set(titles) == {"Joker", "Batman", "Inception"}

    def test_load_movies_empty_directory(self, tmp_path, monkeypatch):
        """Empty directory -> load_all_movies returns empty list"""

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        movies = load_all_movies()
        assert movies == []

    def test_get_all_movies_success(self, tmp_path, monkeypatch):
        """GET / should return list of movies"""
        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(
            json.dumps(JOKER_METADATA), encoding="utf-8"
        )

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        response = client.get("/")
        assert response.status_code == 200
        assert response.json()[0]["title"] == "Joker"

    def test_get_all_movies_not_found(self, tmp_path, monkeypatch):
        """If no movie folders exist, return 404"""

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        response = client.get("/")
        assert response.status_code == 404
        assert response.json()["detail"] == "No movies found in data directory"

    def test_load_movies_ignore_files_without_metadata(self, tmp_path, monkeypatch):
        """Ignore folders without metadata.json"""

        (tmp_path / "BadFolder").mkdir()  # No metadata.json
        good = tmp_path / "Joker"
        good.mkdir()
        (good / "metadata.json").write_text(
            json.dumps(JOKER_METADATA), encoding="utf-8"
        )

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        movies = load_all_movies()
        assert len(movies) == 1
        assert movies[0].title == "Joker"

class TestGetMovieByTitle:
    """Tests for GET /{title} endpoint"""

    def test_get_movie_success(self, tmp_path, monkeypatch):
        """Retrieve a single movie by title"""

        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(
            json.dumps(JOKER_METADATA), encoding="utf-8"
        )

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        response = client.get("/Joker")
        assert response.status_code == 200
        assert response.json()["title"] == "Joker"

    def test_get_movie_not_found(self, tmp_path, monkeypatch):
        """If movie folder doesn't exist -> 404"""

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        response = client.get("/UnknownMovie")
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie 'UnknownMovie' not found"

    def test_get_movie_includes_reviews_from_memory(self, tmp_path, monkeypatch):
        """If movie_reviews_memory has reviews, they should appear in the response."""

        from backend.routers import movieRouter

        movieRouter.movie_reviews_memory.clear()
        movieRouter.movie_reviews_memory["joker"] = [
            {
                "dateOfReview": "2024-01-01",
                "user": "TestUser",
                "usefulnessVote": 10,
                "totalVotes": 12,
                "userRatingOutOf10": 9,
                "reviewTitle": "Amazing!",
                "review": "Amazing movie!"
            }
        ]


        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(
            json.dumps(JOKER_METADATA), encoding="utf-8"
        )

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        response = client.get("/Joker")
        assert response.status_code == 200
        assert response.json()["reviews"][0]["review"] == "Amazing movie!"

