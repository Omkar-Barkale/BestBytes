import pytest
import sys
from pathlib import Path
import json
from backend.users import user

from unittest.mock import mock_open, patch, MagicMock


#pylint: disable = function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = user.User(name, email, pswd, save = False)

def test_saveUserToDB():
    #If we call this function, we should be able to find the specific user created
    path = Path(r"backendTesting\usersTest.json")
    with patch.object(testUser, 'path', path):
        testUser.saveUserToDB(path)
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



    


    