import os
from fastapi import APIRouter, HTTPException
from backend.users.user import User

router = APIRouter()


# register user
@router.post("/register")
def registerUser(username: str, email: str, password: str):
    """Create a new user account."""
    try:
        newUser = User.createAccount(User, username=username, email=email, password=password)
        return {
            "message": "Account created successfully!",
            "username": newUser.username,
            "email": newUser.email,
            "verificationToken": newUser.verificationToken
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# verify email
@router.post("/verify")
def verifyEmail(username: str, token: str):
    """Verify user's email using the verification token."""
    if username not in User.usersDb:
        raise HTTPException(status_code=404, detail="User not found")

    user = User.usersDb[username]
    if user.verifyEmail(token):
        return {"message": "Email verified successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification token")

# login user
@router.post("/login")
def loginUser(username: str, password: str):
    """Login a user and return a session token."""
    try:
        sessionToken = User.login(User, username=username, password=password)
        return {"message": "Login successful!", "sessionToken": sessionToken}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# logout user
@router.post("/logout")
def logoutUser(sessionToken: str):
    """Logout a user by removing their session token."""
    if User.logout(User, sessionToken):
        return {"message": "Logout successful!"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired session token")

# get current user
@router.get("/me")
def getCurrentUser(sessionToken: str):
    """Return the current logged-in user's details if session is valid."""
    currentUser = User.getCurrentUser(User, sessionToken)
    if currentUser:
        return {
            "username": currentUser.username,
            "email": currentUser.email,
            "verified": currentUser.isVerified,
            "createdAt": str(currentUser.createdAt),
            "lastLogin": str(currentUser.lastLogin) if currentUser.lastLogin else None
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
