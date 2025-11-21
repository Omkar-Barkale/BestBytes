import pytest
import sys
from pathlib import Path
import json
from backend.users.user import User
from backend.users.penaltyPoints import PenaltyPoints
from unittest.mock import mock_open, patch, MagicMock
from unittest import TestCase


#pylint: disable = function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = User(name, email, pswd, save = False)


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
    user = User.createAccount(name, email, pswd)
    user.isVerified = True
    
    # Add 2 penalty points
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")
    
    # Should not raise error
    token = user.login(name, pswd)
    assert token is not None

# logging in with less than 3 penalty points
def test_login_allowed_with_fewer_than_3_penalties():
    user = User.createAccount(name, email, pswd)
    user.isVerified = True  # mark verified for login

    # Add 2 penalty points
    pp1 = PenaltyPoints(1, user, "Reason 1")
    pp2 = PenaltyPoints(1, user, "Reason 2")
    user.penaltyPointsList.extend([pp1, pp2])  # important for totalPenaltyPoints

    # Should not raise error
    token = User.login(name, pswd)
    assert token is not None


# logging in with >= 3 penalty points
def test_login_blocked_with_more_than_3_penalties():
    blocked_name = "testblocked"
    blocked_email = "blocked_" + email
    user = User.createAccount(blocked_name, blocked_email, pswd)
    user.isVerified = True

    # Add 5 penalty points
    points = [PenaltyPoints(1, user, f"Reason {i}") for i in range(1, 6)]
    user.penaltyPointsList.extend(points)

    # Should raise ValueError because points >= 3
    with pytest.raises(ValueError, match="too many penalty points"):
        User.login(blocked_name, pswd)
