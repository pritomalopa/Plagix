from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.tenant import Tenant


def get_token_from_cookie_or_header(request: Request) -> str:
    """Extract access token from httpOnly cookie or Authorization header."""
    # 1. Try httpOnly cookie first (secure primary method)
    token = request.cookies.get("access_token")
    if token:
        # Remove 'Bearer ' prefix if present in cookie value
        if token.startswith("Bearer "):
            token = token[7:]
        return token
    
    # 2. Fallback to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
            
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get the currently authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = get_token_from_cookie_or_header(request)
    if not token:
        raise credentials_exception
        
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise credentials_exception
        
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
        
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or suspended"
        )
        
    return user


def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to verify current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def verify_tenant_access(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforce strict tenant isolation: user must belong to the requested tenant."""
    if current_user.tenant_id != tenant_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cross-tenant access is prohibited"
        )
    return current_user
