from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.services.auth_service import (
    authenticate_user,
    generate_login_token,
)

from backend.app.schemas.password import (
    PasswordChangeRequest,
    PasswordChangeResponse,
)

from backend.app.services.password_service import (
    change_password,
    IncorrectPasswordError,
    PasswordReuseError,
)

from backend.app.core.dependencies import (
    get_db,
    get_current_user,
    require_password_changed,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        credentials.login_id,
        credentials.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return generate_login_token(user)


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(require_password_changed),
):
    return {
        "user_id": current_user.id,
        "login_id": current_user.login_id,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }

@router.post(
    "/change-password",
    response_model=PasswordChangeResponse,
)
def change_current_user_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        change_password(
            db,
            current_user,
            password_data,
        )

    except IncorrectPasswordError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except PasswordReuseError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return PasswordChangeResponse(
        message="Password changed successfully."
    )