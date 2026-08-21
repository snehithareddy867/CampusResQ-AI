from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.incident import IncidentCreate, IncidentResponse, ReplanResponse, SimulateDisruptionRequest
from app.models.user import User
from app.services.incident_service import IncidentService
from app.agents.orchestrator import AIOrchestrator
from typing import List
from app.core.database import get_db

router = APIRouter()

@router.post("", response_model=IncidentResponse)
def report_emergency(
    incident_in: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = IncidentService(db)
    incident = service.create_incident(incident_in, current_user.id)
    
    # Process asynchronously to return quickly
    orchestrator = AIOrchestrator(db)
    background_tasks.add_task(orchestrator.process_incident, incident.id)
    
    return incident

@router.get("", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    return service.get_all_incidents()

@router.get("/my", response_model=List[IncidentResponse])
def get_my_incidents(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    return service.get_incidents_by_reporter(current_user.id)

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    incident = service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/{incident_id}/replan", response_model=ReplanResponse)
@router.post("/{incident_id}/simulate-disruption", response_model=ReplanResponse)
def replan_incident(
    incident_id: str,
    background_tasks: BackgroundTasks,
    request: SimulateDisruptionRequest = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # This simulates receiving new info that necessitates replanning
    orchestrator = AIOrchestrator(db)
    
    reason = request.description if request else "Main route is blocked"
    
    # Perform synchronous replanning for the demo to return the response immediately
    # In a real system, you might want this to run async too, but the hackathon requires replan return data
    replan_result = orchestrator.replan_incident_sync(incident_id, reason)
    
    if not replan_result:
        raise HTTPException(status_code=400, detail="Could not replan this incident")
        
    return replan_result

@router.post("/{incident_id}/accept")
def accept_incident(incident_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    result = service.accept_incident(incident_id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Could not accept incident")
    return {"status": "success", "message": "Incident accepted"}

@router.post("/{incident_id}/start")
def start_incident(incident_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    result = service.start_incident(incident_id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Could not start incident")
    return {"status": "success", "message": "Response in progress"}

@router.post("/{incident_id}/resolve")
def resolve_incident(incident_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    service = IncidentService(db)
    result = service.resolve_incident(incident_id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Could not resolve incident")
    return {"status": "success", "message": "Incident resolved"}
