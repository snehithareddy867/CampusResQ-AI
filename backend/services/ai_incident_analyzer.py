"""Phase 1 AI incident analysis with rule-based fallback.

Reuses the existing Emergent/Claude client in agents.py. Never hard-codes keys.
"""
import logging
from typing import Optional

import agents
from services.team_router import ALLOWED_CATEGORIES, normalize_category, route_category

LOG = logging.getLogger("ai_incident_analyzer")

ALLOWED_SEVERITY = ("low", "medium", "high", "critical")

ANALYZER_SYSTEM = """You are the Incident Analysis Agent for CampusResQ AI.
Given an incident description (and optional SOS flag / category hint), output STRICT JSON only:
{
  "category": one of """ + str(list(ALLOWED_CATEGORIES)) + """,
  "severity": one of ["low","medium","high","critical"],
  "confidence": number between 0 and 1,
  "urgent": boolean,
  "reason": one short sentence suitable to show to campus staff (no chain-of-thought)
}
category must be exactly one of the allowed values. Do not invent team names.
Return ONLY the JSON object. No markdown fences."""


def _rule_analyze(description: str, is_sos: bool, category_hint: Optional[str] = None) -> dict:
    t = (description or "").lower()
    hint = (category_hint or "").lower()
    text = f"{t} {hint}"

    category = "OTHER"
    if any(w in text for w in ["collapse", "collapsed", "unconscious", "bleed", "injured", "injury", "seizure", "chest pain", "cardiac", "ambulance", "faint", "medical", "needs medical"]):
        category = "MEDICAL"
    elif any(w in text for w in ["smoke", "fire", "flame", "burn", "explosion", "gas leak"]):
        category = "FIRE"
    elif any(w in text for w in ["electric", "electrical", "shock", "short circuit", "transformer", "electrocution"]):
        category = "ELECTRICAL"
    elif any(w in text for w in ["unauthorized", "intruder", "theft", "assault", "fight", "weapon", "restricted", "stalker", "robbery"]):
        category = "SECURITY"
    elif any(w in text for w in ["accident", "collision", "hit and run", "run over"]):
        category = "ACCIDENT"
    elif any(w in text for w in ["water leak", "flood", "plumbing", "sewage", "burst pipe"]):
        category = "WATER"
    elif any(w in text for w in ["elevator", "lift stuck", "hvac", "network down"]):
        category = "TECHNICAL"
    elif any(w in text for w in ["trapped", "rescue", "cannot get out"]):
        category = "RESCUE"
    elif any(w in text for w in ["scaffold", "structural", "building falling", "debris"]):
        category = "CONSTRUCTION"
    elif any(w in text for w in ["chemical spill", "storm", "earthquake", "landslide"]):
        category = "ENVIRONMENTAL"
    elif any(w in text for w in ["bus", "vehicle", "traffic", "bike crash"]):
        category = "TRANSPORT"

    critical_words = ["fire", "unconscious", "bleeding", "cardiac", "chest pain", "explosion", "weapon", "gas leak", "collapsed"]
    severity = "medium"
    if is_sos or any(w in t for w in critical_words):
        severity = "critical"
    elif category in ("MEDICAL", "FIRE", "RESCUE", "SECURITY") and any(w in t for w in ["needs", "urgent", "help", "smoke", "attempting"]):
        severity = "high"
    elif category == "OTHER":
        severity = "low"

    urgent = severity in ("high", "critical") or is_sos
    routed = route_category(category)
    dept = routed["department"]
    return {
        "category": routed["category"],
        "severity": severity,
        "confidence": 0.62 if category != "OTHER" else 0.45,
        "urgent": urgent,
        "reason": "Rule-based fallback classification from the incident description.",
        "analysis_source": "fallback",
        "department": dept,
        "team_name": routed["team_name"],
        "priority": severity,
        "safety_instructions": agents._fallback_safety(dept),
    }


def _validate_ai_payload(j: dict, is_sos: bool) -> Optional[dict]:
    if not j or not isinstance(j, dict):
        return None
    cat = normalize_category(j.get("category") or "")
    sev = str(j.get("severity") or "medium").lower()
    if sev not in ALLOWED_SEVERITY:
        sev = "medium"
    if is_sos:
        sev = "critical"
    try:
        conf = float(j.get("confidence", 0.7))
    except (TypeError, ValueError):
        conf = 0.7
    conf = max(0.0, min(conf, 1.0))
    urgent = bool(j.get("urgent", sev in ("high", "critical")))
    if is_sos:
        urgent = True
    reason = str(j.get("reason") or "AI classification of the reported incident.")[:280]
    routed = route_category(cat)
    dept = routed["department"]
    return {
        "category": routed["category"],
        "severity": sev,
        "confidence": round(conf, 2),
        "urgent": urgent,
        "reason": reason,
        "analysis_source": "ai",
        "department": dept,
        "team_name": routed["team_name"],
        "priority": sev,
        "safety_instructions": agents._fallback_safety(dept),
    }


async def analyze_incident(
    description: str,
    is_sos: bool = False,
    category_hint: Optional[str] = None,
    incident_id: str = "unknown",
) -> dict:
    """Primary: LLM. Fallback: keywords. Always returns a routed department."""
    LOG.info("AI analysis started incident_id=%s", incident_id)
    user = (
        f"Description: {description}\nSOS: {is_sos}\n"
        f"Category hint: {category_hint or 'none'}\n"
        f"Allowed categories: {list(ALLOWED_CATEGORIES)}"
    )
    raw = await agents._claude_json(ANALYZER_SYSTEM, user, f"analyze-{incident_id}")
    validated = _validate_ai_payload(raw, is_sos) if raw else None
    if not validated:
        LOG.warning("AI analysis failed or invalid JSON; using fallback incident_id=%s", incident_id)
        result = _rule_analyze(description, is_sos, category_hint)
    else:
        result = validated
        LOG.info(
            "AI classification incident_id=%s category=%s severity=%s team=%s source=%s",
            incident_id, result["category"], result["severity"], result["department"], result["analysis_source"],
        )
    LOG.info("AI analysis completed incident_id=%s source=%s", incident_id, result["analysis_source"])
    return result
