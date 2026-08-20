from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.schemas.users import UserUpdate, UserOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.core.security import get_password_hash
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/users/", response_model=List[UserOut])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: User = Depends(RoleChecker([UserRole.system_admin]))
) -> Any:
    """
    Retrieve users. (Admin only)
    """
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/me", response_model=UserOut)
def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current logged in user.
    """
    return current_user

@router.get("/users/{id}", response_model=UserOut)
def read_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific user by id.
    """
    if current_user.id != id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{id}", response_model=UserOut)
def update_user(
    *,
    db: Session = Depends(get_db),
    id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update a user.
    """
    if current_user.id != id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
        
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Perform update
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        db_user.password_hash = get_password_hash(update_data["password"])
        del update_data["password"]
        
    # Admin checks on role or active updates
    if "role" in update_data and current_user.role != UserRole.system_admin:
        del update_data["role"]
    if "is_active" in update_data and current_user.role != UserRole.system_admin:
        del update_data["is_active"]
    if "is_verified" in update_data and current_user.role != UserRole.system_admin:
        del update_data["is_verified"]
        
    for field in update_data:
        setattr(db_user, field, update_data[field])
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="user",
        entity_id=db_user.id,
        ip_address=request.client.host if request.client else None
    )
    return db_user

@router.delete("/users/{id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete a user. (Admin only)
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="user",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "User deleted successfully"}
