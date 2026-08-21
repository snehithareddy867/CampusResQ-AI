from pydantic import BaseModel
from typing import List, Optional
from app.utils.enums import IncidentType, Severity, DepartmentName

class LLMIncidentAnalysis(BaseModel):
    incident_type: IncidentType
    severity: Severity
    summary: str
    primary_department: DepartmentName
    supporting_departments: List[DepartmentName]
    required_actions: List[str]
    immediate_guidance: List[str]
    confidence_score: float
    reasoning: str

class LLMReplanResult(BaseModel):
    reason: str
    changes: List[str]
    new_primary_department: Optional[DepartmentName] = None
    new_supporting_departments: Optional[List[DepartmentName]] = None
    reasoning: str
