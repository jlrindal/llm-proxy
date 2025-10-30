"""
Simple JWT authentication using Supabase tokens.
Your iOS app sends the Supabase auth token in the Authorization header.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from config import settings

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token from Supabase and return user info.
    Your iOS app should send: Authorization: Bearer <supabase_jwt_token>
    """
    token = credentials.credentials
    
    try:
        # Decode the JWT token using your Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "id": user_id,
            "email": payload.get("email")
        }
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

