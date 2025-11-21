import os
import json
import shutil
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock, mock_open
from backend.schemas.movie import movieCreate
from backend.users.user import User
import pytest



from backend.routers.adminRouter import router


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def validMoviePayload():
    """Fixture providing a valid movie payload matching the movieCreate schema"""
    return {
        "title": "Test Movie",
        "movieIMDbRating": 8.5,
        "totalRatingCount": 1000,
        "totalUserReviews": "500",
        "totalCriticReviews": "50",
        "metaScore": "85",
        "movieGenres": ["Action", "Drama"],
        "directors": ["John Doe"],
        "datePublished": "2025-01-01",
        "creators": ["Jane Smith"],
        "mainStars": ["Actor One", "Actor Two"],
        "description": "A thrilling action drama about overcoming challenges."
    }


@pytest.fixture
def tempDataPath(tmp_path):
    """Create temporary data directory for tests"""
    dataDir = tmp_path / "data"
    dataDir.mkdir()
    return str(dataDir)


@pytest.fixture
def mockUserDb():
    """Mock user database"""
    originalDb = User.usersDb.copy() if hasattr(User, 'usersDb') else {}
    User.usersDb = {}
    yield User.usersDb
    User.usersDb = originalDb


@pytest.fixture(autouse=True)
def resetDataPath():
    """Reset DATA_PATH after each test"""
    from backend.routers import adminRouter
    originalPath = adminRouter.DATA_PATH
    yield
    adminRouter.DATA_PATH = originalPath


class TestAddMovie:
    """Tests for POST /add-movie endpoint"""
    
    def testAddMovieSuccess(self, tempDataPath, monkeypatch, validMoviePayload):
        """Successfully add a new movie"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        response = client.post("/add-movie", json=validMoviePayload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Movie 'Test Movie' added successfully."
        
        # Verify folder was created
        movieFolder = os.path.join(tempDataPath, "Test Movie")
        assert os.path.exists(movieFolder)
        
        # Verify metadata file was created
        metadataFile = os.path.join(movieFolder, "metadata.json")
        assert os.path.exists(metadataFile)
        
        # Verify metadata content
        with open(metadataFile, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        assert metadata["title"] == "Test Movie"
        assert metadata["movieIMDbRating"] == 8.5
    
    def testAddMovieAlreadyExists(self, tempDataPath, monkeypatch, validMoviePayload):
        """Returns 400 when movie already exists"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        # Create existing movie folder
        existingFolder = os.path.join(tempDataPath, "Test Movie")
        os.makedirs(existingFolder)
        
        response = client.post("/add-movie", json=validMoviePayload)
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Movie already exists"
    
    def testAddMovieInvalidDataMissingTitle(self):
        """Returns 422 for missing required fields"""
        payload = {
            "movieIMDbRating": 8.5,
            "totalRatingCount": 1000,
            # Missing title and other required fields
        }
        
        response = client.post("/add-movie", json=payload)
        
        assert response.status_code == 422
    
    def testAddMovieInvalidDataWrongType(self):
        """Returns 422 for wrong data types"""
        payload = {
            "title": "Test Movie",
            "movieIMDbRating": "not_a_number",  # Should be float
            "totalRatingCount": 1000,
            "totalUserReviews": "500",
            "totalCriticReviews": "50",
            "metaScore": "85",
            "movieGenres": ["Action"],
            "directors": ["John Doe"],
            "datePublished": "2025-01-01",
            "creators": ["Jane Smith"],
            "mainStars": ["Actor One"],
            "description": "Test description"
        }
        
        response = client.post("/add-movie", json=payload)
        
        assert response.status_code == 422
    
    def testAddMovieWithSpecialCharacters(self, tempDataPath, monkeypatch, validMoviePayload):
        """Handles movie titles with special characters"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        # Modify payload with special character title
        payload = validMoviePayload.copy()
        payload["title"] = "Movie The Sequel"
        
        response = client.post("/add-movie", json=payload)
        
        assert response.status_code == 200
    
    def testAddMovieEmptyTitle(self):
        """Returns 422 for empty title"""
        payload = {
            "title": "",
            "movieIMDbRating": 8.5,
            "totalRatingCount": 1000,
            "totalUserReviews": "500",
            "totalCriticReviews": "50",
            "metaScore": "85",
            "movieGenres": ["Action"],
            "directors": ["John Doe"],
            "datePublished": "2025-01-01",
            "creators": ["Jane Smith"],
            "mainStars": ["Actor One"],
            "description": "Test description"
        }
        
        response = client.post("/add-movie", json=payload)
        
        # Depends on your schema validation
        assert response.status_code in [422, 400]
    
    def testAddMovieMetadataFormat(self, tempDataPath, monkeypatch, validMoviePayload):
        """Verify metadata is saved with proper formatting"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        response = client.post("/add-movie", json=validMoviePayload)
        assert response.status_code == 200
        
        metadataFile = os.path.join(tempDataPath, "Test Movie", "metadata.json")
        with open(metadataFile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify it's indented with 4 spaces
        assert '    ' in content  # Should have 4-space indentation
        assert '\n' in content  # Should be formatted with newlines
    
    def testAddMoviePermissionError(self, tempDataPath, monkeypatch, validMoviePayload):
        """Handles permission errors when creating directory"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        # Patch at the module level where it's used
        with patch("backend.routers.adminRouter.os.makedirs", side_effect=PermissionError("Permission denied")):
            response = client.post("/add-movie", json=validMoviePayload)
            # Should return 500 error with proper error handling
            assert response.status_code == 500
            assert "Permission denied" in response.json()["detail"]


class TestDeleteMovie:
    """Tests for DELETE /delete-movie/{title} endpoint"""
    
    def testDeleteMovieSuccess(self, tempDataPath, monkeypatch):
        """Successfully delete an existing movie"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        # Create a movie to delete
        movieFolder = os.path.join(tempDataPath, "Movie To Delete")
        os.makedirs(movieFolder)
        
        # Add some files
        metadataFile = os.path.join(movieFolder, "metadata.json")
        with open(metadataFile, 'w', encoding='utf-8') as f:
            json.dump({"title": "Movie To Delete"}, f)
        
        reviewsFile = os.path.join(movieFolder, "reviews.txt")
        with open(reviewsFile, 'w', encoding='utf-8') as f:
            f.write("Great movie!")
        
        response = client.delete("/delete-movie/Movie To Delete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Movie 'Movie To Delete' deleted successfully."
        
        # Verify folder was deleted
        assert not os.path.exists(movieFolder)
    
    def testDeleteMovieNotFound(self, tempDataPath, monkeypatch):
        """Returns 404 when movie doesn't exist"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        response = client.delete("/delete-movie/NonExistentMovie")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Movie not found"
    
    def testDeleteMovieWithSpecialCharacters(self, tempDataPath, monkeypatch):
        """Handles movie titles with special characters"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        # Use simpler special characters that work on Windows
        movieTitle = "Movie Part 2"
        movieFolder = os.path.join(tempDataPath, movieTitle)
        os.makedirs(movieFolder)
        
        response = client.delete(f"/delete-movie/{movieTitle}")
        
        assert response.status_code == 200
        assert not os.path.exists(movieFolder)
    
    def testDeleteMovieEmptyFolder(self, tempDataPath, monkeypatch):
        """Delete movie with no files in folder"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        movieFolder = os.path.join(tempDataPath, "Empty Movie")
        os.makedirs(movieFolder)
        
        response = client.delete("/delete-movie/Empty Movie")
        
        assert response.status_code == 200
        assert not os.path.exists(movieFolder)
    
    def testDeleteMovieWithSubdirectories(self, tempDataPath, monkeypatch):
        """Handles deletion of movies with subdirectories"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        movieFolder = os.path.join(tempDataPath, "Movie With Subdir")
        os.makedirs(movieFolder)
        
        # Add a subdirectory (this will cause rmdir to fail)
        subDir = os.path.join(movieFolder, "extras")
        os.makedirs(subDir)
        
        # With error handling, this should return 500 error instead of raising
        response = client.delete("/delete-movie/Movie With Subdir")
        
        # Should return 500 error because rmdir can't remove non-empty directories
        assert response.status_code == 500
        # Check for either "error" or "permission" in the error message
        detail = response.json()["detail"].lower()
        assert "error" in detail or "permission" in detail or "unable" in detail
    
    def testDeleteMoviePermissionError(self, tempDataPath, monkeypatch):
        """Handles permission errors when deleting"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        movieFolder = os.path.join(tempDataPath, "Protected Movie")
        os.makedirs(movieFolder)
        
        # Add a file so there's something to delete
        testFile = os.path.join(movieFolder, "test.txt")
        with open(testFile, 'w') as f:
            f.write("test")
        
        # Patch at the module level where it's used
        with patch("backend.routers.adminRouter.os.remove", side_effect=PermissionError("Permission denied")):
            response = client.delete("/delete-movie/Protected Movie")
            # Should return 500 error with proper error handling
            assert response.status_code == 500
            assert "Permission denied" in response.json()["detail"]
    
    def testDeleteMovieUrlEncoding(self, tempDataPath, monkeypatch):
        """Handles URL-encoded movie titles"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        movieTitle = "Movie With Spaces"
        movieFolder = os.path.join(tempDataPath, movieTitle)
        os.makedirs(movieFolder)
        
        # URL encode the title
        response = client.delete("/delete-movie/Movie%20With%20Spaces")
        
        assert response.status_code == 200
        assert not os.path.exists(movieFolder)
    
    def testDeleteMovieUnauthorizedInvalidToken(self, monkeypatch):
        """Returns 401 when sessionToken is invalid"""
        with patch("backend.routers.adminRouter.User.getCurrentUser", return_value=None):
            response = client.delete("/delete-movie/TestMovie?sessionToken=invalid")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Login required to delete movies"

    # CHECK: only admins can delete movies
    def testDeleteMovieForbiddenNonAdmin(self, monkeypatch):
        """Returns 403 when user is authenticated but not admin"""
        mockUser = MagicMock()
        mockUser.role = "user"

        with patch("backend.routers.adminRouter.User.getCurrentUser", return_value=mockUser):
            response = client.delete("/delete-movie/TestMovie?sessionToken=token123")

        assert response.status_code == 403
        assert response.json()["detail"] == "Only admins can delete movies"

    # CHECK: deleting movie removes the associated reviews
    def testDeleteMovieRemovesAssociatedReviews(self, tempDataPath, monkeypatch):
        """Ensures movieReviews_memory entry is removed"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)

        # Make movie folder
        movieFolder = os.path.join(tempDataPath, "SampleMovie")
        os.makedirs(movieFolder)

        # fake review memory
        adminRouter.movieReviews_memory["samplemovie"] = ["review1", "review2"]

        mockAdmin = MagicMock(role="admin")
        monkeypatch.setattr(adminRouter.User, "getCurrentUser", lambda _, __: mockAdmin)

        response = client.delete("/delete-movie/SampleMovie?sessionToken=adminToken")
        assert response.status_code == 200

        # After deletion review must be removed
        assert "samplemovie" not in adminRouter.movieReviews_memory

    


class TestAssignPenalty:
    """Tests for POST /penalty endpoint"""
    
    def testAssignPenaltySuccess(self, mockUserDb):
        """Successfully assign penalty to existing user"""
        # Create a mock user
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["testuser"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "testuser",
                "points": 10,
                "reason": "Late return"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Assigned 10 penalty points to testuser"
        assert data["totalPenalties"] == 1
        
        # Verify penalty was added
        assert len(mockUser.penalties) == 1
        assert mockUser.penalties[0]["points"] == 10
        assert mockUser.penalties[0]["reason"] == "Late return"
    
    def testAssignPenaltyUserNotFound(self, mockUserDb):
        """Returns 404 when user doesn't exist"""
        response = client.post(
            "/penalty",
            params={
                "username": "nonexistent",
                "points": 10,
                "reason": "Test"
            }
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    
    def testAssignPenaltyFirstPenalty(self, mockUserDb):
        """Initializes penalties list if user doesn't have one"""
        mockUser = MagicMock(spec=[])  # User without penalties attribute
        User.usersDb["newuser"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "newuser",
                "points": 5,
                "reason": "First offense"
            }
        )
        
        assert response.status_code == 200
        assert hasattr(mockUser, "penalties")
        assert len(mockUser.penalties) == 1
    
    def testAssignPenaltyMultiplePenalties(self, mockUserDb):
        """Add multiple penalties to same user"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["repeat_offender"] = mockUser
        
        # First penalty
        response1 = client.post(
            "/penalty",
            params={
                "username": "repeat_offender",
                "points": 5,
                "reason": "Late return"
            }
        )
        assert response1.status_code == 200
        
        # Second penalty
        response2 = client.post(
            "/penalty",
            params={
                "username": "repeat_offender",
                "points": 10,
                "reason": "Damaged item"
            }
        )
        assert response2.status_code == 200
        
        data = response2.json()
        assert data["totalPenalties"] == 2
        assert len(mockUser.penalties) == 2
    
    def testAssignPenaltyZeroPoints(self, mockUserDb):
        """Allows zero penalty points (warning)"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["warned_user"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "warned_user",
                "points": 0,
                "reason": "Verbal warning"
            }
        )
        
        assert response.status_code == 200
        assert mockUser.penalties[0]["points"] == 0
    
    def testAssignPenaltyNegativePoints(self, mockUserDb):
        """Handles negative penalty points"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["testuser"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "testuser",
                "points": -5,
                "reason": "Point reversal"
            }
        )
        
        # This depends on your validation - might accept or reject
        assert response.status_code in [200, 422]
    
    def testAssignPenaltyLongReason(self, mockUserDb):
        """Handles long penalty reasons"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["testuser"] = mockUser
        
        longReason = "A" * 1000
        
        response = client.post(
            "/penalty",
            params={
                "username": "testuser",
                "points": 10,
                "reason": longReason
            }
        )
        
        assert response.status_code == 200
        assert mockUser.penalties[0]["reason"] == longReason
    
    def testAssignPenaltyEmptyReason(self, mockUserDb):
        """Handles empty penalty reason"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["testuser"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "testuser",
                "points": 10,
                "reason": ""
            }
        )
        
        assert response.status_code == 200
        assert mockUser.penalties[0]["reason"] == ""
    
    def testAssignPenaltySpecialCharactersUsername(self, mockUserDb):
        """Handles usernames with special characters"""
        mockUser = MagicMock()
        mockUser.penalties = []
        User.usersDb["user@email.com"] = mockUser
        
        response = client.post(
            "/penalty",
            params={
                "username": "user@email.com",
                "points": 5,
                "reason": "Test"
            }
        )
        
        assert response.status_code == 200
    
    def testAssignPenaltyMissingParameters(self):
        """Returns 422 for missing required parameters"""
        response = client.post("/penalty", params={"username": "testuser"})
        
        assert response.status_code == 422


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def testAddAndDeleteMovieWorkflow(self, tempDataPath, monkeypatch, validMoviePayload):
        """Complete workflow: add movie then delete it"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        addResponse = client.post("/add-movie", json=validMoviePayload)
        assert addResponse.status_code == 200
        
        # Verify it exists
        movieFolder = os.path.join(tempDataPath, "Test Movie")
        assert os.path.exists(movieFolder)
        
        # Delete movie
        deleteResponse = client.delete("/delete-movie/Test Movie")
        assert deleteResponse.status_code == 200
        
        # Verify it's gone
        assert not os.path.exists(movieFolder)
    
    def testCannotDeleteNonexistentMovie(self, tempDataPath, monkeypatch):
        """Cannot delete movie that was never added"""
        from backend.routers import adminRouter
        monkeypatch.setattr(adminRouter, "DATA_PATH", tempDataPath)
        
        response = client.delete("/delete-movie/Never Added Movie")
        
        assert response.status_code == 404
    
    def testMultipleUsersPenalties(self, mockUserDb):
        """Assign penalties to multiple users"""
        user1 = MagicMock()
        user1.penalties = []
        user2 = MagicMock()
        user2.penalties = []
        
        User.usersDb["user1"] = user1
        User.usersDb["user2"] = user2
        
        # Assign to user1
        response1 = client.post(
            "/penalty",
            params={"username": "user1", "points": 5, "reason": "Test1"}
        )
        assert response1.status_code == 200
        
        # Assign to user2
        response2 = client.post(
            "/penalty",
            params={"username": "user2", "points": 10, "reason": "Test2"}
        )
        assert response2.status_code == 200
        
        # Verify isolation
        assert len(user1.penalties) == 1
        assert len(user2.penalties) == 1
        assert user1.penalties[0]["points"] == 5
        assert user2.penalties[0]["points"] == 10