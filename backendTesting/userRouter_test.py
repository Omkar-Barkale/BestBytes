import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch


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

class TestVerifyEmail:
    """Tests for POST /verify"""

    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Reset and preload a fake user before each test."""
        User.usersDb.clear()


        class DummyUser:
            def __init__(self):
                self.username = "khushi"
                self.email = "k@gmail.com"
                self.isVerified = False

            def verifyEmail(self, token):
                return token == "correct-token"


        User.usersDb["khushi"] = DummyUser()

    def test_verify_success(self):
        """Verification works with correct token -> 200"""

        response = client.post("/verify", params={
            "username": "khushi",
            "token": "correct-token",
        })

        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully!"

    def test_verify_user_not_found(self):
        """Unknown username -> 404"""

        response = client.post("/verify", params={
            "username": "unknown",
            "token": "whatever",
        })

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_verify_invalid_token(self):
        """Wrong token -> 400"""

        response = client.post("/verify", params={
            "username": "khushi",
            "token": "wrong-token",
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid verification token"

class TestLoginUser:
    """Tests for POST /login"""

    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Reset DB and add one valid user with predictable login behavior."""
        User.usersDb.clear()

        class DummyUser:
            def __init__(self):
                self.username = "khushi"
                self.email = "k@gmail.com"
                self.password = "pass123"
                self.isVerified = True

        dummy = DummyUser()
        User.usersDb["khushi"] = dummy

        def fake_login(cls, username, password):
            if username != "khushi" or password != "pass123":
                raise ValueError("Invalid credentials")
            return "session-123"

        self.login_patch = patch("backend.users.user.User.login", fake_login)
        self.login_patch.start()

        yield
        self.login_patch.stop()

    def test_login_success(self):
        """Valid username + password -> 200 + return token"""

        response = client.post("/login", params={
            "username": "khushi",
            "password": "pass123"
        })

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Login successful!"
        assert body["sessionToken"] == "session-123"

    def test_login_invalid_credentials(self):
        """Wrong password -> 400"""

        response = client.post("/login", params={
            "username": "khushi",
            "password": "wrong"
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_unknown_user(self):
        """Unknown username -> 400 with error from User.login"""

        response = client.post("/login", params={
            "username": "doesnotexist",
            "password": "whatever"
        })

        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

class TestLogoutUser:
    """Tests for POST /logout"""

    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Reset DB and mock logout behavior for predictable results."""
        User.usersDb.clear()

        class DummyUser:
            def __init__(self):
                self.username = "khushi"
                self.email = "k@gmail.com"
                self.sessionToken = "valid-token"

        self.dummy = DummyUser()

        def fake_logout(cls, token):
            return token == "valid-token"

        self.logout_patch = patch("backend.users.user.User.logout", fake_logout)
        self.logout_patch.start()

        yield
        self.logout_patch.stop()

    def test_logout_success(self):
        """Valid session token -> success"""
        response = client.post("/logout?sessionToken=valid-token")
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful!"

    def test_logout_invalid_token(self):
        """Invalid token -> 400"""
        response = client.post("/logout?sessionToken=wrong")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid or expired session token"

    def test_logout_missing_token(self):
        """Missing sessionToken entirely -> 422"""
        response = client.post("/logout")
        assert response.status_code == 422

class TestGetCurrentUser:
    """Tests for GET /me"""

    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Prepare a mock user and mock getCurrentUser method."""
        User.usersDb.clear()

        class DummyUser:
            def __init__(self):
                self.username = "khushi"
                self.email = "k@gmail.com"
                self.isVerified = True
                self.createdAt = "2024-01-01"
                self.lastLogin = "2024-01-02"

        self.dummy = DummyUser()

        def fake_get_current_user(cls, token):
            return self.dummy if token == "valid-token" else None

        self.patch = patch("backend.users.user.User.getCurrentUser", fake_get_current_user)
        self.patch.start()

        yield
        self.patch.stop()

    def test_get_current_user_success(self):
        """Valid token -> returns user details"""
        response = client.get("/me?sessionToken=valid-token")
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "khushi"
        assert data["email"] == "k@gmail.com"
        assert data["verified"] is True
        assert data["createdAt"] == "2024-01-01"
        assert data["lastLogin"] == "2024-01-02"

    def test_get_current_user_invalid_token(self):
        """Invalid token -> 401"""
        response = client.get("/me?sessionToken=bad-token")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired session token"

    def test_get_current_user_missing_token(self):
        """Missing query parameter -> FastAPI returns 422"""
        response = client.get("/me")
        assert response.status_code == 422
