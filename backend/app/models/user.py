from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    campus_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(String, nullable=True)
    role = Column(String, default="USER")
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="members")
    incidents_reported = relationship("Incident", back_populates="reporter")
    assignments = relationship("ResponderAssignment", back_populates="responder")
    notifications = relationship("Notification", back_populates="user")
