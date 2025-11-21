import pytest
from pathlib import Path
from fastapi import HTTPException
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import json
from backend.services.movieListServices import saveMovieList

@pytest.fixture
def mockBaseDir(tmp_path):
    """Create a temporary base directory for tests"""
    return tmp_path / "data"

class TestSaveMovieList:
    def testCreateMovieListForNewUser(self, mockBaseDir):
        fakeMovieList =["Inception", "Spider-Man", "The Shining"]
        #Create a mock test file to store the user's movie lists
        movieLists = Path(mockBaseDir/"movieLists.json")
        name = "test"
        listName = "favourites"
        data = {}
        saveMovieList(fakeMovieList, name, listName, mockBaseDir)

        assert movieLists.exists()

        with open(movieLists, 'r') as jsonFile:
            try:
                data = json.load(jsonFile)
            except json.JSONDecodeError:
                data = {}
        print(data[name][listName])
        assert name in data
        assert listName in data[name]
        for movie in data[name][listName]:
            assert movie in fakeMovieList

    def testCreateMovieListWithExistingUsers(self, mockBaseDir):
        fakeMovieList =["Inception", "Spider-Man", "The Shining"]
        #Create a mock test file to store the user's movie lists
        movieLists = Path(mockBaseDir/"movieLists.json")
        name = "test"
        listName = "favourites"
        data = {}
        saveMovieList(fakeMovieList, name, listName, mockBaseDir)

        saveMovieList(["Morbius","Joker"], "Not Test", "Cool", mockBaseDir)
        saveMovieList(["Morbius", "Joker"], name, "Cool", mockBaseDir)
        with open(movieLists, 'r') as jsonFile:
            try:
                data = json.load(jsonFile)
            except json.JSONDecodeError:
                data = {}
            jsonFile.close()
        
        assert name in data
        assert listName in data[name]
        assert "Cool" in data[name]
        for movie in data[name]["Cool"]:
            assert movie in ["Morbius","Joker"]
        for movie in data["Not Test"]["Cool"]:
            assert movie in ["Morbius","Joker"]

    def testOverwrittingWithSaveMovieList(self, mockBaseDir):   
        fakeMovieList =["Inception", "Spider-Man", "The Shining"]
        #Create a mock test file to store the user's movie lists
        movieLists = Path(mockBaseDir/"movieLists.json")
        name = "test"
        listName = "favourites"
        data = {}
        saveMovieList(fakeMovieList, name, listName, mockBaseDir)
        saveMovieList(["Morbius","Joker"],name, listName, mockBaseDir)

        with open(movieLists, 'r') as jsonFile:
            try:
                data = json.load(jsonFile)
            except json.JSONDecodeError:
                data = {}
            jsonFile.close()
        
        for movie in data[name][listName]:
            assert movie in ["Morbius", "Joker"]
            assert not movie in fakeMovieList
            