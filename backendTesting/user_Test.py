import pytest
import sys
from pathlib import Path
import json
from backend.users import user
from unittest.mock import mock_open, patch, MagicMock
from unittest import TestCase


#pylint: disable = function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = user.User(name, email, pswd, save = False)


#Test checkUsername
class TestCheckUsername:
    def testCheckUsernameTooShort(self):
        assert testUser.checkUsername("a") == False

    def testCheckUsernameTooLong(self):
        assert testUser.checkUsername("aaaaaaaaaaaaaaaaaaaaaaaaaa") == False

    def testCheckUsernameNonAlphnum(self):
        assert testUser.checkUsername("abcde%") == False
    
    def testCheckUsernameValid(self):
        assert testUser.checkUsername("Username") == True

class checkEmail:
    def testCheckEmailBadPattern(self):
        assert testUser.checkEmail("email.com") == True
        assert testUser.checkEmail("email.email.com") == True
    
    def testCheckEmailValidPattern(self):
        assert testUser.checkEmail("email@email.com")

class encryptPassword(TestCase):
    def testEncryptPassword(self):
        with self.assertRaises(Exception):
            testUser.encryptPassword("a")

    def testEncryptPassword(self):
        assert isinstance(testUser.encryptPassword("password"),bytes)
    


    