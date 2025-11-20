import pytest
from pathlib import Path
from fastapi import HTTPException
from unittest.mock import Mock, patch, MagicMock
import sys

# Adjust import path as needed - import the actual module
import backend.services.moviesService as movieServices
from backend.services.moviesService import (
    listMovies,
    getMovieByName,
    createMovie,
    updateMovie,
    deleteMovie,
    addReview,
    searchMovies
)
from backend.schemas.movie import movieCreate, movieUpdate, movieFilter
from backend.schemas.movieReviews import movieReviewsCreate


# Fixtures
@pytest.fixture
def sampleMetadata():
    """Sample movie metadata - includes all required fields"""
    return {
        "title": "Inception",
        "movieGenres": ["Action", "Sci-Fi"],
        "directors": ["Christopher Nolan"],
        "movieIMDbRating": 8.8,
        "datePublished": "2010-07-16",
        "totalRatingCount": 1000,
        "totalUserReviews": "500",
        "totalCriticReviews": "50",
        "metaScore": "85",
        "creators": ["Christopher Nolan"],
        "mainStars": ["Leonardo DiCaprio", "Tom Hardy"],
        "description": "A thief who steals corporate secrets"
    }


@pytest.fixture
def sampleReviews():
    """Sample movie reviews - includes all required fields"""
    return [
        {
            "reviewer": "John",
            "rating": 9,
            "comment": "Great movie!",
            "dateOfReview": "2010-08-01",
            "user": "john123",
            "usefulnessVote": 10,
            "totalVotes": 12,
            "userRatingOutOf10": 9,
            "reviewTitle": "Amazing!",
            "review": "Great movie!"
        },
        {
            "reviewer": "Jane",
            "rating": 8,
            "comment": "Loved it",
            "dateOfReview": "2010-08-02",
            "user": "jane456",
            "usefulnessVote": 8,
            "totalVotes": 10,
            "userRatingOutOf10": 8,
            "reviewTitle": "Really good",
            "review": "Loved it"
        }
    ]


@pytest.fixture
def mockBaseDir(tmp_path):
    """Create a temporary base directory for tests"""
    return tmp_path / "data"


# Tests for listMovies()
class TestListMovies:
    
    def testListMoviesEmptyDirectory(self, mockBaseDir):
        """Test listing movies when data directory doesn't exist"""
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            result = listMovies()
            assert result == []
    
    def testListMoviesWithData(self, mockBaseDir, sampleMetadata, sampleReviews):
        """Test listing movies with valid data"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata), \
             patch.object(movieServices, 'loadReviews', return_value=sampleReviews):
            
            result = listMovies()
            assert len(result) == 1
            assert result[0].title == "Inception"
            assert len(result[0].reviews) == 2
    
    def testListMoviesSkipsFiles(self, mockBaseDir):
        """Test that listMovies skips non-directory items"""
        mockBaseDir.mkdir(parents=True)
        (mockBaseDir / "file.txt").touch()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            result = listMovies()
            assert result == []
    
    def testListMoviesSkipsInvalidMetadata(self, mockBaseDir):
        """Test that movies without metadata are skipped"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "InvalidMovie"
        movieDir.mkdir()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=None):
            
            result = listMovies()
            assert result == []


# Tests for getMovieByName()
class TestGetMovieByName:
    
    def testGetMovieSuccess(self, mockBaseDir, sampleMetadata, sampleReviews):
        """Test successfully retrieving a movie"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata), \
             patch.object(movieServices, 'loadReviews', return_value=sampleReviews):
            
            result = getMovieByName("Inception")
            assert result.title == "Inception"
            assert len(result.reviews) == 2
    
    def testGetMovieNotFound(self, mockBaseDir):
        """Test getting a non-existent movie"""
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            with pytest.raises(HTTPException) as excInfo:
                getMovieByName("NonExistent")
            assert excInfo.value.status_code == 404
    
    def testGetMovieNoMetadata(self, mockBaseDir):
        """Test getting a movie without metadata"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=None):
            
            with pytest.raises(HTTPException) as excInfo:
                getMovieByName("Inception")
            assert excInfo.value.status_code == 404


# Tests for createMovie()
class TestCreateMovie:
    
    def testCreateMovieSuccess(self, mockBaseDir):
        """Test successfully creating a new movie"""
        payload = movieCreate(
            title="Inception",
            movieGenres=["Action", "Sci-Fi"],
            directors=["Christopher Nolan"],
            movieIMDbRating=8.8,
            datePublished="2010-07-16",
            totalRatingCount=1000,
            totalUserReviews="500",
            totalCriticReviews="50",
            metaScore="85",
            creators=["Christopher Nolan"],
            mainStars=["Leonardo DiCaprio"],
            description="A thief who steals secrets"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'saveMetadata') as mockSaveMeta, \
             patch.object(movieServices, 'saveReviews') as mockSaveReviews:
            
            mockBaseDir.mkdir(parents=True)
            result = createMovie(payload)
            
            assert result.title == "Inception"
            assert result.reviews == []
            mockSaveMeta.assert_called_once()
            mockSaveReviews.assert_called_once_with("Inception", [])
    
    def testCreateMovieAlreadyExists(self, mockBaseDir):
        """Test creating a movie that already exists"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        payload = movieCreate(
            title="Inception",
            movieGenres=["Action"],
            directors=["Nolan"],
            movieIMDbRating=8.8,
            datePublished="2010",
            totalRatingCount=1000,
            totalUserReviews="500",
            totalCriticReviews="50",
            metaScore="85",
            creators=["Nolan"],
            mainStars=["DiCaprio"],
            description="A movie"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            with pytest.raises(HTTPException) as excInfo:
                createMovie(payload)
            assert excInfo.value.status_code == 409


# Tests for updateMovie()
class TestUpdateMovie:
    
    def testUpdateMovieSuccess(self, mockBaseDir, sampleReviews):
        """Test successfully updating a movie"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        payload = movieUpdate(
            title="Inception",
            movieGenres=["Action", "Thriller"],
            directors=["Christopher Nolan"],
            movieIMDbRating=9.0,
            datePublished="2010-07-16",
            totalRatingCount=2000,
            totalUserReviews="1000",
            totalCriticReviews="100",
            metaScore="90",
            creators=["Christopher Nolan"],
            mainStars=["Leonardo DiCaprio"],
            description="Updated description"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'saveMetadata') as mockSave, \
             patch.object(movieServices, 'loadReviews', return_value=sampleReviews):
            
            result = updateMovie("Inception", payload)
            assert result.title == "Inception"
            assert result.movieIMDbRating == 9.0
            mockSave.assert_called_once()
    
    def testUpdateMovieNotFound(self, mockBaseDir):
        """Test updating a non-existent movie"""
        payload = movieUpdate(
            title="NonExistent",
            movieGenres=["Action"],
            directors=["Unknown"],
            movieIMDbRating=5.0,
            datePublished="2020",
            totalRatingCount=100,
            totalUserReviews="50",
            totalCriticReviews="10",
            metaScore="50",
            creators=["Unknown"],
            mainStars=["Unknown"],
            description="Unknown"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            with pytest.raises(HTTPException) as excInfo:
                updateMovie("NonExistent", payload)
            assert excInfo.value.status_code == 404


# Tests for deleteMovie()
class TestDeleteMovie:
    
    def testDeleteMovieSuccess(self, mockBaseDir):
        """Test successfully deleting a movie"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        (movieDir / "metadata.json").touch()
        (movieDir / "reviews.csv").touch()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            deleteMovie("Inception")
            assert not movieDir.exists()
    
    def testDeleteMovieNotFound(self, mockBaseDir):
        """Test deleting a non-existent movie"""
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            with pytest.raises(HTTPException) as excInfo:
                deleteMovie("NonExistent")
            assert excInfo.value.status_code == 404


# Tests for addReview()
class TestAddReview:
    
    def testAddReviewSuccess(self, mockBaseDir, sampleReviews):
        """Test successfully adding a review"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        payload = movieReviewsCreate(
            reviewer="Mike",
            rating=10,
            comment="Masterpiece!",
            dateOfReview="2010-08-05",
            user="mike789",
            usefulnessVote=15,
            totalVotes=20,
            userRatingOutOf10=10,
            reviewTitle="Perfect!",
            review="Masterpiece!"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadReviews', return_value=sampleReviews), \
             patch.object(movieServices, 'saveReviews') as mockSave:
            
            result = addReview("Inception", payload)
            assert result.user == "mike789"
            assert result.userRatingOutOf10 == 10
            mockSave.assert_called_once()
    
    def testAddReviewMovieNotFound(self, mockBaseDir):
        """Test adding a review to non-existent movie"""
        payload = movieReviewsCreate(
            reviewer="Mike",
            rating=10,
            comment="Great!",
            dateOfReview="2010-08-05",
            user="mike789",
            usefulnessVote=15,
            totalVotes=20,
            userRatingOutOf10=10,
            reviewTitle="Great!",
            review="Great!"
        )
        
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            with pytest.raises(HTTPException) as excInfo:
                addReview("NonExistent", payload)
            assert excInfo.value.status_code == 404


# Tests for searchMovies()
class TestSearchMovies:
    
    def testSearchMoviesEmptyDirectory(self, mockBaseDir):
        """Test searching when data directory doesn't exist"""
        filters = movieFilter()
        with patch.object(movieServices, 'baseDir', mockBaseDir):
            result = searchMovies(filters)
            assert result == []
    
    def testSearchByTitle(self, mockBaseDir, sampleMetadata):
        """Test searching movies by title"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(title="Incep")
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 1
            assert result[0].title == "Inception"
    
    def testSearchByGenre(self, mockBaseDir, sampleMetadata):
        """Test searching movies by genre"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(genres=["Sci-Fi"])
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 1
    
    def testSearchByDirector(self, mockBaseDir, sampleMetadata):
        """Test searching movies by director"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(directors=["Christopher Nolan"])
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 1
    
    def testSearchByRatingRange(self, mockBaseDir, sampleMetadata):
        """Test searching movies by rating range"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(min_rating=8.0, max_rating=9.0)
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 1
    
    def testSearchByYear(self, mockBaseDir, sampleMetadata):
        """Test searching movies by year"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(year=2010)
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 1
    
    def testSearchNoMatches(self, mockBaseDir, sampleMetadata):
        """Test searching with no matching results"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "Inception"
        movieDir.mkdir()
        
        filters = movieFilter(title="NonExistent")
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=sampleMetadata):
            
            result = searchMovies(filters)
            assert len(result) == 0
    
    def testSearchSkipsInvalidMetadata(self, mockBaseDir):
        """Test that search skips movies without metadata"""
        mockBaseDir.mkdir(parents=True)
        movieDir = mockBaseDir / "InvalidMovie"
        movieDir.mkdir()
        
        filters = movieFilter()
        
        with patch.object(movieServices, 'baseDir', mockBaseDir), \
             patch.object(movieServices, 'loadMetadata', return_value=None):
            
            result = searchMovies(filters)
            assert result == []


# Integration-style tests
class TestIntegration:
    
    def testCreateAndGetMovie(self, mockBaseDir):
        """Test creating a movie and then retrieving it"""
        payload = movieCreate(
            title="TestMovie",
            movieGenres=["Drama"],
            directors=["Test Director"],
            movieIMDbRating=7.5,
            datePublished="2023-01-01",
            totalRatingCount=500,
            totalUserReviews="250",
            totalCriticReviews="25",
            metaScore="75",
            creators=["Test Director"],
            mainStars=["Test Actor"],
            description="A test movie"
        )
        
        mockBaseDir.mkdir(parents=True)
        
        with patch.object(movieServices, 'saveMetadata'), \
             patch.object(movieServices, 'saveReviews'), \
             patch.object(movieServices, 'loadMetadata', return_value=payload.model_dump()), \
             patch.object(movieServices, 'loadReviews', return_value=[]):
            
            with patch.object(movieServices, 'baseDir', mockBaseDir):
                created = createMovie(payload)
                assert created.title == "TestMovie"
            
            # Create the directory after createMovie for getMovieByName
            movieDir = mockBaseDir / "TestMovie"
            movieDir.mkdir()
            
            with patch.object(movieServices, 'baseDir', mockBaseDir):
                # Now get it
                retrieved = getMovieByName("TestMovie")
                assert retrieved.title == "TestMovie"
                assert retrieved.movieIMDbRating == 7.5