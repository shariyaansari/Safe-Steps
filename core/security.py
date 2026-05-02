# This file contains utility functions for password hashing, verification, and JWT token creation. It uses the passlib library for secure password hashing and the jose library for JWT token management. The functions in this file are used throughout the application to handle authentication and authorization tasks, such as verifying user credentials and generating access tokens for authenticated users.
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash the password using bcrypt algorithm. This function is used when creating a new user or updating a user's password, to ensure that the password is stored securely in the database.
def get_password_hash(password):
    return pwd_context.hash(password)

# Verify the password by comparing the plain password with the hashed password. This function is used during the login process to check if the provided password matches the stored hashed password for a user.
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Create a JWT access token with the provided data and expiration time. This function is used to generate a token for authenticated users, which can be used for subsequent requests to access protected routes. The token includes an expiration time to enhance security by limiting the token's validity period.
def create_access_token(
    data: dict,
    secret_key: str,
    algorithm: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)