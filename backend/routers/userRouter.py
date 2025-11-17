import os
from fastapi import APIRouter, HTTPException
from users.user import User

router = APIRouter()

# register user
@router.post("/register")
def register_user(username: str, email: str, password: str):
    """Create a new user account."""
    try:
        new_user = User.createAccount(User, username=username, email=email, password=password)
        return {
            "message": "Account created successfully!",
            "username": new_user.username,
            "email": new_user.email,
            "verificationToken": new_user.verificationToken
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# verify email
@router.post("/verify")
def verify_email(username: str, token: str):
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
def login_user(username: str, password: str):
    """Login a user and return a session token."""
    try:
        session_token = User.login(User, username=username, password=password)
        return {"message": "Login successful!", "sessionToken": session_token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# logout user
@router.post("/logout")
def logout_user(sessionToken: str):
    """Logout a user by removing their session token."""
    if User.logout(User, sessionToken):
        return {"message": "Logout successful!"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired session token")

# get current user
@router.get("/me")
def get_current_user(sessionToken: str):
    """Return the current logged-in user's details if session is valid."""
    current_user = User.getCurrentUser(User, sessionToken)
    if current_user:
        return {
            "username": current_user.username,
            "email": current_user.email,
            "verified": current_user.isVerified,
            "createdAt": str(current_user.createdAt),
            "lastLogin": str(current_user.lastLogin) if current_user.lastLogin else None
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
