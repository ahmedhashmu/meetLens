"""Current user. Signup aur login frontend par Supabase karta hai."""
from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas import UserOut
from app.services.security import TokenUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def me(user: TokenUser = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email)
