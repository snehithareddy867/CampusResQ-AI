from pydantic import BaseModel
from typing import Optional, List
from app.utils.enums import DepartmentName
from app.schemas.user import UserResponse

class DepartmentBase(BaseModel):
    name: DepartmentName
    description: Optional[str] = None
    status: str = "ACTIVE"
    location: Optional[str] = None
    contact_information: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: str

    class Config:
        from_attributes = True

class DepartmentDashboardResponse(BaseModel):
    department: DepartmentName
    available_responders: int
    busy_responders: int
    incoming_incidents: int
    active_incidents: int
    resolved_incidents: int
