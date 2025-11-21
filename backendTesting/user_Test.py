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




    


    