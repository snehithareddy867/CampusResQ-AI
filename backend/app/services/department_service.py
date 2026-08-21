from sqlalchemy.orm import Session
from app.models.department import Department
from app.models.user import User
from app.models.incident import Incident
from app.models.assignment import ResponderAssignment, IncidentAgentAssignment
from app.utils.enums import IncidentStatus, AssignmentStatus, DepartmentName

class DepartmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_department_dashboard(self, department_id: str):
        dept = self.db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            return None
            
        total_members = self.db.query(User).filter(User.department_id == department_id).count()
        busy_responders = self.db.query(ResponderAssignment).join(User).filter(
            User.department_id == department_id,
            ResponderAssignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED, AssignmentStatus.DISPATCHED])
        ).count()
        
        # Get active incidents assigned to this department
        incidents_query = self.db.query(Incident).join(IncidentAgentAssignment).filter(
            IncidentAgentAssignment.department_id == department_id
        )
        
        active_incidents = incidents_query.filter(
            Incident.status.in_([IncidentStatus.ACKNOWLEDGED, IncidentStatus.IN_PROGRESS, IncidentStatus.DISPATCHING])
        ).count()
        
        incoming_incidents = incidents_query.filter(
            Incident.status.in_([IncidentStatus.REPORTED, IncidentStatus.ANALYZING])
        ).count()
        
        resolved_incidents = incidents_query.filter(Incident.status == IncidentStatus.RESOLVED).count()

        return {
            "department": dept.name,
            "available_responders": total_members - busy_responders,
            "busy_responders": busy_responders,
            "incoming_incidents": incoming_incidents,
            "active_incidents": active_incidents,
            "resolved_incidents": resolved_incidents
        }

    def get_department_incidents(self, department_id: str):
        # Return all incidents that have been routed to this department
        return self.db.query(Incident).join(IncidentAgentAssignment).filter(
            IncidentAgentAssignment.department_id == department_id
        ).order_by(Incident.created_at.desc()).all()

    def get_department_members(self, department_id: str):
        return self.db.query(User).filter(User.department_id == department_id).all()
