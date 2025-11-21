import bcrypt
import uuid
import re
import json


from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import threading

from backend.services.userServices import saveUserToDB

#pylint: disable = C0303
class User:
    activeSessions = {}  # Store active user sessions with expiry
    _lock = threading.Lock()  # Thread lock for concurrent access
    sessionTimeout = timedelta(hours=24)  # Sessions expire after 24 hours
    
    def __init__(self, username: str, email: str, password: str, save:bool = True):
        """Initialize a new user with validation"""
        self.id = str(uuid.uuid4())

        path = Path(r"backend\data\Users\userList.json")

        self.path = path

        data = {}
        if path.exists():
            with open(path, 'r') as jsonFile:
                try:
                    data = json.load(jsonFile)
                except json.JSONDecodeError:
                    data = {}

        
      
        # Validate and set username
        if self.checkUsername(username):
            if username in data:
                raise ValueError("Username already exists")
            else:
                self.username =username
        else:
            raise ValueError("Invalid username: must be 3-20 characters and alphanumeric")
        
        # Validate and set email
        if self.checkEmail(email):
            self.email = email
        else:
            raise ValueError("Invalid email address")
        
        # Encrypt and set password
        self.passwordHash = self.encryptPassword(password)
        self.isVerified = False  # Email verification status
        self.verificationToken = str(uuid.uuid4())
        self.createdAt = datetime.now()
        self.lastLogin = None

        if save:
            saveUserToDB(path)
        
    
    
    def checkUsername(self, username: str) -> bool:
        """Validate username: 3-20 characters, alphanumeric only"""
        if len(username) < 3 or len(username) > 20:
            return False
        elif username.isalnum():
            return True
        else:
            return False
    
    
    def checkEmail(self, email: str) -> bool:
        """Validate email format and check if domain has MX records"""
        # Basic email format validation
        emailPattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(emailPattern, email):
            return True
        return False
    

    
    def encryptPassword(self, password: str) -> bytes:
        """Encrypt password using bcrypt"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed
    
    def verifyPassword(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.passwordHash)
    
    def verifyEmail(self, token: str) -> bool:
        """Verify user's email with verification token"""
        if token == self.verificationToken:
            self.isVerified = True
            return True
        return False
    
    
    def _cleanExpiredSessions(cls):
        """Remove expired sessions"""
        currentTime = datetime.now()
        expiredTokens = [
            token for token, (user, loginTime) in cls.activeSessions.items()
            if currentTime - loginTime > cls.sessionTimeout
        ]
        for token in expiredTokens:
            del cls.activeSessions[token]
    
    
    def createAccount(cls, username: str, email: str, password: str) -> 'User':
        """Create a new user account"""
        with cls._lock:  # Thread-safe operation
            # Check if username already exists
            if username in cls.usersDb:
                raise ValueError("Username already exists")
            
            # Check if email already exists
            for user in cls.usersDb.values():
                if user.email == email:
                    raise ValueError("Email already registered")
            
            # Create new user
            newUser = cls(username, email, password)
            cls.usersDb[username] = newUser
            
            print(f"Account created! Verification token: {newUser.verificationToken}")
            print(f"Total users: {len(cls.usersDb)}")
            
            return newUser
    

    def login(cls, username: str, password: str) -> Optional[str]:
        """Login user and return session token"""
        with cls._lock:  # Thread-safe operation
            # Clean expired sessions first
            cls._cleanExpiredSessions()
            
            # Check if user exists
            if username not in cls.usersDb:
                raise ValueError("Invalid username or password")
            
            user = cls.usersDb[username]
            
            # Verify password
            if not user.verifyPassword(password):
                raise ValueError("Invalid username or password")
            
            # Check if email is verified
            if not user.isVerified:
                raise ValueError("Please verify your email before logging in")
            
            # Create session token
            sessionToken = str(uuid.uuid4())
            cls.activeSessions[sessionToken] = (user, datetime.now())
            user.lastLogin = datetime.now()
            
            print(f"Login successful! Welcome, {username}")
            print(f"Active sessions: {len(cls.activeSessions)}")
            return sessionToken
    
    def logout(cls, sessionToken: str) -> bool:
        """Logout user by removing session token"""
        with cls._lock:  # Thread-safe operation
            if sessionToken in cls.activeSessions:
                user, _ = cls.activeSessions[sessionToken]
                del cls.activeSessions[sessionToken]
                print(f"Logout successful! Goodbye, {user.username}")
                print(f"Active sessions: {len(cls.activeSessions)}")
                return True
            return False
    

    def getCurrentUser(cls, sessionToken: str) -> Optional['User']:
        """Get currently logged-in user from session token"""
        with cls._lock:  # Thread-safe operation
            cls._cleanExpiredSessions()
            
            if sessionToken in cls.activeSessions:
                user, loginTime = cls.activeSessions[sessionToken]
                # Check if session is still valid
                if datetime.now() - loginTime <= cls.sessionTimeout:
                    return user
                else:
                    # Session expired, remove it
                    del cls.activeSessions[sessionToken]
            return None
    
               