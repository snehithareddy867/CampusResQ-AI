from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.enums import AssignmentStatus
import uuid

class IncidentAgentAssignment(Base):
    __tablename__ = "incident_agent_assignments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"))
    agent_type = Column(String)  # e.g., "MEDICAL_AGENT"
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    priority = Column(String, default="SUPPORT") # PRIMARY or SUPPORT
    status = Column(String, default="ACTIVE")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(String, nullable=True)

    incident = relationship("Incident", back_populates="agent_assignments")
    department = relationship("Department", back_populates="agent_assignments")

class ResponderAssignment(Base):
    __tablename__ = "responder_assignments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"))
    responder_id = Column(String, ForeignKey("users.id"))
    status = Column(SQLAlchemyEnum(AssignmentStatus), default=AssignmentStatus.PENDING)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    status_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    incident = relationship("Incident", back_populates="responder_assignments")
    responder = relationship("User", back_populates="assignments")
