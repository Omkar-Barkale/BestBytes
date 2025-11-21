import pytest
import sys
from pathlib import Path
import json
from backend.services.userServices import saveUserToDB
from backend.users import user

from unittest.mock import mock_open, patch, MagicMock

@pytest.fixture
def mockBaseDir(tmp_path):
    """Create a temporary base directory for tests"""
    return tmp_path / "data"



#pylint: disable = function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = user.User(name, email, pswd, save = False)

def test_saveUserToDB(mockBaseDir):
    #If we call this function, we should be able to find the specific user created
    path = mockBaseDir/"users.json"
    saveUserToDB(testUser.username,testUser.email,testUser.passwordHash,mockBaseDir)
    with open(path,'r') as jsonFile:
        try:
            data = json.load(jsonFile) 
        except json.JSONDecodeError:
            data = {}
        
    assert name in data
    assert email in data[name]["email"]
    assert testUser.passwordHash in data[name]["password"]

    #clean up
    with open(path,'w') as jsonFile:
        jsonFile.truncate(0)