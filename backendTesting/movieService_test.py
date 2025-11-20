import pytest
import sys
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
from backend.repositories import itemsRepo
from backend.services import moviesService

#pylint: disable = function-naming-style, method-naming-style


def testListMoviesEmpty(tmp_path):
    with patch("backend.services.moviesService.baseDir", tmp_path):
        result = moviesService.listMovies()
        assert result == []

