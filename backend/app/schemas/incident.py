from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.utils.enums import IncidentType, IncidentStatus, Severity

class IncidentCreate(BaseModel):
    title: Optional[str] = None
    description: str
    incident_type: Optional[IncidentType] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: Optional[Severity] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

class IncidentTimelineResponse(BaseModel):
    id: str
    event: str
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True

class IncidentResponse(BaseModel):
    id: str
    reporter_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    incident_type: Optional[IncidentType] = None
    status: IncidentStatus
    severity: Optional[Severity] = None
    location_name: Optional[str] = None
    estimated_response_time_minutes: Optional[float] = None
    immediate_guidance: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    timeline: List[IncidentTimelineResponse] = []

    class Config:
        from_attributes = True

class ReplanResponse(BaseModel):
    reason: str
    previous_plan: dict
    new_plan: dict
    changes: List[str]

class SimulateDisruptionRequest(BaseModel):
    type: str
    description: str
