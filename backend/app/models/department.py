from sqlalchemy import Column, String, Integer, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.enums import DepartmentName
import uuid

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(SQLAlchemyEnum(DepartmentName), unique=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="ACTIVE")
    location = Column(String, nullable=True)
    contact_information = Column(String, nullable=True)

    members = relationship("User", back_populates="department")
    agent_assignments = relationship("IncidentAgentAssignment", back_populates="department")
