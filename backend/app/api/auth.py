from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.user import UserResponse, UserProfileUpdate
from app.models.user import User
from app.models.department import Department
from app.core.security import get_password_hash, verify_password, create_access_token
from app.utils.enums import DepartmentName

router = APIRouter()

@router.post("/register", response_model=dict)
def register(user_in: UserRegister, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        name=user_in.name,
        campus_id=user_in.campus_id,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        phone_number=user_in.phone_number,
        role=user_in.role
    )
    
    if user_in.department != DepartmentName.NONE:
        dept = db.query(Department).filter(Department.name == user_in.department).first()
        if dept:
            db_user.department_id = dept.id
            
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(subject=db_user.id)
    
    dept_name = db_user.department.name.value if db_user.department else DepartmentName.NONE.value
    
    return {
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "department": dept_name
        },
        "token": access_token
    }

@router.post("/login", response_model=dict)
def login(db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = create_access_token(subject=user.id)
    dept_name = user.department.name.value if user.department else DepartmentName.NONE.value
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "department": dept_name
        },
        "token": access_token
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(deps.get_current_active_user)):
    user_resp = UserResponse.from_orm(current_user)
    user_resp.department = current_user.department.name.value if current_user.department else None
    return user_resp

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_in: UserProfileUpdate, 
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if profile_in.name is not None:
        current_user.name = profile_in.name
    if profile_in.phone_number is not None:
        current_user.phone_number = profile_in.phone_number
        
    if profile_in.department is not None:
        if profile_in.department == DepartmentName.NONE:
            current_user.department_id = None
        else:
            dept = db.query(Department).filter(Department.name == profile_in.department).first()
            if dept:
                current_user.department_id = dept.id
                
    db.commit()
    db.refresh(current_user)
    
    user_resp = UserResponse.from_orm(current_user)
    user_resp.department = current_user.department.name.value if current_user.department else None
    return user_resp
    
@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
