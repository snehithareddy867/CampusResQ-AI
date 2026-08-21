from sqlalchemy.orm import Session
from app.models.incident import Incident, IncidentTimeline
from app.models.department import Department
from app.models.user import User
from app.models.assignment import IncidentAgentAssignment, ResponderAssignment
from app.models.ai_decision import AIDecisionLog
from app.utils.enums import IncidentStatus, AssignmentStatus, DepartmentName, NotificationType, Severity
from app.ai.llm_client import LLMClient
from app.services.eta_service import ETAService
from app.services.notification_service import NotificationService
import logging
import asyncio
from app.core.websocket import manager

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()
        self.eta_service = ETAService()
        self.notification_service = NotificationService(db)

    async def _broadcast(self, incident_id: str, event: str, message: str, **kwargs):
        from datetime import datetime
        payload = {
            "event": event,
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": message,
                **kwargs
            }
        }
        await manager.broadcast_to_incident(incident_id, payload)

    def _add_timeline(self, incident_id: str, event: str, desc: str):
        tl = IncidentTimeline(incident_id=incident_id, event=event, description=desc)
        self.db.add(tl)
        self.db.commit()

    def _log_decision(self, incident_id: str, agent: str, dec_type: str, decision: str, reasoning: str):
        log = AIDecisionLog(
            incident_id=incident_id,
            agent=agent,
            decision_type=dec_type,
            decision=decision,
            reasoning_summary=reasoning
        )
        self.db.add(log)
        self.db.commit()

    async def process_incident(self, incident_id: str):
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return

        # 1. Start Analysis
        incident.status = IncidentStatus.ANALYZING
        self.db.commit()
        self._add_timeline(incident.id, "AI_ANALYSIS_STARTED", "AI Orchestrator is analyzing the incident")
        await self._broadcast(incident_id, "AI_ANALYSIS_STARTED", "AI is analyzing the situation")

        # 2. Analyze via LLM
        desc = f"Title: {incident.title}\nDesc: {incident.description}"
        analysis = self.llm.analyze_incident(desc, incident.location_name or "Unknown")

        # 3. Update Incident with Analysis
        incident.incident_type = analysis.incident_type
        incident.severity = analysis.severity
        incident.immediate_guidance = "\n".join(analysis.immediate_guidance)
        self.db.commit()

        self._log_decision(
            incident_id, 
            "ORCHESTRATOR", 
            "CLASSIFICATION_AND_ROUTING",
            f"Type: {analysis.incident_type}, Primary: {analysis.primary_department}",
            analysis.reasoning
        )

        self._add_timeline(incident.id, "AI_ANALYSIS_COMPLETED", f"Classified as {analysis.incident_type.value} - {analysis.severity.value}")
        await self._broadcast(incident_id, "AI_ANALYSIS_COMPLETED", f"Incident classified. Required departments identified.")

        # 4. Activate Agents (Assign Departments)
        self._assign_department(incident_id, analysis.primary_department, "PRIMARY")
        for dept in analysis.supporting_departments:
            if dept != analysis.primary_department:
                self._assign_department(incident_id, dept, "SUPPORT")

        if analysis.severity == Severity.CRITICAL:
            incident.status = IncidentStatus.WAITING_FOR_APPROVAL
            self.db.commit()
            self._add_timeline(incident.id, "WAITING_FOR_APPROVAL", "Critical incident requires Command Center approval before dispatch")
            await self._broadcast(incident_id, "STATUS_UPDATE", "Waiting for command center approval")
            return
            
        incident.status = IncidentStatus.DISPATCHING
        self.db.commit()
        
        # 5. Find Responders
        # In a full system, separate agents would run here. 
        # For hackathon demo, orchestrator orchestrates it.
        await self._find_and_notify_responders(incident_id, analysis.primary_department)
        
        # 6. Notify Reporter
        if incident.reporter_id:
            self.notification_service.create_notification(
                incident.reporter_id,
                NotificationType.SAFETY_GUIDANCE,
                "Immediate Safety Guidance",
                incident.immediate_guidance,
                incident.id
            )

        # 7. Calculate ETA
        eta = self.eta_service.calculate_eta(incident.location_name, analysis.primary_department.value)
        incident.estimated_response_time_minutes = eta
        self.db.commit()
        
        self._add_timeline(incident.id, "ETA_UPDATED", f"Estimated response time: {eta} minutes")
        await self._broadcast(incident_id, "ETA_UPDATED", f"Responders estimated in {eta} minutes", eta_minutes=eta)

    def _assign_department(self, incident_id: str, dept_name: DepartmentName, priority: str):
        dept = self.db.query(Department).filter(Department.name == dept_name).first()
        if not dept:
            return
            
        assignment = IncidentAgentAssignment(
            incident_id=incident_id,
            agent_type=f"{dept_name.value}_AGENT",
            department_id=dept.id,
            priority=priority
        )
        self.db.add(assignment)
        self.db.commit()
        self._add_timeline(incident_id, "DEPARTMENT_ASSIGNED", f"{dept_name.value} Department has been assigned to respond")

    async def _find_and_notify_responders(self, incident_id: str, primary_dept: DepartmentName):
        dept = self.db.query(Department).filter(Department.name == primary_dept).first()
        if not dept:
            return
            
        # Simple selection: find first available responder in department
        available_responders = self.db.query(User).filter(User.department_id == dept.id).all()
        # In a real app, you'd check ResponderAssignment for busy status
        
        if available_responders:
            responder = available_responders[0] # Pick first for demo
            
            ra = ResponderAssignment(
                incident_id=incident_id,
                responder_id=responder.id
            )
            self.db.add(ra)
            self.db.commit()
            
            self._add_timeline(incident_id, "RESPONDER_NOTIFIED", f"Responder from {primary_dept.value} notified")
            
            self.notification_service.create_notification(
                responder.id,
                NotificationType.INCIDENT_RECEIVED,
                "New Incident Assignment",
                "You have been assigned to a new incident.",
                incident_id
            )

    def replan_incident_sync(self, incident_id: str, reason: str = "Main route is blocked"):
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None
            
        incident.status = IncidentStatus.REPLANNING
        self.db.commit()
        self._add_timeline(incident.id, "REPLANNING_STARTED", "New information received. AI Orchestrator is replanning.")
        
        # Mock synchronous broadcast - real app uses async loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Cannot use run_until_complete inside running loop easily without nested loops, 
                # so we just add task
                loop.create_task(self._broadcast(incident_id, "REPLANNING_STARTED", "Replanning in progress due to changing conditions"))
        except:
            pass

        replan = self.llm.replan_incident({}, reason)
        
        new_eta = self.eta_service.replan_eta(incident.estimated_response_time_minutes or 5.0)
        incident.estimated_response_time_minutes = new_eta
        incident.status = IncidentStatus.IN_PROGRESS
        self.db.commit()

        self._log_decision(
            incident_id,
            "ORCHESTRATOR",
            "REPLANNING",
            "Updated ETA and response strategy",
            replan.reasoning
        )
        
        self._add_timeline(incident.id, "REPLANNING_COMPLETED", f"Plan updated: {replan.changes[0]}")
        self._add_timeline(incident.id, "ETA_UPDATED", f"New estimated response time: {new_eta} minutes")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._broadcast(incident_id, "REPLANNING_COMPLETED", "Replanning completed", eta_minutes=new_eta, changes=replan.changes))
        except:
            pass

        return {
            "reason": replan.reason,
            "previous_plan": {},
            "new_plan": {},
            "changes": replan.changes
        }
