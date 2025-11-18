import pytest
import sys
from pathlib import Path

from backend.repositories import itemsRepo

#pylint: disable = function-naming-style, method-naming-style
def test_GetMovie():
    assert(itemsRepo.getMovieDir("test")) == Path.cwd() + "/backend/data"
