import traceback

import app.crud as crud
import app.schemas as schemas
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.file_service import save_upload_file
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["users"])


@router.get("/api/users/me", response_model=schemas.UserResponse)
async def read_users_me(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = crud.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please sign in again.",
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session. Please sign in again.",
            )

        user = crud.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取用户信息错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load profile: {str(e)}",
        )


@router.patch("/api/users/me", response_model=schemas.UserResponse)
async def update_users_me(
    body: schemas.UserUpdate,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(token, db)
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return current_user
    if "username" in update_data and (update_data["username"] or "").strip() == "":
        del update_data["username"]
    try:
        updated = crud.update_user(db, current_user.id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated


@router.patch("/api/users/me/password")
async def change_password_me(
    body: schemas.PasswordChange,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(token, db)
    ok, err = crud.change_password(
        db, current_user.id, body.current_password, body.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "Could not update password.",
        )
    return {"message": "Password updated."}


@router.post("/api/users/me/avatar", response_model=schemas.UserResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(token, db)
    image_url = save_upload_file(file, current_user.id, file_type="avatar")
    crud.update_user(db, current_user.id, avatar_url=image_url)
    return crud.get_user_by_id(db, current_user.id)


