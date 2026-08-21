import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.ai.schemas import LLMIncidentAnalysis, LLMReplanResult
from app.utils.enums import IncidentType, Severity, DepartmentName

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        
        # Initialize OpenAI client if key is available
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI library not installed. Using mock fallback.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def analyze_incident(self, description: str, location: str) -> LLMIncidentAnalysis:
        if not self.client:
            return self._mock_analyze(description, location)
            
        try:
            from app.ai.prompts import ANALYZE_INCIDENT_PROMPT
            
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ANALYZE_INCIDENT_PROMPT},
                    {"role": "user", "content": f"Incident Description: {description}\nLocation: {location}"}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Use Pydantic to validate and coerce enum types
            analysis = LLMIncidentAnalysis(**result)
            return analysis
        except Exception as e:
            logger.error(f"LLM API failed: {e}")
            return self._mock_analyze(description, location)

    def replan_incident(self, current_state: dict, new_information: str) -> LLMReplanResult:
        if not self.client:
            return self._mock_replan(current_state, new_information)
            
        try:
            from app.ai.prompts import REPLAN_INCIDENT_PROMPT
            
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": REPLAN_INCIDENT_PROMPT},
                    {"role": "user", "content": f"Current State: {json.dumps(current_state)}\nNew Information: {new_information}"}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            replan = LLMReplanResult(**result)
            return replan
        except Exception as e:
            logger.error(f"LLM API replan failed: {e}")
            return self._mock_replan(current_state, new_information)

    def _mock_analyze(self, description: str, location: str) -> LLMIncidentAnalysis:
        desc_lower = description.lower()
        
        # Simple heuristic fallback
        incident_type = IncidentType.OTHER
        severity = Severity.MEDIUM
        primary = DepartmentName.SECURITY
        support = []
        guidance = ["Stay calm.", "Wait for responders."]
        
        if "fire" in desc_lower or "smoke" in desc_lower:
            incident_type = IncidentType.FIRE
            severity = Severity.CRITICAL
            primary = DepartmentName.FACILITIES
            support = [DepartmentName.SECURITY, DepartmentName.MEDICAL]
            guidance = ["Evacuate the area immediately.", "Do not use elevators.", "Stay low if there is smoke."]
        elif "medical" in desc_lower or "collapse" in desc_lower or "hurt" in desc_lower:
            incident_type = IncidentType.MEDICAL
            severity = Severity.HIGH
            primary = DepartmentName.MEDICAL
            support = [DepartmentName.SECURITY]
            guidance = ["Do not move the person unless in immediate danger.", "Keep the area clear.", "Wait for medical team."]
        elif "fight" in desc_lower or "weapon" in desc_lower:
            incident_type = IncidentType.VIOLENCE
            severity = Severity.CRITICAL
            primary = DepartmentName.SECURITY
            support = [DepartmentName.MEDICAL]
            guidance = ["Move to a safe location.", "Do not engage.", "Wait for security."]
            
        return LLMIncidentAnalysis(
            incident_type=incident_type,
            severity=severity,
            summary=f"Mock AI summary for: {description[:50]}...",
            primary_department=primary,
            supporting_departments=support,
            required_actions=[f"Dispatch {primary.value}", "Secure area"],
            immediate_guidance=guidance,
            confidence_score=0.85,
            reasoning=f"Mock fallback reasoning selected {primary.value} based on keywords."
        )

    def _mock_replan(self, current_state: dict, new_information: str) -> LLMReplanResult:
        return LLMReplanResult(
            reason="Mock replanning triggered by new info: " + new_information,
            changes=["ETA increased due to new information", "Alternative route required"],
            reasoning="New conditions require adjustment of response parameters."
        )
