import pytest
import sys
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
from backend.repositories import itemsRepo

#pylint: disable = function-naming-style, method-naming-style
def testGetMovie():
    assert(str(itemsRepo.getMovieDir("test"))) == str(Path.cwd()) + "\\backend\data\\test"


    
