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
    
    def test_get_movie_dir_returns_correct_path(self):
        """Verify getMovieDir constructs correct path"""
        movie_name = "test"
        expected_path = itemsRepo.baseDir / movie_name
        assert itemsRepo.getMovieDir(movie_name) == expected_path
    
    def test_get_movie_dir_with_special_characters(self):
        """Test movie names with special characters"""
        movie_name = "test-movie_2025"
        expected_path = itemsRepo.baseDir / movie_name
        assert itemsRepo.getMovieDir(movie_name) == expected_path
    
    def test_get_movie_dir_with_spaces(self):
        """Test movie names with spaces"""
        movie_name = "The Great Movie"
        expected_path = itemsRepo.baseDir / movie_name
        assert itemsRepo.getMovieDir(movie_name) == expected_path


class TestLoadMetadata:
    """Tests for loadMetadata function"""
    
    def test_load_metadata_file_missing(self):
        """Returns empty dict when metadata file doesn't exist"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
            result = itemsRepo.loadMetadata("NonExistentMovie")
            assert result == {}
    
    def test_load_metadata_success(self):
        """Successfully loads valid metadata JSON"""
        fake_json = '{"title": "FakeMovie", "year": 2025, "director": "John Doe"}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fake_json)):
            result = itemsRepo.loadMetadata("FakeMovie")
            assert result == {"title": "FakeMovie", "year": 2025, "director": "John Doe"}
    
    def test_load_metadata_empty_json(self):
        """Handles empty JSON object"""
        fake_json = '{}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fake_json)):
            result = itemsRepo.loadMetadata("FakeMovie")
            assert result == {}
    
    def test_load_metadata_with_unicode(self):
        """Handles Unicode characters in metadata"""
        fake_json = '{"title": "Amélie", "director": "Jean-Pierre Jeunet"}'
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fake_json)):
            result = itemsRepo.loadMetadata("Amélie")
            assert result["title"] == "Amélie"
    
    def test_load_metadata_corrupted_json(self):
        """Raises error for corrupted JSON"""
        fake_json = '{"title": "FakeMovie", "year": 2025'  # Missing closing brace
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=fake_json)):
            with pytest.raises(json.JSONDecodeError):
                itemsRepo.loadMetadata("FakeMovie")


class TestLoadReviews:
    """Tests for loadReviews function"""
    
    def test_load_reviews_file_missing(self):
        """Returns empty list when reviews file doesn't exist"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=False):
            result = itemsRepo.loadReviews("NonExistentMovie")
            assert result == []
    
    def test_load_reviews_success(self):
        """Successfully loads valid reviews CSV"""
        csv_data = "name,review\nAlice,Great Movie\nBob,Ok"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csv_data)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert len(result) == 2
            assert result[0]["name"] == "Alice"
            assert result[0]["review"] == "Great Movie"
            assert result[1]["name"] == "Bob"
            assert result[1]["review"] == "Ok"
    
    def test_load_reviews_empty_file(self):
        """Handles CSV with only headers"""
        csv_data = "name,review\n"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csv_data)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert result == []
    
    def test_load_reviews_with_commas_in_content(self):
        """Handles reviews containing commas"""
        csv_data = "name,review\nAlice,\"Great, really enjoyed it\"\nBob,Okay"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csv_data)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert len(result) == 2
            assert result[0]["review"] == "Great, really enjoyed it"
    
    def test_load_reviews_with_unicode(self):
        """Handles Unicode characters in reviews"""
        csv_data = "name,review\nAlice,Très bon film!\nBob,Excelente película"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csv_data)):
            result = itemsRepo.loadReviews("FakeMovie")
            assert result[0]["review"] == "Très bon film!"
            assert result[1]["review"] == "Excelente película"


class TestSaveMetadata:
    """Tests for saveMetadata function"""
    
    def test_save_metadata_writes_file(self, tmp_path):
        """Successfully writes metadata to file"""
        movie_name = "FakeMovie"
        data = {"title": "FakeMovie", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            
            file_path = tmp_path / movie_name / "metadata.json"
            assert file_path.exists()
            
            content = json.loads(file_path.read_text(encoding="utf-8"))
            assert content == data
    
    def test_save_metadata_creates_directory(self, tmp_path):
        """Creates directory if it doesn't exist"""
        movie_name = "NewMovie"
        data = {"title": "NewMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movie_dir = tmp_path / movie_name
            assert not movie_dir.exists()
            
            itemsRepo.saveMetadata(movie_name, data)
            
            assert movie_dir.exists()
            assert (movie_dir / "metadata.json").exists()
    
    def test_save_metadata_overwrites_existing(self, tmp_path):
        """Overwrites existing metadata file"""
        movie_name = "FakeMovie"
        old_data = {"title": "Old Title"}
        new_data = {"title": "New Title", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, old_data)
            itemsRepo.saveMetadata(movie_name, new_data)
            
            file_path = tmp_path / movie_name / "metadata.json"
            content = json.loads(file_path.read_text(encoding="utf-8"))
            assert content == new_data
    
    def test_save_metadata_with_unicode(self, tmp_path):
        """Handles Unicode characters correctly"""
        movie_name = "Amélie"
        data = {"title": "Amélie", "director": "Jean-Pierre Jeunet"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            
            file_path = tmp_path / movie_name / "metadata.json"
            content = json.loads(file_path.read_text(encoding="utf-8"))
            assert content["title"] == "Amélie"
    
    def test_save_metadata_empty_dict(self, tmp_path):
        """Handles empty metadata dictionary"""
        movie_name = "EmptyMovie"
        data = {}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            
            file_path = tmp_path / movie_name / "metadata.json"
            content = json.loads(file_path.read_text(encoding="utf-8"))
            assert content == {}
    
    def test_save_metadata_uses_atomic_write(self, tmp_path):
        """Verifies atomic write using temporary file"""
        movie_name = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace") as mock_replace:
                itemsRepo.saveMetadata(movie_name, data)
                
                # Verify os.replace was called (atomic operation)
                assert mock_replace.called


class TestSaveReviews:
    """Tests for saveReviews function"""
    
    def test_save_reviews_writes_csv(self, tmp_path):
        """Successfully writes reviews to CSV"""
        movie_name = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Good"},
            {"name": "Bob", "review": "Great"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            
            file_path = tmp_path / movie_name / "movieReviews.csv"
            assert file_path.exists()
            
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["name"] == "Alice"
                assert rows[1]["review"] == "Great"
    
    def test_save_reviews_deletes_file_when_empty(self, tmp_path):
        """Deletes reviews file when list is empty"""
        movie_name = "FakeMovie"
        
        movie_dir = tmp_path / movie_name
        movie_dir.mkdir()
        file_path = movie_dir / "movieReviews.csv"
        file_path.touch()
        assert file_path.exists()
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, [])
            assert not file_path.exists()
    
    def test_save_reviews_empty_list_no_file_exists(self, tmp_path):
        """Handles empty list when no file exists"""
        movie_name = "FakeMovie"
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Should not raise an error
            itemsRepo.saveReviews(movie_name, [])
            
            file_path = tmp_path / movie_name / "movieReviews.csv"
            assert not file_path.exists()
    
    def test_save_reviews_with_special_characters(self, tmp_path):
        """Handles reviews with special characters"""
        movie_name = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Great, really \"amazing\"!"},
            {"name": "Bob", "review": "It's okay, not bad"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            
            file_path = tmp_path / movie_name / "movieReviews.csv"
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert rows[0]["review"] == "Great, really \"amazing\"!"
    
    def test_save_reviews_with_unicode(self, tmp_path):
        """Handles Unicode characters in reviews"""
        movie_name = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Très bon!"},
            {"name": "Bob", "review": "Excelente película"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            
            file_path = tmp_path / movie_name / "movieReviews.csv"
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert rows[0]["review"] == "Très bon!"
    
    def test_save_reviews_creates_directory(self, tmp_path):
        """Creates directory if it doesn't exist"""
        movie_name = "NewMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movie_dir = tmp_path / movie_name
            assert not movie_dir.exists()
            
            itemsRepo.saveReviews(movie_name, reviews)
            
            assert movie_dir.exists()
            assert (movie_dir / "movieReviews.csv").exists()
    
    def test_save_reviews_uses_atomic_write(self, tmp_path):
        """Verifies atomic write using temporary file"""
        movie_name = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace") as mock_replace:
                itemsRepo.saveReviews(movie_name, reviews)
                assert mock_replace.called
    
    def test_save_reviews_overwrites_existing(self, tmp_path):
        """Overwrites existing reviews file"""
        movie_name = "FakeMovie"
        old_reviews = [{"name": "Alice", "review": "Good"}]
        new_reviews = [
            {"name": "Bob", "review": "Great"},
            {"name": "Charlie", "review": "Amazing"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, old_reviews)
            itemsRepo.saveReviews(movie_name, new_reviews)
            
            file_path = tmp_path / movie_name / "movieReviews.csv"
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["name"] == "Bob"


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_save_and_load_metadata_roundtrip(self, tmp_path):
        """Verify save and load metadata work together"""
        movie_name = "TestMovie"
        data = {"title": "TestMovie", "year": 2025, "director": "John Doe"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded_data = itemsRepo.loadMetadata(movie_name)
            assert loaded_data == data
    
    def test_save_and_load_reviews_roundtrip(self, tmp_path):
        """Verify save and load reviews work together"""
        movie_name = "TestMovie"
        reviews = [
            {"name": "Alice", "review": "Excellent"},
            {"name": "Bob", "review": "Good movie"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            loaded_reviews = itemsRepo.loadReviews(movie_name)
            assert loaded_reviews == reviews
    
    def test_multiple_movies_isolation(self, tmp_path):
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
    
    def test_load_metadata_file_read_permission_error(self):
        """Handles permission errors when reading metadata"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                itemsRepo.loadMetadata("FakeMovie")
    
    def test_load_reviews_file_read_permission_error(self):
        """Handles permission errors when reading reviews"""
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                itemsRepo.loadReviews("FakeMovie")
    
    def test_save_metadata_write_permission_error(self, tmp_path):
        """Handles permission errors when writing metadata"""
        movie_name = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Create directory but make it read-only
            movie_dir = tmp_path / movie_name
            movie_dir.mkdir()
            
            with patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Write denied")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveMetadata(movie_name, data)
    
    def test_save_reviews_write_permission_error(self, tmp_path):
        """Handles permission errors when writing reviews"""
        movie_name = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            movie_dir = tmp_path / movie_name
            movie_dir.mkdir()
            
            with patch("backend.repositories.itemsRepo.Path.open", side_effect=PermissionError("Write denied")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveReviews(movie_name, reviews)
    
    def test_save_metadata_directory_creation_error(self, tmp_path):
        """Handles errors when creating movie directory"""
        movie_name = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("backend.repositories.itemsRepo.Path.mkdir", side_effect=OSError("Cannot create directory")):
                with pytest.raises(OSError):
                    itemsRepo.saveMetadata(movie_name, data)
    
    def test_load_reviews_malformed_csv(self):
        """Handles malformed CSV data gracefully"""
        # CSV with inconsistent columns
        csv_data = "name,review\nAlice,Good,Extra\nBob"
        
        with patch("backend.repositories.itemsRepo.Path.exists", return_value=True), \
             patch("backend.repositories.itemsRepo.Path.open", mock_open(read_data=csv_data)):
            # Should still load but may have unexpected structure
            result = itemsRepo.loadReviews("FakeMovie")
            # csv.DictReader is lenient, so this should work
            assert isinstance(result, list)
    
    def test_save_metadata_with_nested_structures(self, tmp_path):
        """Handles complex nested data structures"""
        movie_name = "ComplexMovie"
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
            itemsRepo.saveMetadata(movie_name, data)
            loaded_data = itemsRepo.loadMetadata(movie_name)
            assert loaded_data == data
    
    def test_save_reviews_with_extra_fields(self, tmp_path):
        """Handles reviews with varying field sets"""
        movie_name = "FakeMovie"
        reviews = [
            {"name": "Alice", "review": "Good", "rating": "5"},
            {"name": "Bob", "review": "Okay", "rating": "3"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            loaded_reviews = itemsRepo.loadReviews(movie_name)
            assert len(loaded_reviews) == 2
            assert "rating" in loaded_reviews[0]
    
    def test_load_metadata_encoding_error(self):
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
    
    def test_save_metadata_with_non_serializable_data(self, tmp_path):
        """Handles non-JSON-serializable data"""
        movie_name = "FakeMovie"
        
        # Create a non-serializable object
        class NonSerializable:
            pass
        
        data = {"title": "FakeMovie", "object": NonSerializable()}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with pytest.raises(TypeError):
                itemsRepo.saveMetadata(movie_name, data)
    
    def test_base_dir_is_path_object(self):
        """Verifies baseDir is a Path object"""
        assert isinstance(itemsRepo.baseDir, Path)
    
    def test_get_movie_dir_returns_path_object(self):
        """Verifies getMovieDir returns Path object"""
        result = itemsRepo.getMovieDir("TestMovie")
        assert isinstance(result, Path)
    
    def test_save_reviews_delete_handles_permission_error(self, tmp_path):
        """Handles permission error when trying to delete empty reviews file"""
        movie_name = "FakeMovie"
        
        movie_dir = tmp_path / movie_name
        movie_dir.mkdir()
        file_path = movie_dir / "movieReviews.csv"
        file_path.touch()
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("backend.repositories.itemsRepo.Path.unlink", side_effect=PermissionError("Cannot delete")):
                with pytest.raises(PermissionError):
                    itemsRepo.saveReviews(movie_name, [])
    
    def test_save_metadata_os_replace_failure(self, tmp_path):
        """Handles os.replace failure"""
        movie_name = "FakeMovie"
        data = {"title": "FakeMovie"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace", side_effect=OSError("Replace failed")):
                with pytest.raises(OSError):
                    itemsRepo.saveMetadata(movie_name, data)
    
    def test_save_reviews_os_replace_failure(self, tmp_path):
        """Handles os.replace failure for reviews"""
        movie_name = "FakeMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            with patch("os.replace", side_effect=OSError("Replace failed")):
                with pytest.raises(OSError):
                    itemsRepo.saveReviews(movie_name, reviews)
    
    def test_load_metadata_with_very_large_file(self, tmp_path):
        """Handles large metadata files"""
        movie_name = "LargeMovie"
        # Create large data structure
        data = {
            "title": "Large Movie",
            "cast": [{"actor": f"Actor {i}"} for i in range(1000)]
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded_data = itemsRepo.loadMetadata(movie_name)
            assert len(loaded_data["cast"]) == 1000
    
    def test_load_reviews_with_many_reviews(self, tmp_path):
        """Handles CSV files with many reviews"""
        movie_name = "PopularMovie"
        reviews = [
            {"name": f"User{i}", "review": f"Review {i}"}
            for i in range(100)
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            loaded_reviews = itemsRepo.loadReviews(movie_name)
            assert len(loaded_reviews) == 100


class TestRealFileSystemOperations:
    """Tests using actual file system (not mocked) to ensure real behavior"""
    
    def test_save_metadata_creates_actual_file(self, tmp_path):
        """Integration test: actually write and read metadata file"""
        movie_name = "RealMovie"
        data = {"title": "Real Movie", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Save the metadata
            itemsRepo.saveMetadata(movie_name, data)
            
            # Verify file was created
            metadata_file = tmp_path / movie_name / "metadata.json"
            assert metadata_file.exists()
            assert metadata_file.is_file()
            
            # Verify content without using loadMetadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            assert content == data
    
    def test_save_reviews_creates_actual_csv(self, tmp_path):
        """Integration test: actually write and read CSV file"""
        movie_name = "RealMovie"
        reviews = [
            {"name": "Alice", "review": "Great"},
            {"name": "Bob", "review": "Good"}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            # Save reviews
            itemsRepo.saveReviews(movie_name, reviews)
            
            # Verify file was created
            reviews_file = tmp_path / movie_name / "movieReviews.csv"
            assert reviews_file.exists()
            assert reviews_file.is_file()
            
            # Verify content without using loadReviews
            with open(reviews_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "Alice"
    
    def test_metadata_file_format_correct(self, tmp_path):
        """Verify metadata JSON is properly formatted"""
        movie_name = "FormattedMovie"
        data = {"title": "Test", "year": 2025}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            
            metadata_file = tmp_path / movie_name / "metadata.json"
            content = metadata_file.read_text(encoding='utf-8')
            
            # Check it's indented (indent=2)
            assert '\n' in content
            assert '  ' in content  # Should have 2-space indentation
    
    def test_reviews_csv_has_proper_headers(self, tmp_path):
        """Verify CSV file has correct headers"""
        movie_name = "HeaderMovie"
        reviews = [{"name": "Alice", "review": "Good", "rating": "5"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            
            reviews_file = tmp_path / movie_name / "movieReviews.csv"
            with open(reviews_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            
            # Headers should match the dict keys
            assert "name" in first_line
            assert "review" in first_line
            assert "rating" in first_line
    
    def test_atomic_write_temp_file_cleanup(self, tmp_path):
        """Verify temporary files are cleaned up after successful write"""
        movie_name = "TempFileMovie"
        data = {"title": "Test"}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            
            movie_dir = tmp_path / movie_name
            # Check no .tmp files remain
            tmp_files = list(movie_dir.glob("*.tmp"))
            assert len(tmp_files) == 0
    
    def test_save_reviews_atomic_write_temp_cleanup(self, tmp_path):
        """Verify temporary CSV files are cleaned up"""
        movie_name = "TempCSVMovie"
        reviews = [{"name": "Alice", "review": "Good"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            
            movie_dir = tmp_path / movie_name
            # Check no .tmp files remain
            tmp_files = list(movie_dir.glob("*.tmp"))
            assert len(tmp_files) == 0
    
    def test_concurrent_saves_last_write_wins(self, tmp_path):
        """Verify last write wins when saving multiple times"""
        movie_name = "ConcurrentMovie"
        data1 = {"title": "First", "version": 1}
        data2 = {"title": "Second", "version": 2}
        data3 = {"title": "Third", "version": 3}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data1)
            itemsRepo.saveMetadata(movie_name, data2)
            itemsRepo.saveMetadata(movie_name, data3)
            
            loaded = itemsRepo.loadMetadata(movie_name)
            assert loaded == data3
            assert loaded["version"] == 3


class TestPathOperations:
    """Tests focusing on path handling and structure"""
    
    def test_base_dir_structure(self):
        """Verify baseDir points to correct location"""
        # baseDir should be parent/parent/data from the repo file
        assert itemsRepo.baseDir.name == "data"
        assert itemsRepo.baseDir.is_absolute()
    
    def test_get_movie_dir_preserves_case(self):
        """Verify movie names are preserved in paths (case may vary by OS)"""
        import platform
        
        movie_lower = "testmovie"
        movie_upper = "TESTMOVIE"
        movie_mixed = "TestMovie"
        
        path_lower = itemsRepo.getMovieDir(movie_lower)
        path_upper = itemsRepo.getMovieDir(movie_upper)
        path_mixed = itemsRepo.getMovieDir(movie_mixed)
        
        # On case-sensitive filesystems (Linux/Mac), paths should differ
        # On Windows, paths may be equal but the movie name is still preserved
        if platform.system() != "Windows":
            assert path_lower != path_upper
            assert path_lower != path_mixed
            assert path_upper != path_mixed
        else:
            # On Windows, verify the movie name is at least in the path string
            assert movie_lower in str(path_lower).lower()
            assert movie_upper.lower() in str(path_upper).lower()
            assert movie_mixed.lower() in str(path_mixed).lower()
    
    def test_metadata_path_construction(self):
        """Verify metadata.json path is constructed correctly"""
        movie_name = "TestMovie"
        expected = itemsRepo.baseDir / movie_name / "metadata.json"
        
        # We can verify this by checking what getMovieDir returns
        movie_dir = itemsRepo.getMovieDir(movie_name)
        assert movie_dir / "metadata.json" == expected
    
    def test_reviews_path_construction(self):
        """Verify movieReviews.csv path is constructed correctly"""
        movie_name = "TestMovie"
        expected = itemsRepo.baseDir / movie_name / "movieReviews.csv"
        
        movie_dir = itemsRepo.getMovieDir(movie_name)
        assert movie_dir / "movieReviews.csv" == expected


class TestBoundaryConditions:
    """Tests for boundary conditions and extreme values"""
    
    def test_empty_movie_name(self):
        """Handle empty string as movie name"""
        movie_name = ""
        path = itemsRepo.getMovieDir(movie_name)
        # Should still work, just creates path with empty name
        assert path == itemsRepo.baseDir / ""
    
    def test_very_long_movie_name(self):
        """Handle very long movie names"""
        movie_name = "A" * 255  # Max filename length on most systems
        path = itemsRepo.getMovieDir(movie_name)
        assert movie_name in str(path)
    
    def test_metadata_with_null_values(self, tmp_path):
        """Handle null values in metadata"""
        movie_name = "NullMovie"
        data = {"title": "Test", "director": None, "year": None}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded = itemsRepo.loadMetadata(movie_name)
            assert loaded["director"] is None
            assert loaded["year"] is None
    
    def test_reviews_with_empty_strings(self, tmp_path):
        """Handle empty strings in review fields"""
        movie_name = "EmptyFieldsMovie"
        reviews = [
            {"name": "", "review": ""},
            {"name": "Bob", "review": ""}
        ]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            loaded = itemsRepo.loadReviews(movie_name)
            assert loaded[0]["name"] == ""
            assert loaded[0]["review"] == ""
    
    def test_metadata_with_boolean_values(self, tmp_path):
        """Handle boolean values in metadata"""
        movie_name = "BoolMovie"
        data = {"title": "Test", "available": True, "restricted": False}
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded = itemsRepo.loadMetadata(movie_name)
            assert loaded["available"] is True
            assert loaded["restricted"] is False
    
    def test_metadata_with_numeric_values(self, tmp_path):
        """Handle various numeric types in metadata"""
        movie_name = "NumericMovie"
        data = {
            "title": "Test",
            "year": 2025,
            "rating": 8.5,
            "budget": 1000000,
            "runtime": 120.5
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded = itemsRepo.loadMetadata(movie_name)
            assert loaded["year"] == 2025
            assert loaded["rating"] == 8.5
            assert loaded["budget"] == 1000000
    
    def test_reviews_single_column(self, tmp_path):
        """Handle reviews with only one field"""
        movie_name = "SingleColumnMovie"
        reviews = [{"review": "Good"}, {"review": "Bad"}]
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveReviews(movie_name, reviews)
            loaded = itemsRepo.loadReviews(movie_name)
            assert len(loaded) == 2
            assert "review" in loaded[0]
    
    def test_metadata_with_array_values(self, tmp_path):
        """Handle arrays in metadata"""
        movie_name = "ArrayMovie"
        data = {
            "title": "Test",
            "genres": ["Action", "Comedy", "Drama"],
            "cast": ["Actor1", "Actor2"]
        }
        
        with patch("backend.repositories.itemsRepo.baseDir", tmp_path):
            itemsRepo.saveMetadata(movie_name, data)
            loaded = itemsRepo.loadMetadata(movie_name)
            assert loaded["genres"] == ["Action", "Comedy", "Drama"]
            assert len(loaded["cast"]) == 2