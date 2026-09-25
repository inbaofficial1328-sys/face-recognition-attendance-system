from fastapi import APIRouter, Depends

from backend.app.core.dependencies import require_roles
from backend.app.models.user import User

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_roles("ADMIN")),
):
    return {
        "message": "Welcome to the ADMIN dashboard",
        "user_id": current_user.id,
        "role": current_user.role,
    }