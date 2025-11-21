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
DUMMY_REVIEW = {
    "dateOfReview": "2024-01-01",
    "user": "X",
    "usefulnessVote": 0,
    "totalVotes": 0,
    "userRatingOutOf10": 5,
    "reviewTitle": "Test",
    "review": "Test"
}

class TestAddReview:
    """Tests for POST /{title}/review endpoint"""

    def test_add_review_success(self, tmp_path, monkeypatch):
        """Valid user + valid movie folder -> review saved"""
        from backend.routers import movieRouter
        movieRouter.movie_reviews_memory.clear()

        # create dir with data
        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(json.dumps(JOKER_METADATA), encoding="utf-8")

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        review_payload = {
            "dateOfReview": "2024-01-01",
            "user": "Khushi",
            "usefulnessVote": 3,
            "totalVotes": 5,
            "userRatingOutOf10": 9,
            "reviewTitle": "Great!",
            "review": "Amazing movie!"
        }

        with patch("backend.routers.movieRouter.User.getCurrentUser", return_value={"username": "Khushi"}):
            response = client.post("/Joker/review?sessionToken=abc", json=review_payload)

        assert response.status_code == 200
        assert response.json()["review"] == "Amazing movie!"

    def test_add_review_unauthenticated(self, tmp_path, monkeypatch):
        """If user is not logged in -> 401 BEFORE validating payload"""

        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(json.dumps(JOKER_METADATA), encoding="utf-8")

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        dummy_payload = {
            "dateOfReview": "2024-01-01",
            "user": "X",
            "usefulnessVote": 0,
            "totalVotes": 0,
            "userRatingOutOf10": 5,
            "reviewTitle": "Test",
            "review": "Test"
        }

        with patch("backend.routers.movieRouter.User.getCurrentUser", return_value=None):
            response = client.post("/Joker/review?sessionToken=bad", json=dummy_payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to review"

    def test_add_review_movie_not_found(self, tmp_path, monkeypatch):
        """If movie folder does not exist -> 404 BEFORE validating payload"""

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        payload = {
            "dateOfReview": "2024-01-01",
            "user": "Khushi",
            "usefulnessVote": 1,
            "totalVotes": 2,
            "userRatingOutOf10": 7,
            "reviewTitle": "Nice",
            "review": "Good"
        }

        with patch("backend.routers.movieRouter.User.getCurrentUser", return_value={"username": "Khushi"}):
            response = client.post("/UnknownMovie/review?sessionToken=abc", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Movie 'UnknownMovie' not found"

    def test_add_review_saved_in_memory(self, tmp_path, monkeypatch):
        """Review should be stored in movie_reviews_memory under lowercase key"""

        from backend.routers import movieRouter
        movieRouter.movie_reviews_memory.clear()

        movie_dir = tmp_path / "Joker"
        movie_dir.mkdir()
        (movie_dir / "metadata.json").write_text(json.dumps(JOKER_METADATA), encoding="utf-8")

        monkeypatch.setattr("backend.routers.movieRouter.DATA_PATH", str(tmp_path))

        review_payload = {
            "dateOfReview": "2024-01-01",
            "user": "Khushi",
            "usefulnessVote": 10,
            "totalVotes": 12,
            "userRatingOutOf10": 8,
            "reviewTitle": "Nice",
            "review": "Good film"
        }

        with patch("backend.routers.movieRouter.User.getCurrentUser", return_value={"username": "Khushi"}):
            response = client.post("/Joker/review?sessionToken=abc", json=review_payload)

        assert response.status_code == 200
        assert len(movieRouter.movie_reviews_memory["joker"]) == 1
        assert movieRouter.movie_reviews_memory["joker"][0].review == "Good film"
