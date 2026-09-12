"""Authentication and authorization utilities with JWT."""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Literal, Optional
import os

# User role type
UserRole = Literal["operator", "basic"]

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "d687019fcd2ef40a5710aa556ec1902c")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

# Static users for demo (in production, use database)
USERS_DB = {
    "admin@truthos.com": {
        "email": "admin@truthos.com",
        "password": "AdminPass123",  # In production, use hashed passwords
        "role": "operator"
    },
    "user@truthos.com": {
        "email": "user@truthos.com",
        "password": "UserPass123",  # In production, use hashed passwords
        "role": "basic"
    }
}

# HTTP Bearer security scheme
security = HTTPBearer()


def create_access_token(email: str, role: str) -> str:
    """
    Create a JWT access token.
    
    Args:
        email: User email
        role: User role (operator or basic)
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "role": role,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: 401 if token invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        if email is None or role is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": "Invalid token payload"
                }
            )
        
        return {"email": email, "role": role}
    
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_TOKEN",
                "message": f"Token validation failed: {str(e)}"
            }
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to extract and validate user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        User dict with email and role
        
    Raises:
        HTTPException: 401 if token missing or invalid
    """
    token = credentials.credentials
    user = verify_token(token)
    return user


async def get_user_role(user: dict = Depends(get_current_user)) -> UserRole:
    """
    Dependency to extract user role from authenticated user.
    
    Args:
        user: Authenticated user dict
        
    Returns:
        User role
    """
    return user["role"]


async def require_operator_role(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to enforce operator role requirement.
    
    Args:
        user: Authenticated user dict
        
    Returns:
        User dict if operator
        
    Raises:
        HTTPException: 403 if user is not operator
    """
    if user["role"] != "operator":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "This operation requires operator role"
            }
        )
    
    return user


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user with email and password.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User dict if authentication successful, None otherwise
    """
    user = USERS_DB.get(email)
    
    if not user:
        return None
    
    # In production, use password hashing (bcrypt)
    if user["password"] != password:
        return None
    
    return user