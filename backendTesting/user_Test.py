# CamelCase version of the provided test file

import pytest
import sys
from pathlib import Path
import json
from backend.users.user import User
from backend.users.penaltyPoints import PenaltyPoints
from unittest.mock import mock_open, patch, MagicMock
from unittest import TestCase
from datetime import datetime, timedelta
import threading

# pylint: disable=function-naming-style, method-naming-style
name = "test"
email = "email@email.com"
pswd = "password"
testUser = User(name, email, pswd, save=False)


@pytest.fixture(autouse=True)
def cleanupUsersDb():
    User.usersDb.clear()
    User.activeSessions.clear()
    yield
    User.usersDb.clear()
    User.activeSessions.clear()


class TestCheckUsername:
    def testCheckUsernameTooShort(self):
        assert testUser.checkUsername("a") is False

    def testCheckUsernameTooLong(self):
        assert testUser.checkUsername("a" * 26) is False

    def testCheckUsernameNonAlphnum(self):
        assert testUser.checkUsername("abcde%") is False

    def testCheckUsernameValid(self):
        assert testUser.checkUsername("Username") is True

    def testCheckUsernameMinLength(self):
        assert testUser.checkUsername("abc") is True

    def testCheckUsernameMaxLength(self):
        assert testUser.checkUsername("a" * 20) is True

    def testCheckUsernameJustOverMax(self):
        assert testUser.checkUsername("a" * 21) is False

    def testCheckUsernameWithUnderscore(self):
        assert testUser.checkUsername("user_name") is False
        assert testUser.checkUsername("test_user_123") is False

    def testCheckUsernameEmpty(self):
        assert testUser.checkUsername("") is False


class TestCheckEmail:
    def testCheckEmailBadPattern(self):
        assert testUser.checkEmail("email.com") is False
        assert testUser.checkEmail("email.email.com") is False

    def testCheckEmailValidPattern(self):
        assert testUser.checkEmail("email@email.com") is True

    def testCheckEmailMultipleAt(self):
        assert testUser.checkEmail("email@@email.com") is False

    def testCheckEmailNoTopLevelDomain(self):
        assert testUser.checkEmail("email@email") is False

    def testCheckEmailSpecialCharsInvalid(self):
        assert testUser.checkEmail("em ail@email.com") is False

    def testCheckEmailEmpty(self):
        assert testUser.checkEmail("") is False

    def testCheckEmailValidWithPlus(self):
        assert testUser.checkEmail("user+tag@email.com") is True


class TestEncryptPassword(TestCase):
    def testEncryptPasswordInvalid(self):
        with self.assertRaises(Exception):
            testUser.encryptPassword("a")

    def testEncryptPasswordValid(self):
        assert isinstance(testUser.encryptPassword("password"), bytes)

    def testEncryptPasswordMinLength(self):
        result = testUser.encryptPassword("12345678")
        assert isinstance(result, bytes)

    def testEncryptPasswordVeryLong(self):
        longPassword = "a" * 100
        with pytest.raises(ValueError, match="cannot be longer than 72 bytes"):
            testUser.encryptPassword(longPassword)

    def testEncryptPasswordSpecialChars(self):
        result = testUser.encryptPassword("P@ssw0rd!")
        assert isinstance(result, bytes)

    def testEncryptPasswordUnicode(self):
        result = testUser.encryptPassword("pässwörd123")
        assert isinstance(result, bytes)


class TestVerifyPassword:
    def testVerifyPasswordInvalid(self):
        assert testUser.verifyPassword("notpass") is False

    def testVerifyPasswordValid(self):
        assert testUser.verifyPassword("password") is True

    def testVerifyPasswordEmpty(self):
        assert testUser.verifyPassword("") is False

    def testVerifyPasswordCaseSensitive(self):
        assert testUser.verifyPassword("Password") is False
        assert testUser.verifyPassword("PASSWORD") is False

    def testVerifyPasswordWithSpaces(self):
        assert testUser.verifyPassword(" password") is False
        assert testUser.verifyPassword("password ") is False


class TestVerifyEmail:
    def testVerifyEmail(self):
        assert testUser.verifyEmail(testUser.verificationToken) is True

    def testVerifyEmailFalse(self):
        assert testUser.verifyEmail(testUser.id) is False

    def testVerifyEmailEmpty(self):
        assert testUser.verifyEmail("") is False

    def testVerifyEmailAlreadyVerified(self):
        user = User("testverify", "verify@test.com", "password123", save=False)
        user.verifyEmail(user.verificationToken)
        assert user.isVerified is True
        assert user.verifyEmail(user.verificationToken) is True
        assert user.isVerified is True


def testLoginAllowedWithFewerThan3Penalties():
    user = User(name, email, pswd, save=False)
    user.isVerified = True
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")
    User.usersDb[user.username] = user
    token = User.login(user.username, pswd)
    assert token is not None


def testLoginBlockedWithMoreThan3Penalties():
    blockedUser = User("blockeduser", "blocked@email.com", pswd, save=False)
    blockedUser.isVerified = True
    for i in range(5):
        PenaltyPoints(1, blockedUser, f"Reason {i+1}")
    User.usersDb[blockedUser.username] = blockedUser
    with pytest.raises(ValueError, match="too many penalty points"):
        User.login(blockedUser.username, pswd)


def testLoginBlockedWithExactly3Penalties():
    user = User("boundaryuser", "boundary@test.com", pswd, save=False)
    user.isVerified = True
    PenaltyPoints(1, user, "Reason 1")
    PenaltyPoints(1, user, "Reason 2")
    PenaltyPoints(1, user, "Reason 3")
    User.usersDb[user.username] = user
    with pytest.raises(ValueError, match="too many penalty points"):
        User.login(user.username, pswd)


def testLoginAllowedWithExpiredPenalties():
    user = User("expireduser", "expired@test.com", pswd, save=False)
    user.isVerified = True
    pp1 = PenaltyPoints(2, user, "Old violation")
    pp2 = PenaltyPoints(2, user, "Another old violation")
    pastTime = datetime.now() - timedelta(days=1)
    pp1.expiresAt = pastTime
    pp2.expiresAt = pastTime
    User.usersDb[user.username] = user
    token = User.login(user.username, pswd)
    assert token is not None


def testTotalPenaltyPoints():
    user = User("penaltytest", "penalty@test.com", "password123", save=False)
    PenaltyPoints(1, user, "Minor violation")
    PenaltyPoints(2, user, "Major violation")
    assert user.totalPenaltyPoints() == 3


def testTotalPenaltyPointsZero():
    user = User("newpenalty", "newpenalty@test.com", "password123", save=False)
    assert user.totalPenaltyPoints() == 0


def testCreateAccountSuccess():
    username = "newuser1"
    emailNew = "newuser1@example.com"
    password = "StrongPass123!"
    user = User(username, emailNew, password, save=False)
    assert user.username == username
    assert user.email == emailNew
    assert isinstance(user.passwordHash, bytes)
    assert user.isVerified is False
    assert user.penaltyPointsList == []


def testCreateAccountDuplicateUsername():
    username = "duplicateUser"
    email1 = "duplicate1@example.com"
    email2 = "duplicate2@example.com"
    password = "password1234"
    user1 = User(username, email1, password, save=False)
    User.usersDb[user1.username] = user1
    with pytest.raises(ValueError, match="(?i)username already exists"):
        User.createAccount(username, email2, password)


def testCreateAccountDuplicateEmail():
    username1 = "user1"
    username2 = "user2"
    sharedEmail = "same@example.com"
    password = "password1234"
    user1 = User(username1, sharedEmail, password, save=False)
    User.usersDb[user1.username] = user1
    with pytest.raises(ValueError, match="(?i)email already registered"):
        User.createAccount(username2, sharedEmail, password)


def testCreateAccountInvalidUsername():
    with pytest.raises(ValueError, match="Invalid username"):
        User("ab", "test@test.com", "password123", save=False)
    with pytest.raises(ValueError, match="Invalid username"):
        User("user@name", "test@test.com", "password123", save=False)


def testCreateAccountInvalidEmail():
    with pytest.raises(ValueError, match="Invalid email"):
        User("validuser", "invalidemail", "password123", save=False)


def testCreateAccountWeakPassword():
    with pytest.raises(ValueError, match="at least 8 characters"):
        User("validuser", "valid@test.com", "short", save=False)


def testLoginFailsNotVerified():
    username = "unverified"
    emailUnverified = "unverified@example.com"
    password = "password123"
    user = User(username, emailUnverified, password, save=False)
    user.isVerified = False
    User.usersDb[user.username] = user
    with pytest.raises(ValueError, match="verify your email"):
        User.login(username, password)


def testLoginInvalidUsername():
    with pytest.raises(ValueError, match="Invalid username or password"):
        User.login("nonexistent", "password123")


def testLoginInvalidPassword():
    user = User("testlogin", "testlogin@test.com", "correct123", save=False)
    user.isVerified = True
    User.usersDb[user.username] = user
    with pytest.raises(ValueError, match="Invalid username or password"):
        User.login(user.username, "wrongpassword")


def testLoginSuccess():
    user = User("logintest", "login@test.com", "password123", save=False)
    user.isVerified = True
    User.usersDb[user.username] = user
    token = User.login(user.username, "password123")
    assert token is not None
    assert token in User.activeSessions
    assert user.lastLogin is not None


def testLogoutSuccess():
    user = User("logouttest", "logout@test.com", "password123", save=False)
    user.isVerified = True
    User.usersDb[user.username] = user
    token = User.login(user.username, "password123")
    assert token in User.activeSessions
    result = user.logout(token)
    assert result is True
    assert token not in User.activeSessions


def testLogoutInvalidToken():
    user = User("logouttest2", "logout2@test.com", "password123", save=False)
    result = user.logout("invalid-token-12345")
    assert result is False


def testGetCurrentUserValid():
    user = User("sessiontest", "session@test.com", "password123", save=False)
    user.isVerified = True
    User.usersDb[user.username] = user
    token = User.login(user.username, "password123")
    retrievedUser = user.getCurrentUser(token)
    assert retrievedUser is not None
    assert retrievedUser.username == user.username


def testGetCurrentUserInvalid():
    user = User("sessiontest2", "session2@test.com", "password123", save=False)
    retrievedUser = user.getCurrentUser("invalid-token")
    assert retrievedUser is None


def testGetCurrentUserExpired():
    user = User("expiredtest", "expired@test.com", "password123", save=False)
    user.isVerified = True
    User.usersDb[user.username] = user
    token = User.login(user.username, "password123")
    if token in User.activeSessions:
        oldUser, _ = User.activeSessions[token]
        expiredTime = datetime.now() - timedelta(hours=25)
        User.activeSessions[token] = (oldUser, expiredTime)
    retrievedUser = user.getCurrentUser(token)
    assert retrievedUser is None
    assert token not in User.activeSessions


def testCleanExpiredSessions():
    user1 = User("cleanup1", "cleanup1@test.com", "password123", save=False)
    user2 = User("cleanup2", "cleanup2@test.com", "password123", save=False)
    user1.isVerified = True
    user2.isVerified = True
    User.usersDb[user1.username] = user1
    User.usersDb[user2.username] = user2
    token1 = User.login(user1.username, "password123")
    token2 = User.login(user2.username, "password123")
    if token1 in User.activeSessions:
        oldUser, _ = User.activeSessions[token1]
        expiredTime = datetime.now() - timedelta(hours=25)
        User.activeSessions[token1] = (oldUser, expiredTime)
    User._cleanExpiredSessions()
    assert token1 not in User.activeSessions
    assert token2 in User.activeSessions


def testCompleteUserWorkflow():
    username = "workflow"
    emailWorkflow = "workflow@test.com"
    password = "password123"
    user = User(username, emailWorkflow, password, save=False)
    User.usersDb[user.username] = user
    assert user.username == username
    assert user.isVerified is False
    user.verifyEmail(user.verificationToken)
    assert user.isVerified is True
    token = User.login(username, password)
    assert token is not None
    assert token in User.activeSessions
    result = user.logout(token)
    assert result is True
    assert token not in User.activeSessions


def testThreadSafetyLockExists():
    assert hasattr(User, "_lock")

    lock_type = type(threading.Lock())

    assert isinstance(User._lock, lock_type)


def testUserInitializationAttributes():
    user = User("attrtest", "attr@test.com", "password123", save=False)
    assert hasattr(user, "id")
    assert hasattr(user, "username")
    assert hasattr(user, "email")
    assert hasattr(user, "passwordHash")
    assert hasattr(user, "isVerified")
    assert hasattr(user, "verificationToken")
    assert hasattr(user, "createdAt")
    assert hasattr(user, "lastLogin")
    assert hasattr(user, "penaltyPointsList")
    assert isinstance(user.id, str)
    assert user.lastLogin is None
    assert isinstance(user.createdAt, datetime)
    assert isinstance(user.penaltyPointsList, list)


def testVerificationTokenIsUnique():
    user1 = User("unique1", "unique1@test.com", "password123", save=False)
    user2 = User("unique2", "unique2@test.com", "password123", save=False)
    assert user1.verificationToken != user2.verificationToken
    assert user1.id != user2.id
