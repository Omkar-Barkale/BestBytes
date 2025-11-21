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
    
    def testVerifyEmailFalse(self):
        assert testUser.verifyEmail(testUser.id) == False
    

    