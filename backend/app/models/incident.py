from sqlalchemy import Column, String, Float, Text, Enum as SQLAlchemyEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.enums import IncidentType, IncidentStatus, Severity
import uuid

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    reporter_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    incident_type = Column(SQLAlchemyEnum(IncidentType), nullable=True)
    status = Column(SQLAlchemyEnum(IncidentStatus), default=IncidentStatus.REPORTED)
    severity = Column(SQLAlchemyEnum(Severity), nullable=True)
    
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    building = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    room = Column(String, nullable=True)
    
    estimated_response_time_minutes = Column(Float, nullable=True)
    immediate_guidance = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    reporter = relationship("User", back_populates="incidents_reported")
    agent_assignments = relationship("IncidentAgentAssignment", back_populates="incident")
    responder_assignments = relationship("ResponderAssignment", back_populates="incident")
    timeline = relationship("IncidentTimeline", back_populates="incident")
    ai_decisions = relationship("AIDecisionLog", back_populates="incident")
    
class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"))
    event = Column(String)
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    incident = relationship("Incident", back_populates="timeline")
