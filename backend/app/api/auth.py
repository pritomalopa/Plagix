from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db.session import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    """
    Register a new teacher account. Automatically creates a tenant workspace
    if none is specified, hashes password securely, and sets an httpOnly session cookie.
    """
    # 1. Check if email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )
    
    # 2. Create Tenant workspace
    tenant_name = user_in.tenant_name or f"{user_in.name}'s Workspace"
    tenant = Tenant(
        name=tenant_name,
        plan="free",
        settings={}
    )
    db.add(tenant)
    db.flush()  # Flush to get tenant.id
    
    # 3. Create User with hashed password
    hashed_password = get_password_hash(user_in.password)
    user = User(
        tenant_id=tenant.id,
        email=user_in.email,
        password_hash=hashed_password,
        role="teacher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 4. Generate Access Token & Set httpOnly Cookie
    access_token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24  # 24 hours
    )
    
    return user


@router.post("/login", response_model=UserResponse)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate teacher credentials, set secure httpOnly cookie, and return user profile.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended or inactive"
        )
        
    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    
    # Generate token & set cookie
    access_token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24
    )
    
    return user


@router.post("/logout")
def logout(response: Response):
    """
    Log out user by clearing the authentication cookie.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user profile and tenant details.
    """
    return current_user
