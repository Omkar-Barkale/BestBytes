import pytest
import sys
from pathlib import Path
import json
from backend.users import User
from backend.users.penaltyPoints import PenaltyPoints
from unittest.mock import mock_open, patch, MagicMock
from unittest import TestCase


#pylint: disable = function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = User.User(name, email, pswd, save = False)


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
    

# logging in with less than 3 penalty points check
def test_login_allowed_with_fewer_than_3_penalties():
    user = User.User(name, email, pswd, save=False)
    
    # Add 2 penalty points
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")
    
    # Should not raise error
    token = user.login(name, pswd)
    assert token is not None


# logging in with greater than or equal to 3 penalty points check
def test_login_blocked_with_more_than_3_penalties():
    user = User.User(name + "_blocked", "blocked_" + email, pswd, save=False)
    
    # Add more than 3 penalty points
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")
    PenaltyPoints(1, user, "Reason 3")
    PenaltyPoints(1, user, "Reason 4")
    PenaltyPoints(1, user, "Reason 5")
    
    # Should raise ValueError because points >= 3
    with pytest.raises(ValueError, match="Account blocked"):
        user.login(name + "_blocked", pswd)


    


