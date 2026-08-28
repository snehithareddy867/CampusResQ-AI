"""Pydantic models for CampusResQ AI."""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


def uid() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Enums ----------
class Role(str, Enum):
    STUDENT = "student"
    RESPONDER = "responder"
    DEPT_PERSONNEL = "dept_personnel"
    DEPT_ADMIN = "dept_admin"
    HEAD_ADMIN = "head_admin"


class Department(str, Enum):
    MEDICAL = "medical"
    FIRE_SAFETY = "fire_safety"
    SECURITY = "security"
    ELECTRICAL = "electrical"
    CONSTRUCTION = "construction"
    FACILITIES = "facilities"
    ENVIRONMENTAL = "environmental"
    TRANSPORT = "transport"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    CLASSIFIED = "classified"
    FRAUD_REVIEW = "fraud_review"
    ASSIGNING = "assigning"
    WAITING_FOR_ACCEPTANCE = "waiting_for_acceptance"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    RESOLVED = "resolved"
    RESOLUTION_PENDING = "resolution_pending"
    REOPENED = "reopened"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class FraudLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.STUDENT
    department: Optional[Department] = None
    phone: Optional[str] = None
    registration_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: Role
    department: Optional[Department] = None
    phone: Optional[str] = None
    available: bool = True
    created_at: str


# ---------- Incident ----------
class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None


class Evidence(BaseModel):
    kind: str  # image | audio | video
    data_url: Optional[str] = None  # base64 for demo (small)
    filename: Optional[str] = None


class ReportRequest(BaseModel):
    description: str
    location: Location
    category_hint: Optional[str] = None
    evidence: List[Evidence] = []
    is_sos: bool = False
    client_op_id: Optional[str] = None  # for offline dedupe
    voice_transcript: Optional[str] = None


class AIAnalysis(BaseModel):
    category: str
    department: Department
    priority: Priority
    confidence: float
    reason: str
    safety_instructions: List[str] = []


class FraudAnalysis(BaseModel):
    risk_score: float
    risk_level: FraudLevel
    reasons: List[str]
    recommended_action: str


class Incident(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=uid)
    reporter_id: str
    reporter_name: str
    description: str
    location: Location
    category_hint: Optional[str] = None
    is_sos: bool = False
    evidence: List[Evidence] = []
    status: IncidentStatus = IncidentStatus.SUBMITTED
    ai_analysis: Optional[AIAnalysis] = None
    fraud_analysis: Optional[FraudAnalysis] = None
    assigned_department: Optional[Department] = None
    assigned_responder_id: Optional[str] = None
    assigned_responder_name: Optional[str] = None
    responder_location: Optional[Location] = None
    eta_minutes: Optional[int] = None
    priority: Optional[Priority] = None
    reported_at: str = Field(default_factory=now_iso)
    classified_at: Optional[str] = None
    assigned_at: Optional[str] = None
    accepted_at: Optional[str] = None
    en_route_at: Optional[str] = None
    arrived_at: Optional[str] = None
    resolved_at: Optional[str] = None
    reopened_at: Optional[str] = None
    escalated: bool = False
    client_op_id: Optional[str] = None
    timeline: List[dict] = []
    reporter_confirmed_safe: bool = False
    reporter_safe_at: Optional[str] = None
    responder_marked_complete: bool = False
    responder_complete_at: Optional[str] = None
    sos_broadcast_ids: List[str] = []
    sos_radius_m: Optional[int] = None
    distance_km: Optional[float] = None
    location_history: List[dict] = []
    voice_transcript: Optional[str] = None


class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=uid)
    user_id: str
    type: str
    message: str
    incident_id: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    created_at: str = Field(default_factory=now_iso)
    read_at: Optional[str] = None


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=uid)
    actor_id: str
    actor_name: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    prev_value: Optional[Any] = None
    new_value: Optional[Any] = None
    created_at: str = Field(default_factory=now_iso)


class ResponderAcceptRequest(BaseModel):
    incident_id: str
    eta_minutes: int
    current_location: Optional[Location] = None


class ResponderRejectRequest(BaseModel):
    incident_id: str
    reason: Optional[str] = None


class ResponderLocationUpdate(BaseModel):
    incident_id: str
    location: Location
    eta_minutes: Optional[int] = None
    heading: Optional[float] = None  # degrees 0-360
    speed_mps: Optional[float] = None  # meters per second
    accuracy: Optional[float] = None  # meters


class StatusUpdateRequest(BaseModel):
    status: IncidentStatus
    note: Optional[str] = None


class AdminOverrideRequest(BaseModel):
    department: Optional[Department] = None
    priority: Optional[Priority] = None
    responder_id: Optional[str] = None
    fraud_decision: Optional[str] = None  # approve|dismiss|escalate
    note: Optional[str] = None


class AssistantChatRequest(BaseModel):
    incident_id: Optional[str] = None
    message: str
    session_id: Optional[str] = None


# ---------- Teams / Backup ----------
class TeamMember(BaseModel):
    user_id: str
    name: str
    role_title: Optional[str] = None
    skills: List[str] = []


class Team(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=uid)
    department: Department
    kind: str = "primary"  # primary | backup
    name: str
    members: List[TeamMember] = []
    acceptance_timeout_sec: int = 60
    created_at: str = Field(default_factory=now_iso)


class TeamCreateRequest(BaseModel):
    department: Department
    kind: str = "primary"
    name: str
    member_ids: List[str] = []
    acceptance_timeout_sec: int = 60


class TeamUpdateRequest(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    member_ids: Optional[List[str]] = None
    acceptance_timeout_sec: Optional[int] = None


class ResponderSkillsUpdate(BaseModel):
    user_id: str
    skills: List[str]


# ---------- Push ----------
class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict  # {p256dh, auth}


# ---------- Forensics ----------
class MediaForensics(BaseModel):
    verdict: str  # authentic | suspicious | likely_manipulated | insufficient_data
    confidence: float
    reasons: List[str]
    per_item: List[dict] = []
