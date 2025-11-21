import pytest
import sys
from pathlib import Path
import json
from backend.services.userServices import saveUserToDB,findUserInDB
from backend.users import user
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock, mock_open


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
    saveUserToDB(testUser.username,testUser.email,testUser.passwordHash.decode('utf-8'),mockBaseDir)
    with open(path,'r') as jsonFile:
        try:
            data = json.load(jsonFile) 
        except json.JSONDecodeError:
            data = {}
        
    assert name in data
    assert email in data[name]["email"]
    assert testUser.passwordHash.decode('utf-8') in data[name]["password"]

    #clean up
    with open(path,'w') as jsonFile:
        jsonFile.truncate(0)


def testFindUserInDB(mockBaseDir):
    saveUserToDB(testUser.username,testUser.email,testUser.passwordHash.decode('utf-8'),mockBaseDir)
    saveUserToDB("testUser.username",testUser.email,testUser.passwordHash.decode('utf-8'),mockBaseDir)
    saveUserToDB("tester",testUser.email,testUser.passwordHash.decode('utf-8'),mockBaseDir)

    assert findUserInDB(testUser.username,mockBaseDir) == {"email":testUser.email,"password":testUser.passwordHash.decode('utf-8')}
    with pytest.raises(ValueError):
        findUserInDB("notTester",mockBaseDir)
        