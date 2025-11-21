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

class TestViewAllLists:
    """Tests for GET /{username} endpoint"""

    @pytest.fixture(autouse=True)
    def setup_lists(self, mock_valid_user):
        """Create two lists for user khushi"""
        client.post(
            "/create",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "sessionToken": "abc"
            }
        )
        client.post(
            "/create",
            params={
                "username": "Khushi",
                "listName": "Watchlist",
                "sessionToken": "abc"
            }
        )

    def test_view_all_lists_success(self, mock_valid_user):
        """View all lists successfully"""
        response = client.get(
            "/khushi",
            params={"sessionToken": "abc"}
        )

        assert response.status_code == 200
        body = response.json()

        # both lists should exist and be empty arrays
        assert "Favorites" in body
        assert "Watchlist" in body
        assert body["Favorites"] == []
        assert body["Watchlist"] == []

    def test_view_lists_unauthenticated(self, mock_invalid_user):
        """User must be logged in to view lists"""
        response = client.get(
            "/khushi",
            params={"sessionToken": "wrong"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to View Lists"

    def test_view_lists_user_not_found(self, mock_valid_user):
        """User does not exist or has no lists"""
        response = client.get(
            "/unknownuser",
            params={"sessionToken": "abc"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No lists found for this user"

    def test_view_lists_case_insensitive(self, mock_valid_user):
        """Usernames must be case-insensitive"""
        response = client.get(
            "/KhUsHi",
            params={"sessionToken": "abc"}
        )

        assert response.status_code == 200
        body = response.json()
        assert "Favorites" in body
        assert "Watchlist" in body

    def test_view_lists_when_user_has_zero_lists(self, mock_valid_user):
        """If user exists but has zero lists, return 404"""

        from backend.routers.listsRouter import userMovieLists
        userMovieLists["khushi"].clear()

        response = client.get(
            "/khushi",
            params={"sessionToken": "abc"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No lists found for this user"

class TestRemoveMovieFromList:
    """Tests for DELETE /remove endpoint"""

    @pytest.fixture(autouse=True)
    def setup_user_list_with_movie(self, mock_valid_user):
        """Create user, list, and insert Joker movie before each test"""

        # creates list
        client.post(
            "/create",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "sessionToken": "abc"
            }
        )

        # adds Joker to list
        client.post(
            "/add",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

    def test_remove_movie_success(self, mock_valid_user):
        """Successfully remove a movie from the list"""
        response = client.delete(
            "/remove",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Removed 'Joker' from list 'Favorites'"}

        from backend.routers.listsRouter import userMovieLists
        assert "Joker" not in userMovieLists["khushi"]["Favorites"]

    def test_remove_movie_unauthenticated(self, mock_invalid_user):
        """Removing a movie must require login"""
        response = client.delete(
            "/remove",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "wrong"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to Delete Lists"

    def test_remove_movie_user_not_found(self, mock_valid_user):
        """If the user does not exist"""
        response = client.delete(
            "/remove",
            params={
                "username": "UnknownUser",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_remove_movie_list_not_found(self, mock_valid_user):
        """If list does not exist"""
        response = client.delete(
            "/remove",
            params={
                "username": "Khushi",
                "listName": "NotAList",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "List not found"

    def test_remove_movie_not_in_list(self, mock_valid_user):
        """Trying to remove a movie that does not exist in the list"""

        # makes the list empty
        client.delete(
            "/remove",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        # removes
        response = client.delete(
            "/remove",
            params={
                "username": "Khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not in list"

    def test_remove_movie_case_insensitive_user(self, mock_valid_user):
        """Usernames should be case-insensitive when deleting movies"""

        # readds movie
        client.post(
            "/add",
            params={
                "username": "khushi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        response = client.delete(
            "/remove",
            params={
                "username": "KhUsHi",
                "listName": "Favorites",
                "movieTitle": "Joker",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Removed 'Joker' from list 'Favorites'"}

        from backend.routers.listsRouter import userMovieLists
        assert "Joker" not in userMovieLists["khushi"]["Favorites"]

# deletes the entire list
class TestDeleteList:
    """Tests for DELETE /delete endpoint"""

    @pytest.fixture(autouse=True)
    def setup_lists(self, mock_valid_user):
        # create user + 2 lists
        client.post("/create", params={
            "username": "khushi",
            "listName": "Fav",
            "sessionToken": "abc"
        })
        client.post("/create", params={
            "username": "khushi",
            "listName": "Watch",
            "sessionToken": "abc"
        })

    def test_delete_list_success(self, mock_valid_user):
        response = client.delete(
            "/delete",
            params={
                "username": "khushi",
                "listName": "Fav",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Deleted list 'Fav' for khushi"}

        from backend.routers.listsRouter import userMovieLists
        assert "Fav" not in userMovieLists["khushi"]

    def test_delete_list_not_found(self, mock_valid_user):
        response = client.delete(
            "/delete",
            params={
                "username": "khushi",
                "listName": "DoesNotExist",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "List not found"

    def test_delete_user_not_found(self, mock_valid_user):
        response = client.delete(
            "/delete",
            params={
                "username": "unknownUser",
                "listName": "Fav",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_delete_list_unauthenticated(self, mock_invalid_user):
        response = client.delete(
            "/delete",
            params={
                "username": "khushi",
                "listName": "Fav",
                "sessionToken": "wrong"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to Delete Lists"

    def test_delete_list_case_insensitive(self, mock_valid_user):
        response = client.delete(
            "/delete",
            params={
                "username": "KhUsHi",
                "listName": "Watch",
                "sessionToken": "abc"
            }
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Deleted list 'Watch' for KhUsHi"}

        from backend.routers.listsRouter import userMovieLists
        assert "Watch" not in userMovieLists["khushi"]

