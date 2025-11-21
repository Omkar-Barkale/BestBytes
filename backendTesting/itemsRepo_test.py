import pytest
import sys
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
from backend.repositories import itemsRepo

#pylint: disable = function-naming-style, method-naming-style
def testGetMovie():
    assert itemsRepo.getMovieDir("test") == Path.cwd() / "backend" / "data" / "test"


def testGetMovieDirPath():
    movieName = "test"
    expectedPath = itemsRepo.baseDir / movieName
    assert itemsRepo.getMovieDir(movieName) == expectedPath




def testLoadMetadataMissing():
    with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
        result = itemsRepo.loadMetadata("FakeMovie")
        assert result == {}


def testLoadMetadataSuccess():
    fakeJson = '{"title": "FakeMovie", "year": 2025}'

    with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
         patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fakeJson)):
        result = itemsRepo.loadMetadata("FakeMovie")
        assert result == {"title": "FakeMovie", "year": 2025}




def testLoadReviewsMissing():
    with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
        result = itemsRepo.loadReviews("FakeMovie")
        assert result == []


def testLoadReviewsSuccess():
    csvData = "name,review\nAlice,Great Movie\nBob,Ok"

    with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
         patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
        result = itemsRepo.loadReviews("FakeMovie")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["review"] == "Great Movie"

def testSaveMetadataWritesFile(tmp_path):
    movieName = "FakeMovie"
    data = {"title": "FakeMovie"}
    
    # patch baseDir to tmp_path
    with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
        itemsRepo.saveMetadata(movieName, data)

        # check the file exists
        filePath = tmp_path / movieName / "metadata.json"
        assert filePath.exists()

        # check content
        content = filePath.read_text(encoding="utf-8")
        assert '"title": "FakeMovie"' in content


def testSaveReviewsWritesCsv(tmp_path):
    movieName = "FakeMovie"
    reviews = [{"name": "Alice", "review": "Good"}]
    
    with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
        itemsRepo.saveReviews(movieName, reviews)

        filePath = tmp_path / movieName / "movieReviews.csv"
        assert filePath.exists()

        content = filePath.read_text(encoding="utf-8")
        assert "Alice" in content
        assert "Good" in content


def testSaveReviewsDeletesFileWhenEmpty(tmp_path):
    movieName = "FakeMovie"

    # create an empty file
    movieDir = tmp_path / movieName
    movieDir.mkdir()
    filePath = movieDir / "movieReviews.csv"
    filePath.touch()
    assert filePath.exists()

    # patch baseDir to tmp_path
    with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
        itemsRepo.saveReviews(movieName, [])

        # file should be deleted
        assert not filePath.exists()
    
