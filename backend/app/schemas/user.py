from pydantic import BaseModel, EmailStr
from typing import Optional
from app.utils.enums import DepartmentName

class UserBase(BaseModel):
    name: str
    campus_id: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: str

class UserCreate(UserBase):
    password: str
    department: DepartmentName = DepartmentName.NONE

from pydantic import BaseModel, EmailStr, field_validator

class UserResponse(UserBase):
    id: str
    department: Optional[str] = None

    @field_validator('department', mode='before')
    @classmethod
    def extract_department_name(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if hasattr(v, 'name'):
            return v.name.value if hasattr(v.name, 'value') else v.name
        return str(v)

    class Config:
        from_attributes = True
        
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[DepartmentName] = None
