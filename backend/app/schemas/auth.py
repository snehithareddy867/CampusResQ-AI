from pydantic import BaseModel, EmailStr
from typing import Optional
from app.utils.enums import DepartmentName

class UserRegister(BaseModel):
    name: str
    campus_id: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    role: str = "USER"
    department: DepartmentName = DepartmentName.NONE

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
