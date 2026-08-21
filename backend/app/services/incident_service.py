from sqlalchemy.orm import Session
from app.models.user import User
from app.models.incident import Incident, IncidentTimeline
from app.models.assignment import ResponderAssignment, IncidentAgentAssignment
from app.schemas.incident import IncidentCreate
from app.utils.enums import IncidentStatus, AssignmentStatus
from app.core.websocket import manager
import asyncio

class IncidentService:
    def __init__(self, db: Session):
        self.db = db

    def create_incident(self, incident_in: IncidentCreate, reporter_id: str) -> Incident:
        db_incident = Incident(
            reporter_id=reporter_id,
            title=incident_in.title,
            description=incident_in.description,
            incident_type=incident_in.incident_type,
            location_name=incident_in.location_name,
            latitude=incident_in.latitude,
            longitude=incident_in.longitude,
            severity=incident_in.severity,
            building=incident_in.building,
            floor=incident_in.floor,
            room=incident_in.room,
            status=IncidentStatus.REPORTED
        )
        self.db.add(db_incident)
        self.db.commit()
        self.db.refresh(db_incident)
        
        self.add_timeline_event(db_incident.id, "INCIDENT_CREATED", "Emergency reported")
        return db_incident

    def add_timeline_event(self, incident_id: str, event: str, description: str):
        timeline = IncidentTimeline(
            incident_id=incident_id,
            event=event,
            description=description
        )
        self.db.add(timeline)
        self.db.commit()
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                from datetime import datetime
                loop.create_task(manager.broadcast_to_incident(incident_id, {
                    "event": event,
                    "incident_id": incident_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "message": description
                    }
                }))
        except:
            pass

    def get_all_incidents(self):
        return self.db.query(Incident).order_by(Incident.created_at.desc()).all()

    def get_incidents_by_reporter(self, reporter_id: str):
        return self.db.query(Incident).filter(Incident.reporter_id == reporter_id).order_by(Incident.created_at.desc()).all()

    def get_incident(self, incident_id: str):
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def accept_incident(self, incident_id: str, user_or_id) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False
            
        if isinstance(user_or_id, str):
            current_user = self.db.query(User).filter(User.id == user_or_id).first()
        else:
            current_user = user_or_id
            
        if not current_user:
            return False
            
        if not current_user.department_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Standard users without a department cannot accept responder assignments.")
            
        agent_assignment = self.db.query(IncidentAgentAssignment).filter(
            IncidentAgentAssignment.incident_id == incident_id,
            IncidentAgentAssignment.department_id == current_user.department_id
        ).first()
        
        existing_resp_assignment = self.db.query(ResponderAssignment).filter(
            ResponderAssignment.incident_id == incident_id,
            ResponderAssignment.responder_id == current_user.id
        ).first()
        
        if not agent_assignment and not existing_resp_assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="User's department is not assigned to this incident.")
            
        if existing_resp_assignment:
            existing_resp_assignment.status = AssignmentStatus.ACCEPTED
        else:
            new_assignment = ResponderAssignment(
                incident_id=incident_id,
                responder_id=current_user.id,
                status=AssignmentStatus.ACCEPTED
            )
            self.db.add(new_assignment)
            
        if incident.status in [IncidentStatus.DISPATCHING, IncidentStatus.REPORTED, IncidentStatus.ANALYZING, IncidentStatus.WAITING_FOR_APPROVAL]:
            incident.status = IncidentStatus.ACKNOWLEDGED
            
        self.db.commit()
        self.add_timeline_event(incident_id, "RESPONDER_ACCEPTED", f"Responder has accepted the assignment")
        return True
        
    def start_incident(self, incident_id: str, user_or_id) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False
            
        if isinstance(user_or_id, str):
            current_user = self.db.query(User).filter(User.id == user_or_id).first()
        else:
            current_user = user_or_id
            
        if not current_user:
            return False
            
        if not current_user.department_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Standard users without a department cannot start response.")
            
        agent_assignment = self.db.query(IncidentAgentAssignment).filter(
            IncidentAgentAssignment.incident_id == incident_id,
            IncidentAgentAssignment.department_id == current_user.department_id
        ).first()
        
        existing_resp_assignment = self.db.query(ResponderAssignment).filter(
            ResponderAssignment.incident_id == incident_id,
            ResponderAssignment.responder_id == current_user.id
        ).first()
        
        if not agent_assignment and not existing_resp_assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="User's department is not assigned to this incident.")
            
        if existing_resp_assignment:
            existing_resp_assignment.status = AssignmentStatus.DISPATCHED
        else:
            new_assignment = ResponderAssignment(
                incident_id=incident_id,
                responder_id=current_user.id,
                status=AssignmentStatus.DISPATCHED
            )
            self.db.add(new_assignment)
            
        incident.status = IncidentStatus.IN_PROGRESS
        self.db.commit()
        self.add_timeline_event(incident_id, "RESPONDER_DISPATCHED", "Responder is on the way")
        return True

    def resolve_incident(self, incident_id: str, user_or_id) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False
            
        if isinstance(user_or_id, str):
            current_user = self.db.query(User).filter(User.id == user_or_id).first()
        else:
            current_user = user_or_id
            
        if not current_user:
            return False
            
        if not current_user.department_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Standard users without a department cannot resolve incidents.")
            
        agent_assignment = self.db.query(IncidentAgentAssignment).filter(
            IncidentAgentAssignment.incident_id == incident_id,
            IncidentAgentAssignment.department_id == current_user.department_id
        ).first()
        
        existing_resp_assignment = self.db.query(ResponderAssignment).filter(
            ResponderAssignment.incident_id == incident_id,
            ResponderAssignment.responder_id == current_user.id
        ).first()
        
        if not agent_assignment and not existing_resp_assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="User's department is not assigned to this incident.")
            
        if existing_resp_assignment:
            existing_resp_assignment.status = AssignmentStatus.COMPLETED
            
        incident.status = IncidentStatus.RESOLVED
        
        # Close agent assignments
        agents = self.db.query(IncidentAgentAssignment).filter(IncidentAgentAssignment.incident_id == incident_id).all()
        for agent in agents:
            agent.status = "COMPLETED"
            
        self.db.commit()
        self.add_timeline_event(incident_id, "INCIDENT_RESOLVED", "Incident has been resolved")
        return True
