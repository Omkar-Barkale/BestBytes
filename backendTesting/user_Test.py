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

#Test checkEmail
class TestCheckEmail:
    def testCheckEmailBadPattern(self):
        assert testUser.checkEmail("email.com") == False
        assert testUser.checkEmail("email.email.com") == False
    
    def testCheckEmailValidPattern(self):
        assert testUser.checkEmail("email@email.com")

#Test Encrypt
class TestEncryptPassword(TestCase):
    def testEncryptPasswordInvalid(self):
        with self.assertRaises(Exception):
            testUser.encryptPassword("a")

    def testEncryptPasswordValid(self):
        assert isinstance(testUser.encryptPassword("password"),bytes)

#Test verifyPassword
class TestVerifyPassword:
    def testVerifyPasswordInvalid(self):
       assert testUser.verifyPassword("notpass") == False

    def testVerifyPasswordValid(self):
        assert testUser.verifyPassword("password") == True
    

class TestVerifyEmail:
    def testVerifyEmail(self):
        assert testUser.verifyEmail(testUser.verificationToken) == True
    
    def testVerifyEmailFalse(self):
        assert testUser.verifyEmail(testUser.id) == False
    
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
    # create user without saving to disk
    user = User(name, email, pswd, save=False)
    user.isVerified = True  # bypass email verification for testing

    # Add 2 penalty points
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")

    # Add user to in-memory db (needed for login)
    User.usersDb[user.username] = user

    # Login should succeed
    token = User.login(user.username, pswd)
    assert token is not None

def test_login_allowed_with_fewer_than_3_penalties():
    user = User(name, email, pswd, save=False)
    user.isVerified = True

    # Add 2 penalty points
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")

    # Add to in-memory db
    User.usersDb[user.username] = user

    token = User.login(user.username, pswd)
    assert token is not None


def test_login_blocked_with_more_than_3_penalties():
    blocked_user = User("blockeduser", "blocked_" + email, pswd, save=False)
    blocked_user.isVerified = True

    # Add 5 penalty points
    for i in range(5):
        PenaltyPoints(1, blocked_user, f"Reason {i+1}")

    User.usersDb[blocked_user.username] = blocked_user

    with pytest.raises(ValueError, match="too many penalty points"):
        User.login(blocked_user.username, pswd)

        
def test_create_account_success():
    username = "newuser1"
    email = "newuser1@example.com"
    password = "StrongPass123!"

    # Create account (user object) in memory only and not saving to a JSON file
    user = User(username, email, password, save=False)

    assert user.username == username
    assert user.email == email
    assert isinstance(user.passwordHash, bytes)
    assert user.isVerified is False   # default
    assert user.penaltyPointsList == []   # starts empty


# test fcn for login failure
def test_login_fails_not_verified():
    username = "unverified"
    email = "unverified@example.com"
    password = "password123"

    user = User(username, email, password, save=False)
    user.isVerified = False
    User.usersDb[user.username] = user

    with pytest.raises(ValueError, match="verify your email"):
        User.login(username, password)


# test fcn for duplicate account creation
def test_create_account_duplicate_username():
    username = "duplicateUser"
    email1 = "duplicate1@example.com"
    email2 = "duplicate2@example.com"
    password = "password1234"

    # First account
    user1 = User(username, email1, password, save=False)
    User.usersDb[user1.username] = user1

    # Second account with same username should fail
    with pytest.raises(ValueError, match="(?i)username already exists"):
        User.createAccount(username, email2, password)



