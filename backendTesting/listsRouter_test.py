import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock

from backend.routers.listsRouter import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_lists():
    """Reset userMovieLists before every test"""
    from backend.routers import listsRouter
    listsRouter.userMovieLists.clear()


@pytest.fixture
def mock_valid_user():
    """Mock a logged-in user"""
    mock_user = MagicMock()
    with patch("backend.users.user.User.getCurrentUser", return_value=mock_user):
        yield mock_user


@pytest.fixture
def mock_invalid_user():
    """Mock an unauthenticated session"""
    with patch("backend.users.user.User.getCurrentUser", return_value=None):
        yield


class TestCreateList:
    """Tests for POST /create endpoint"""

    def test_create_list_success(self, mock_valid_user):
        response = client.post(
            "/create",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "List 'Favorites' created for Khushi"
        }

    def test_create_list_duplicate(self, mock_valid_user):
        client.post("/create", params={
            "username": "Khushi",
            "listName": "Favorites",
            "sessionToken": "abc"
        })

        response = client.post("/create", params={
            "username": "Khushi",
            "listName": "Favorites",
            "sessionToken": "abc"
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "List already exists"

    def test_create_list_new_user_auto_created(self, mock_valid_user):
        response = client.post("/create", params={
            "username": "NewUser",
            "listName": "Watchlist",
            "sessionToken": "abc"
        })

        assert response.status_code == 200

        from backend.routers.listsRouter import userMovieLists
        assert "newuser" in userMovieLists
        assert "Watchlist" in userMovieLists["newuser"]

    def test_create_list_case_insensitive_usernames(self, mock_valid_user):
        client.post("/create", params={
            "username": "KHUSHI",
            "listName": "SciFi",
            "sessionToken": "abc"
        })

        from backend.routers.listsRouter import userMovieLists
        assert "khushi" in userMovieLists
        assert "SciFi" in userMovieLists["khushi"]

    def test_create_list_unauthenticated(self, mock_invalid_user):
        """User must be logged in"""
        response = client.post("/create", params={
            "username": "Khushi",
            "listName": "Favorites",
            "sessionToken": "WRONG"
        })

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to Create Lists"

class TestAddMovieToList:
    """Tests for POST /add endpoint"""

    @pytest.fixture(autouse=True)
    def setup_user_list(self, mock_valid_user):
        """Creates a user and an empty list before each add-movie test"""
        # prepare a valid list owned by user "khushi"
        client.post(
            "/create",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "sessionToken": "abc"
            }
        )

    def test_add_movie_success(self, mock_valid_user):
        """Successfully add the Joker movie to an existing list"""
        joker_title = "Joker"

        response = client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "movieTitle": joker_title,
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Added 'Joker' to list 'Favorites'"}

        from backend.routers.listsRouter import userMovieLists
        assert "Joker" in userMovieLists["khushi"]["Favorites"]

    def test_add_movie_unauthenticated(self, mock_invalid_user):
        """Adding a movie must require login"""
        response = client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "wrong"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to Add to Lists"

    def test_add_movie_user_not_found(self, mock_valid_user):
        """User has no lists yet -> cannot add movie"""
        response = client.post(
            "/add",
            params={
                "username": "unknownUser",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User has no lists yet"

    def test_add_movie_list_not_found(self, mock_valid_user):
        """Trying to add movie to a non-existing list"""
        response = client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "NonExistentList",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "List not found"

    def test_add_movie_duplicate(self, mock_valid_user):
        """Adding the same movie twice should error"""

        # first add succeeds
        client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        # second add should fail
        response = client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Movie already in list"

    def test_add_movie_case_insensitive_user(self, mock_valid_user):
        """Username should be case insensitive when adding movies"""
        response = client.post(
            "/add",
            params={
                "username": "KhUsHi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Added 'Joker' to list 'Favorites'"}

        from backend.routers.listsRouter import userMovieLists
        assert "Joker" in userMovieLists["khushi"]["Favorites"]
