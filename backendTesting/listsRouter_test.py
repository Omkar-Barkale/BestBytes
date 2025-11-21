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
