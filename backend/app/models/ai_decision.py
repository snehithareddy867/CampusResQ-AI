from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class AIDecisionLog(Base):
    __tablename__ = "ai_decision_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"))
    agent = Column(String)
    decision_type = Column(String)
    input_summary = Column(Text, nullable=True)
    decision = Column(Text)
    reasoning_summary = Column(Text)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="ai_decisions")
