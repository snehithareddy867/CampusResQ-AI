from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.models.incident import Incident, IncidentTimeline
from app.utils.enums import IncidentStatus
from app.agents.orchestrator import AIOrchestrator
from app.schemas.incident import IncidentResponse
from typing import List

router = APIRouter()

@router.get("/overview")
def get_overview(db: Session = Depends(deps.get_db)):
    total = db.query(Incident).count()
    active = db.query(Incident).filter(Incident.status.in_([IncidentStatus.REPORTED, IncidentStatus.IN_PROGRESS, IncidentStatus.DISPATCHING, IncidentStatus.WAITING_FOR_APPROVAL])).count()
    resolved = db.query(Incident).filter(Incident.status == IncidentStatus.RESOLVED).count()
    
    return {
        "total_incidents": total,
        "active_incidents": active,
        "resolved_incidents": resolved
    }

@router.get("/incidents", response_model=List[IncidentResponse])
def get_all_incidents(db: Session = Depends(deps.get_db)):
    return db.query(Incident).order_by(Incident.created_at.desc()).all()

@router.get("/active", response_model=List[IncidentResponse])
def get_active_incidents(db: Session = Depends(deps.get_db)):
    return db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.REPORTED, IncidentStatus.IN_PROGRESS, IncidentStatus.DISPATCHING, IncidentStatus.WAITING_FOR_APPROVAL])
    ).order_by(Incident.created_at.desc()).all()

@router.get("/analytics")
def get_analytics(db: Session = Depends(deps.get_db)):
    # Basic analytics mock
    return {
        "average_response_time": 4.2,
        "critical_incidents": db.query(Incident).filter(Incident.severity == "CRITICAL").count()
    }

@router.post("/incidents/{incident_id}/approve-plan")
async def approve_plan(incident_id: str, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident or incident.status != IncidentStatus.WAITING_FOR_APPROVAL:
        raise HTTPException(status_code=400, detail="Incident not waiting for approval")
        
    incident.status = IncidentStatus.DISPATCHING
    db.commit()
    
    tl = IncidentTimeline(incident_id=incident_id, event="APPROVAL_GRANTED", description="Command Center approved the response plan")
    db.add(tl)
    db.commit()
    
    orchestrator = AIOrchestrator(db)
    await orchestrator._broadcast(incident_id, "STATUS_UPDATE", "Plan approved. Dispatching responders.")
    
    # In a real app we'd get the primary dept from the agent assignment table.
    # We will simulate finding the first primary assignment
    from app.models.assignment import IncidentAgentAssignment
    primary_assignment = db.query(IncidentAgentAssignment).filter(
        IncidentAgentAssignment.incident_id == incident_id,
        IncidentAgentAssignment.priority == "PRIMARY"
    ).first()
    
    if primary_assignment:
        from app.utils.enums import DepartmentName
        try:
            dept_name = DepartmentName(primary_assignment.agent_type.replace("_AGENT", ""))
            background_tasks.add_task(orchestrator._find_and_notify_responders, incident_id, dept_name)
        except Exception:
            pass
            
    return {"status": "success", "message": "Plan approved"}

@router.post("/incidents/{incident_id}/reject-plan")
async def reject_plan(incident_id: str, db: Session = Depends(deps.get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident or incident.status != IncidentStatus.WAITING_FOR_APPROVAL:
        raise HTTPException(status_code=400, detail="Incident not waiting for approval")
        
    incident.status = IncidentStatus.CANCELLED
    db.commit()
    
    tl = IncidentTimeline(incident_id=incident_id, event="APPROVAL_REJECTED", description="Command Center rejected the response plan")
    db.add(tl)
    db.commit()
    
    orchestrator = AIOrchestrator(db)
    await orchestrator._broadcast(incident_id, "STATUS_UPDATE", "Plan rejected by Command Center")
    
    return {"status": "success", "message": "Plan rejected"}

@router.post("/incidents/{incident_id}/modify-plan")
def modify_plan(incident_id: str, new_plan: dict, db: Session = Depends(deps.get_db)):
    # Mock modify plan for hackathon
    return {"status": "success", "message": "Plan modified and dispatched"}
