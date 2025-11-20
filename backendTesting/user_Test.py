import pytest
import sys
from pathlib import Path

from backend.users import user

testUser = user.User("name", "email@email.com", "Password")
#pylint: disable = function-naming-style, method-naming-style
def test_CheckEmail():
    assert(testUser.checkEmail("email@email.com")) == True

def test_Check():
    assert(testUser.checkUsername("A")) == False
    
    