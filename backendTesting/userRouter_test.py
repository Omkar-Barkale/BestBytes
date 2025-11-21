import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.routers.userRouter import router
from backend.users.user import User

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_user_db():
    """Reset the in-memory user database before each test."""
    User.usersDb.clear()
    User.activeSessions.clear()


class TestRegisterUser:
    """Tests for POST /register"""

    def test_register_success(self, monkeypatch):
        """A new user registers successfully."""

        class FakeUser:
            def __init__(self):
                self.username = "khushi"
                self.email = "k@gmail.com"
                self.verificationToken = "abc123"

        monkeypatch.setattr(
            "backend.routers.userRouter.User.createAccount",
            lambda *args, **kwargs: FakeUser()
        )

        response = client.post("/register", params={
            "username": "khushi",
            "email": "k@gmail.com",
            "password": "pass123",
        })

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Account created successfully!"
        assert data["username"] == "khushi"
        assert data["email"] == "k@gmail.com"
        assert data["verificationToken"] == "abc123"

    def test_register_user_already_exists(self, monkeypatch):
        """If createAccount raises ValueError -> 400"""

        def fail(*a, **k):
            raise ValueError("User already exists")

        monkeypatch.setattr(
            "backend.routers.userRouter.User.createAccount",
            fail
        )

        response = client.post("/register", params={
            "username": "khushi",
            "email": "k@gmail.com",
            "password": "pass123",
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "User already exists"

    def test_register_invalid_email(self, monkeypatch):
        """If createAccount raises invalid email error -> 400"""

        def fail(*a, **k):
            raise ValueError("Invalid email format")

        monkeypatch.setattr(
            "backend.routers.userRouter.User.createAccount",
            fail
        )

        response = client.post("/register", params={
            "username": "test",
            "email": "bad-email",
            "password": "pass123",
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email format"
