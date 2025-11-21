import pytest
import sys
import json
import csv
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock, call
from backend.repositories import itemsRepo

# pylint: disable=function-naming-style, method-naming-style


class TestGetMovieDir:
    """Tests for getMovieDir function"""
    
    def testGetMovieDirReturnsCorrectPath(self):
        """Verify getMovieDir constructs correct path"""
        movieName = "test"
        expectedPath = itemsRepo.baseDir / movieName
        assert itemsRepo.getMovieDir(movieName) == expectedPath
    
    def testGetMovieDirWithSpecialCharacters(self):
        """Test movie names with special characters"""
        movieName = "test-movie_2025"
        expectedPath = itemsRepo.baseDir / movieName
        assert itemsRepo.getMovieDir(movieName) == expectedPath
    
    def testGetMovieDirWithSpaces(self):
        """Test movie names with spaces"""
        movieName = "The Great Movie"
        expectedPath = itemsRepo.baseDir / movieName
        assert itemsRepo.getMovieDir(movieName) == expectedPath


class TestLoadMetadata:
    """Tests for loadMetadata function"""
    
    def testLoadMetadataFileMissing(self):
        """Returns empty dict when metadata file doesn't exist"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
            result = itemsRepo.loadMetadata("NonExistentMovie")
            assert result == {}
    
    def testLoadMetadataSuccess(self):
        """Successfully loads valid metadata JSON"""
        fakeJson = '{"title": "FakeMovie", "year": 2025, "director": "John Doe"}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fakeJson)):
            result = itemsRepo.loadMetadata("FakeMovie")
            assert result == {"title": "FakeMovie", "year": 2025, "director": "John Doe"}
    
    def testLoadMetadataEmptyJson(self):
        """Handles empty JSON object"""
        fakeJson = '{}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fakeJson)):
            result = itemsRepo.loadMetadata("FakeMovie")
            assert result == {}
    
    def testLoadMetadataWithUnicode(self):
        """Handles Unicode characters in metadata"""
        fakeJson = '{"title": "Amélie", "director": "Jean-Pierre Jeunet"}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fakeJson)):
            result = itemsRepo.loadMetadata("Amélie")
            assert result["title"] == "Amélie"
    
    def testLoadMetadataCorruptedJson(self):
        """Raises error for corrupted JSON"""
        fakeJson = '{"title": "FakeMovie", "year": 2025'  # Missing closing brace
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fakeJson)):
            with pytest.raises(json.JSONDecodeError):
                itemsRepo.loadMetadata("FakeMovie")


class TestLoadReviews:
    """Tests for loadReviews function"""
    
    def testLoadReviewsFileMissing(self):
        """Returns empty list when reviews file doesn't exist"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
            result = itemsRepo.loadReviews("NonExistentMovie")
            assert result == []
    
    def testLoadReviewsSuccess(self):
        """Successfully loads valid reviews CSV"""
        csvData = "name,review\nAlice,Great Movie\nBob,Ok"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert len(result) == 2
            assert result[0]["name"] == "Alice"
            assert result[0]["review"] == "Great Movie"
            assert result[1]["name"] == "Bob"
            assert result[1]["review"] == "Ok"
    
    def testLoadReviewsEmptyFile(self):
        """Handles CSV with only headers"""
        csvData = "name,review\n"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert result == []
    
    def testLoadReviewsWithCommasInContent(self):
        """Handles reviews containing commas"""
        csvData = "name,review\nAlice,\"Great, really enjoyed it\"\nBob,Okay"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert len(result) == 2
            assert result[0]["review"] == "Great, really enjoyed it"
    
    def testLoadReviewsWithUnicode(self):
        """Handles Unicode characters in reviews"""
        csvData = "name,review\nAlice,Très bon film!\nBob,Excelente película"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert result[0]["review"] == "Très bon film!"
            assert result[1]["review"] == "Excelente película"


class TestSaveMetadata:
    """Tests for saveMetadata function"""
    
    def testSaveMetadataWritesFile(self, tmp_path):
        """Successfully writes metadata to file"""
        movieName = "FakeMovie"
        data = {"title": "FakeMovie", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            
            filePath = tmp_path / movieName / "metadata.json"
            assert filePath.exists()
            
            content = json.loads(filePath.read_text(encoding="utf-8"))
            assert content == data
    
    def testSaveMetadataCreatesDirectory(self, tmp_path):
        """Creates directory if it doesn't exist"""
        movieName = "NewMovie"
        data = {"title": "NewMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movieDir = tmp_path / movieName
            assert not movieDir.exists()
            
            itemsRepo.saveMetadata(movieName, data)
            
            assert movieDir.exists()
            assert (movieDir / "metadata.json").exists()
    
    def testSaveMetadataOverwritesExisting(self, tmp_path):
        """Overwrites existing metadata file"""
        movieName = "FakeMovie"
        oldData = {"title": "Old Title"}
        newData = {"title": "New Title", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, oldData)
            itemsRepo.saveMetadata(movieName, newData)
            
            filePath = tmp_path / movieName / "metadata.json"
            content = json.loads(filePath.read_text(encoding="utf-8"))
            assert content == newData
    
    def testSaveMetadataWithUnicode(self, tmp_path):
        """Handles Unicode characters correctly"""
        movieName = "Amélie"
        data = {"title": "Amélie", "director": "Jean-Pierre Jeunet"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            
            filePath = tmp_path / movieName / "metadata.json"
            content = json.loads(filePath.read_text(encoding="utf-8"))
            assert content["title"] == "Amélie"
    
    def testSaveMetadataEmptyDict(self, tmp_path):
        """Handles empty metadata dictionary"""
        movieName = "EmptyMovie"
        data = {}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            
            filePath = tmp_path / movieName / "metadata.json"
            content = json.loads(filePath.read_text(encoding="utf-8"))
            assert content == {}
    
    def testSaveMetadataUsesAtomicWrite(self, tmp_path):
        """Verifies atomic write using temporary file"""
        movieName = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace") as mockReplace:
                itemsRepo.saveMetadata(movieName, data)
                
                # Verify os.replace was called (atomic operation)
                assert mockReplace.called


class TestSaveReviews:
    """Tests for saveReviews function"""
    
    def testSaveReviewsWritesCsv(self, tmp_path):
        """Successfully writes reviews to CSV"""
        movieName = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Good"},
            {"name": "Bob", "review": "Great"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            
            filePath = tmp_path / movieName / "movieReviews.csv"
            assert filePath.exists()
            
            with filePath.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["name"] == "Alice"
                assert rows[1]["review"] == "Great"
    
    def testSaveReviewsDeletesFileWhenEmpty(self, tmp_path):
        """Deletes reviews file when list is empty"""
        movieName = "FakeMovie"
        
        movieDir = tmp_path / movieName
        movieDir.mkdir()
        filePath = movieDir / "movieReviews.csv"
        filePath.touch()
        assert filePath.exists()
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, [])
            assert not filePath.exists()
    
    def testSaveReviewsEmptyListNoFileExists(self, tmp_path):
        """Handles empty list when no file exists"""
        movieName = "FakeMovie"
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Should not raise an error
            itemsRepo.saveReviews(movieName, [])
            
            filePath = tmp_path / movieName / "movieReviews.csv"
            assert not filePath.exists()
    
    def testSaveReviewsWithSpecialCharacters(self, tmp_path):
        """Handles reviews with special characters"""
        movieName = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Great, really \"amazing\"!"},
            {"name": "Bob", "review": "It's okay, not bad"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            
            filePath = tmp_path / movieName / "movieReviews.csv"
            with filePath.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert rows[0]["review"] == "Great, really \"amazing\"!"
    
    def testSaveReviewsWithUnicode(self, tmp_path):
        """Handles Unicode characters in reviews"""
        movieName = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Très bon!"},
            {"name": "Bob", "review": "Excelente película"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            
            filePath = tmp_path / movieName / "movieReviews.csv"
            with filePath.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert rows[0]["review"] == "Très bon!"
    
    def testSaveReviewsCreatesDirectory(self, tmp_path):
        """Creates directory if it doesn't exist"""
        movieName = "NewMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movieDir = tmp_path / movieName
            assert not movieDir.exists()
            
            itemsRepo.saveReviews(movieName, reviews)
            
            assert movieDir.exists()
            assert (movieDir / "movieReviews.csv").exists()
    
    def testSaveReviewsUsesAtomicWrite(self, tmp_path):
        """Verifies atomic write using temporary file"""
        movieName = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace") as mockReplace:
                itemsRepo.saveReviews(movieName, reviews)
                assert mockReplace.called
    
    def testSaveReviewsOverwritesExisting(self, tmp_path):
        """Overwrites existing reviews file"""
        movieName = "FakeMovie"
        oldReviews = [{"name": "Alice", "review": "Good"}]
        newReviews = [
            {"name": "Bob", "review": "Great"},
            {"name": "Charlie", "review": "Amazing"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, oldReviews)
            itemsRepo.saveReviews(movieName, newReviews)
            
            filePath = tmp_path / movieName / "movieReviews.csv"
            with filePath.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["name"] == "Bob"


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def testSaveAndLoadMetadataRoundtrip(self, tmp_path):
        """Verify save and load metadata work together"""
        movieName = "TestMovie"
        data = {"title": "TestMovie", "year": 2025, "director": "John Doe"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loadedData = itemsRepo.loadMetadata(movieName)
            assert loadedData == data
    
    def testSaveAndLoadReviewsRoundtrip(self, tmp_path):
        """Verify save and load reviews work together"""
        movieName = "TestMovie"
        reviews = [
            {"name": "Alice", "review": "Excellent"},
            {"name": "Bob", "review": "Good movie"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            loadedReviews = itemsRepo.loadReviews(movieName)
            assert loadedReviews == reviews
    
    def testMultipleMoviesIsolation(self, tmp_path):
        """Verify different movies don't interfere with each other"""
        movie1 = "Movie1"
        movie2 = "Movie2"
        data1 = {"title": "Movie1"}
        data2 = {"title": "Movie2"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie1, data1)
            itemsRepo.saveMetadata(movie2, data2)
            
            loaded1 = itemsRepo.loadMetadata(movie1)
            loaded2 = itemsRepo.loadMetadata(movie2)
            
            assert loaded1 == data1
            assert loaded2 == data2


class TestEdgeCasesAndErrorHandling:
    """Additional edge cases and error scenarios"""
    
    def testLoadMetadataFileReadPermissionError(self):
        """Handles permission errors when reading metadata"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                itemsRepo.loadMetadata("FakeMovie")
    
    def testLoadReviewsFileReadPermissionError(self):
        """Handles permission errors when reading reviews"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                itemsRepo.loadReviews("FakeMovie")
    
    def testSaveMetadataWritePermissionError(self, tmp_path):
        """Handles permission errors when writing metadata"""
        movieName = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Create directory but make it read-only
            movieDir = tmp_path / movieName
            movieDir.mkdir()
            
            with patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Write denied")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveMetadata(movieName, data)
    
    def testSaveReviewsWritePermissionError(self, tmp_path):
        """Handles permission errors when writing reviews"""
        movieName = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movieDir = tmp_path / movieName
            movieDir.mkdir()
            
            with patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Write denied")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveReviews(movieName, reviews)
    
    def testSaveMetadataDirectoryCreationError(self, tmp_path):
        """Handles errors when creating movie directory"""
        movieName = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("backend.repositories.itemsRepo.Path.mkdir", side_effect=OSError("Cannot create directory")):
                with pytest.raises(OSError):
                    itemsRepo.saveMetadata(movieName, data)
    
    def testLoadReviewsMalformedCsv(self):
        """Handles malformed CSV data gracefully"""
        # CSV with inconsistent columns
        csvData = "name,review\nAlice,Good,Extra\nBob"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csvData)):
            # Should still load but may have unexpected structure
            result = itemsRepo.loadReviews("FakeMovie")
            # csv.DictReader is lenient, so this should work
            assert isinstance(result, list)
    
    def testSaveMetadataWithNestedStructures(self, tmp_path):
        """Handles complex nested data structures"""
        movieName = "ComplexMovie"
        data = {
            "title": "Complex Movie",
            "cast": [
                {"name": "Actor 1", "role": "Lead"},
                {"name": "Actor 2", "role": "Support"}
            ],
            "ratings": {
                "imdb": 8.5,
                "rotten_tomatoes": 95
            }
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loadedData = itemsRepo.loadMetadata(movieName)
            assert loadedData == data
    
    def testSaveReviewsWithExtraFields(self, tmp_path):
        """Handles reviews with varying field sets"""
        movieName = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Good", "rating": "5"},
            {"name": "Bob", "review": "Okay", "rating": "3"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            loadedReviews = itemsRepo.loadReviews(movieName)
            assert len(loadedReviews) == 2
            assert "rating" in loadedReviews[0]
    
    def testLoadMetadataEncodingError(self):
        """Handles encoding issues in metadata file"""
        # Invalid UTF-8 byte sequence
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True):
            m = mock_open()
            m.return_value.read.side_effect = UnicodeDecodeError(
                'utf-8', b'\x80', 0, 1, 'invalid start byte'
            )
            with patch("backend.repositories.itemsRepo.Path.open", m):
                with pytest.raises(UnicodeDecodeError):
                    itemsRepo.loadMetadata("FakeMovie")
    
    def testSaveMetadataWithNonSerializableData(self, tmp_path):
        """Handles non-JSON-serializable data"""
        movieName = "FakeMovie"
        
        # Create a non-serializable object
        class NonSerializable:
            pass
        
        data = {"title": "FakeMovie", "object": NonSerializable()}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with pytest.raises(TypeError):
                itemsRepo.saveMetadata(movieName, data)
    
    def testBaseDirIsPathObject(self):
        """Verifies baseDir is a Path object"""
        assert isinstance(itemsRepo.baseDir, Path)
    
    def testGetMovieDirReturnsPathObject(self):
        """Verifies getMovieDir returns Path object"""
        result = itemsRepo.getMovieDir("TestMovie")
        assert isinstance(result, Path)
    
    def testSaveReviewsDeleteHandlesPermissionError(self, tmp_path):
        """Handles permission error when trying to delete empty reviews file"""
        movieName = "FakeMovie"
        
        movieDir = tmp_path / movieName
        movieDir.mkdir()
        filePath = movieDir / "movieReviews.csv"
        filePath.touch()
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("backend.repositories.itemsRepo.Path.unlink", side_effect=PermissionError("Cannot delete")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveReviews(movieName, [])
    
    def testSaveMetadataOsReplaceFailure(self, tmp_path):
        """Handles os.replace failure"""
        movieName = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace", side_effect=OSError("Replace failed")):
                with pytest.raises(OSError):
                    itemsRepo.saveMetadata(movieName, data)
    
    def testSaveReviewsOsReplaceFailure(self, tmp_path):
        """Handles os.replace failure for reviews"""
        movieName = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace", side_effect=OSError("Replace failed")):
                with pytest.raises(OSError):
                    itemsRepo.saveReviews(movieName, reviews)
    
    def testLoadMetadataWithVeryLargeFile(self, tmp_path):
        """Handles large metadata files"""
        movieName = "LargeMovie"
        # Create large data structure
        data = {
            "title": "Large Movie",
            "cast": [{"actor": f"Actor {i}"} for i in range(1000)]
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loadedData = itemsRepo.loadMetadata(movieName)
            assert len(loadedData["cast"]) == 1000
    
    def testLoadReviewsWithManyReviews(self, tmp_path):
        """Handles CSV files with many reviews"""
        movieName = "PopularMovie"
        reviews = [
            {"name": f"User{i}", "review": f"Review {i}"}
            for i in range(100)
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            loadedReviews = itemsRepo.loadReviews(movieName)
            assert len(loadedReviews) == 100


class TestRealFileSystemOperations:
    """Tests using actual file system (not mocked) to ensure real behavior"""
    
    def testSaveMetadataCreatesActualFile(self, tmp_path):
        """Integration test: actually write and read metadata file"""
        movieName = "RealMovie"
        data = {"title": "Real Movie", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Save the metadata
            itemsRepo.saveMetadata(movieName, data)
            
            # Verify file was created
            metadataFile = tmp_path / movieName / "metadata.json"
            assert metadataFile.exists()
            assert metadataFile.is_file()
            
            # Verify content without using loadMetadata
            with open(metadataFile, 'r', encoding='utf-8') as f:
                content = json.load(f)
            assert content == data
    
    def testSaveReviewsCreatesActualCsv(self, tmp_path):
        """Integration test: actually write and read CSV file"""
        movieName = "RealMovie"
        reviews = [
            {"name": "Alice", "review": "Great"},
            {"name": "Bob", "review": "Good"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Save reviews
            itemsRepo.saveReviews(movieName, reviews)
            
            # Verify file was created
            reviewsFile = tmp_path / movieName / "movieReviews.csv"
            assert reviewsFile.exists()
            assert reviewsFile.is_file()
            
            # Verify content without using loadReviews
            with open(reviewsFile, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "Alice"
    
    def testMetadataFileFormatCorrect(self, tmp_path):
        """Verify metadata JSON is properly formatted"""
        movieName = "FormattedMovie"
        data = {"title": "Test", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            
            metadataFile = tmp_path / movieName / "metadata.json"
            content = metadataFile.read_text(encoding='utf-8')
            
            # Check it's indented (indent=2)
            assert '\n' in content
            assert '  ' in content  # Should have 2-space indentation
    
    def testReviewsCsvHasProperHeaders(self, tmp_path):
        """Verify CSV file has correct headers"""
        movieName = "HeaderMovie"
        reviews = [{"name": "Alice", "review": "Good", "rating": "5"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            
            reviewsFile = tmp_path / movieName / "movieReviews.csv"
            with open(reviewsFile, 'r', encoding='utf-8') as f:
                firstLine = f.readline().strip()
            
            # Headers should match the dict keys
            assert "name" in firstLine
            assert "review" in firstLine
            assert "rating" in firstLine
    
    def testAtomicWriteTempFileCleanup(self, tmp_path):
        """Verify temporary files are cleaned up after successful write"""
        movieName = "TempFileMovie"
        data = {"title": "Test"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            
            movieDir = tmp_path / movieName
            # Check no .tmp files remain
            tmpFiles = list(movieDir.glob("*.tmp"))
            assert len(tmpFiles) == 0
    
    def testSaveReviewsAtomicWriteTempCleanup(self, tmp_path):
        """Verify temporary CSV files are cleaned up"""
        movieName = "TempCSVMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            
            movieDir = tmp_path / movieName
            # Check no .tmp files remain
            tmpFiles = list(movieDir.glob("*.tmp"))
            assert len(tmpFiles) == 0
    
    def testConcurrentSavesLastWriteWins(self, tmp_path):
        """Verify last write wins when saving multiple times"""
        movieName = "ConcurrentMovie"
        data1 = {"title": "First", "version": 1}
        data2 = {"title": "Second", "version": 2}
        data3 = {"title": "Third", "version": 3}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data1)
            itemsRepo.saveMetadata(movieName, data2)
            itemsRepo.saveMetadata(movieName, data3)
            
            loaded = itemsRepo.loadMetadata(movieName)
            assert loaded == data3
            assert loaded["version"] == 3


class TestPathOperations:
    """Tests focusing on path handling and structure"""
    
    def testBaseDirStructure(self):
        """Verify baseDir points to correct location"""
        # baseDir should be parent/parent/data from the repo file
        assert itemsRepo.baseDir.name == "data"
        assert itemsRepo.baseDir.is_absolute()
    
    def testGetMovieDirPreservesCase(self):
        """Verify movie names are preserved in paths (case may vary by OS)"""
        import platform
        
        movieLower = "testmovie"
        movieUpper = "TESTMOVIE"
        movieMixed = "TestMovie"
        
        pathLower = itemsRepo.getMovieDir(movieLower)
        pathUpper = itemsRepo.getMovieDir(movieUpper)
        pathMixed = itemsRepo.getMovieDir(movieMixed)
        
        # On case-sensitive filesystems (Linux/Mac), paths should differ
        # On Windows, paths may be equal but the movie name is still preserved
        if platform.system() != "Windows":
            assert pathLower != pathUpper
            assert pathLower != pathMixed
            assert pathUpper != pathMixed
        else:
            # On Windows, verify the movie name is at least in the path string
            assert movieLower in str(pathLower).lower()
            assert movieUpper.lower() in str(pathUpper).lower()
            assert movieMixed.lower() in str(pathMixed).lower()
    
    def testMetadataPathConstruction(self):
        """Verify metadata.json path is constructed correctly"""
        movieName = "TestMovie"
        expected = itemsRepo.baseDir / movieName / "metadata.json"
        
        # We can verify this by checking what getMovieDir returns
        movieDir = itemsRepo.getMovieDir(movieName)
        assert movieDir / "metadata.json" == expected
    
    def testReviewsPathConstruction(self):
        """Verify movieReviews.csv path is constructed correctly"""
        movieName = "TestMovie"
        expected = itemsRepo.baseDir / movieName / "movieReviews.csv"
        
        movieDir = itemsRepo.getMovieDir(movieName)
        assert movieDir / "movieReviews.csv" == expected


class TestBoundaryConditions:
    """Tests for boundary conditions and extreme values"""
    
    def testEmptyMovieName(self):
        """Handle empty string as movie name"""
        movieName = ""
        path = itemsRepo.getMovieDir(movieName)
        # Should still work, just creates path with empty name
        assert path == itemsRepo.baseDir / ""
    
    def testVeryLongMovieName(self):
        """Handle very long movie names"""
        movieName = "A" * 255  # Max filename length on most systems
        path = itemsRepo.getMovieDir(movieName)
        assert movieName in str(path)
    
    def testMetadataWithNullValues(self, tmp_path):
        """Handle null values in metadata"""
        movieName = "NullMovie"
        data = {"title": "Test", "director": None, "year": None}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loaded = itemsRepo.loadMetadata(movieName)
            assert loaded["director"] is None
            assert loaded["year"] is None
    
    def testReviewsWithEmptyStrings(self, tmp_path):
        """Handle empty strings in review fields"""
        movieName = "EmptyFieldsMovie"
        reviews = [
            {"name": "", "review": ""},
            {"name": "Bob", "review": ""}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            loaded = itemsRepo.loadReviews(movieName)
            assert loaded[0]["name"] == ""
            assert loaded[0]["review"] == ""
    
    def testMetadataWithBooleanValues(self, tmp_path):
        """Handle boolean values in metadata"""
        movieName = "BoolMovie"
        data = {"title": "Test", "available": True, "restricted": False}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loaded = itemsRepo.loadMetadata(movieName)
            assert loaded["available"] is True
            assert loaded["restricted"] is False
    
    def testMetadataWithNumericValues(self, tmp_path):
        """Handle various numeric types in metadata"""
        movieName = "NumericMovie"
        data = {
            "title": "Test",
            "year": 2025,
            "rating": 8.5,
            "budget": 1000000,
            "runtime": 120.5
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loaded = itemsRepo.loadMetadata(movieName)
            assert loaded["year"] == 2025
            assert loaded["rating"] == 8.5
            assert loaded["budget"] == 1000000
    
    def testReviewsSingleColumn(self, tmp_path):
        """Handle reviews with only one field"""
        movieName = "SingleColumnMovie"
        reviews = [{"review": "Good"}, {"review": "Bad"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movieName, reviews)
            loaded = itemsRepo.loadReviews(movieName)
            assert len(loaded) == 2
            assert "review" in loaded[0]
    
    def testMetadataWithArrayValues(self, tmp_path):
        """Handle arrays in metadata"""
        movieName = "ArrayMovie"
        data = {
            "title": "Test",
            "genres": ["Action", "Comedy", "Drama"],
            "cast": ["Actor1", "Actor2"]
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movieName, data)
            loaded = itemsRepo.loadMetadata(movieName)
            assert loaded["genres"] == ["Action", "Comedy", "Drama"]
            assert len(loaded["cast"]) == 2