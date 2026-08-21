from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.department import DepartmentResponse, DepartmentDashboardResponse
from app.schemas.incident import IncidentResponse
from app.schemas.user import UserResponse
from app.models.user import User
from app.services.department_service import DepartmentService

router = APIRouter()

@router.get("/me", response_model=DepartmentDashboardResponse)
def get_my_department(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    if not current_user.department_id:
        raise HTTPException(status_code=400, detail="User is not assigned to any department")
    
    service = DepartmentService(db)
    return service.get_department_dashboard(current_user.department_id)

@router.get("/incidents", response_model=List[IncidentResponse])
def get_department_incidents(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    if not current_user.department_id:
        raise HTTPException(status_code=400, detail="User is not assigned to any department")
        
    service = DepartmentService(db)
    return service.get_department_incidents(current_user.department_id)

@router.get("/members", response_model=List[UserResponse])
def get_department_members(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    if not current_user.department_id:
        raise HTTPException(status_code=400, detail="User is not assigned to any department")
        
    service = DepartmentService(db)
    return service.get_department_members(current_user.department_id)
