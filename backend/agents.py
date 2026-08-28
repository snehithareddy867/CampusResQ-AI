"""Multi-agent AI orchestrator.

Uses Claude Sonnet 4.6 through the optional Emergent LLM integration when
available. If Emergent is unavailable or no API key is configured, the
built-in rule-based fallbacks keep the application functional."""
import os
import json
import re
import logging
from typing import Optional, List
try:
    # Emergent integration is optional. If the package is unavailable,
    # the built-in rule-based fallback is used automatically.
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    LlmChat = None
    UserMessage = None

LOG = logging.getLogger("agents")
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

DEPARTMENTS = [
    "medical", "fire_safety", "security", "electrical",
    "construction", "facilities", "environmental", "transport",
]
PRIORITIES = ["low", "medium", "high", "critical"]

CLASSIFIER_SYSTEM = """You are the Classifier Agent for CampusResQ AI, a campus emergency-response platform.
Given an incident description (and optional metadata), output STRICT JSON with keys:
category (short human string), department (one of: medical, fire_safety, security, electrical, construction, facilities, environmental, transport),
priority (one of: low, medium, high, critical), confidence (0..1 float), reason (1 sentence),
safety_instructions (array of 3 concise safety steps for the reporter until help arrives).
Return ONLY the JSON object. No prose. No markdown fences."""

FRAUD_SYSTEM = """You are the Fraud Detection Agent for CampusResQ AI.
Analyze the report considering: keyword coherence, vagueness, prank markers, duplicate history, and location plausibility.
Output STRICT JSON with keys: risk_score (0..1 float), risk_level (low|medium|high|critical), reasons (array of short strings), recommended_action (one of: proceed, review, escalate).
Return ONLY JSON."""

ASSISTANT_SYSTEM = """You are the CampusResQ AI Safety Assistant. You provide clear, calm, actionable safety guidance to a user while rescuers are on the way.
Rules:
- Never invent dangerous instructions; use widely-accepted first-response guidance.
- Prefer bullet steps.
- Keep answers under 150 words.
- If the situation is life-threatening, tell the user to stay on the line and follow official instructions."""


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    # remove fenced code
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        # try to find first {...}
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


async def _claude_json(system: str, user_text: str, session_id: str) -> Optional[dict]:
    if not EMERGENT_KEY or LlmChat is None or UserMessage is None:
        return None
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=session_id,
            system_message=system,
        ).with_model("anthropic", "claude-sonnet-4-6")
        resp = await chat.send_message(UserMessage(text=user_text))
        # send_message returns text
        if isinstance(resp, str):
            return _extract_json(resp)
        return _extract_json(str(resp))
    except Exception as e:
        LOG.warning(f"Claude call failed: {e}")
        return None


# ---------------- Rule-based fallback ----------------
KEYWORDS = {
    "medical": ["injury", "injured", "bleed", "unconscious", "seizure", "chest pain", "collapse", "faint", "cardiac", "heart", "wound", "cut", "broken", "asthma", "sick", "ill", "medical", "ambulance"],
    "fire_safety": ["fire", "smoke", "burn", "flame", "sparks", "gas leak", "explosion"],
    "electrical": ["electric", "electrical", "shock", "wire", "short circuit", "sparks from socket", "electrocution", "transformer"],
    "security": ["theft", "steal", "robbery", "attack", "assault", "fight", "harass", "stalker", "suspicious person", "intruder", "weapon"],
    "construction": ["collapse", "structural", "crack", "building falling", "scaffold", "beam", "debris"],
    "facilities": ["water leak", "flood", "elevator", "lift stuck", "broken door", "plumbing", "sewage"],
    "environmental": ["storm", "flooding", "earthquake", "lightning", "cyclone", "heat", "landslide", "chemical spill"],
    "transport": ["accident", "vehicle", "car", "bus", "bike", "hit", "run over", "collision", "traffic"],
}
CRITICAL_WORDS = ["fire", "unconscious", "bleeding heavily", "cardiac", "chest pain", "explosion", "collapse", "weapon", "gunshot", "electrocution", "gas leak"]


def _rule_classify(text: str, is_sos: bool) -> dict:
    t = text.lower()
    best_dept = "security"
    best_hits = 0
    best_category = "Security"
    for dept, kws in KEYWORDS.items():
        hits = sum(1 for k in kws if k in t)
        if hits > best_hits:
            best_hits = hits
            best_dept = dept
            best_category = dept.replace("_", " ").title()
    priority = "medium"
    if is_sos or any(w in t for w in CRITICAL_WORDS):
        priority = "critical"
    elif best_hits >= 2:
        priority = "high"
    elif best_hits == 0:
        priority = "low"
    confidence = min(0.5 + 0.15 * best_hits, 0.9) if best_hits else 0.5
    return {
        "category": best_category,
        "department": best_dept,
        "priority": priority,
        "confidence": round(confidence, 2),
        "reason": "Rule-based fallback classification.",
        "safety_instructions": _fallback_safety(best_dept),
    }


def _fallback_safety(dept: str) -> List[str]:
    tips = {
        "medical": ["Stay with the person; keep them calm.", "Do not move them if a spinal injury is possible.", "Follow instructions from the ambulance team."],
        "fire_safety": ["Evacuate the area immediately using stairs, not lifts.", "Stay low to avoid smoke inhalation.", "Do not re-enter the building."],
        "electrical": ["Do not touch the person or wire directly.", "Cut power at the main breaker if safe.", "Keep bystanders at a safe distance."],
        "security": ["Move to a safe, well-lit location.", "Avoid confrontation; keep distance.", "Stay on the line with campus security."],
        "construction": ["Move away from unstable structures.", "Do not enter cordoned areas.", "Warn others nearby."],
        "facilities": ["Keep away from water near electrical outlets.", "Turn off water/power at main if safe.", "Avoid slippery areas."],
        "environmental": ["Take shelter in a strong indoor structure.", "Stay away from windows.", "Follow official campus alerts."],
        "transport": ["Do not move injured persons unless in danger.", "Signal oncoming traffic to slow down.", "Wait for ambulance and campus security."],
    }
    return tips.get(dept, ["Stay calm.", "Move to a safe area.", "Wait for help; do not hang up."])


# ---------------- Public API ----------------
async def classify_incident(description: str, is_sos: bool, category_hint: Optional[str], incident_id: str) -> dict:
    user = f"Description: {description}\nSOS: {is_sos}\nCategory hint: {category_hint or 'none'}\nDepartments allowed: {DEPARTMENTS}\nPriorities: {PRIORITIES}"
    j = await _claude_json(CLASSIFIER_SYSTEM, user, f"classify-{incident_id}")
    if not j or "department" not in j or j.get("department") not in DEPARTMENTS:
        return _rule_classify(description, is_sos)
    # Normalize
    j["priority"] = j.get("priority", "medium").lower()
    if j["priority"] not in PRIORITIES:
        j["priority"] = "medium"
    if is_sos:
        j["priority"] = "critical"
    try:
        j["confidence"] = float(j.get("confidence", 0.7))
    except Exception:
        j["confidence"] = 0.7
    j.setdefault("safety_instructions", _fallback_safety(j["department"]))
    j.setdefault("category", j["department"].replace("_", " ").title())
    j.setdefault("reason", "AI classification.")
    return j


async def fraud_analyze(description: str, reporter_history_count: int, recent_duplicate: bool, incident_id: str) -> dict:
    user = f"Description: {description}\nReporter recent report count: {reporter_history_count}\nRecent duplicate description: {recent_duplicate}"
    j = await _claude_json(FRAUD_SYSTEM, user, f"fraud-{incident_id}")
    if not j:
        # simple heuristic
        score = 0.05
        reasons = []
        if recent_duplicate:
            score += 0.5
            reasons.append("Duplicate content submitted recently.")
        if reporter_history_count > 5:
            score += 0.2
            reasons.append("High recent submission rate.")
        if len(description.strip()) < 12:
            score += 0.2
            reasons.append("Very short description.")
        if any(w in description.lower() for w in ["prank", "joke", "test test"]):
            score += 0.3
            reasons.append("Prank markers detected.")
        score = min(score, 0.99)
        level = "low"
        if score >= 0.75:
            level = "critical"
        elif score >= 0.5:
            level = "high"
        elif score >= 0.25:
            level = "medium"
        action = "proceed" if level == "low" else ("review" if level == "medium" else "escalate")
        return {"risk_score": round(score, 2), "risk_level": level, "reasons": reasons or ["No suspicious markers."], "recommended_action": action}
    try:
        j["risk_score"] = float(j.get("risk_score", 0.1))
    except Exception:
        j["risk_score"] = 0.1
    j["risk_level"] = j.get("risk_level", "low").lower()
    if j["risk_level"] not in ["low", "medium", "high", "critical"]:
        j["risk_level"] = "low"
    j.setdefault("reasons", [])
    j.setdefault("recommended_action", "proceed")
    return j


async def assistant_reply(message: str, incident_context: Optional[dict], session_id: str) -> str:
    if not EMERGENT_KEY or LlmChat is None or UserMessage is None:
        return _fallback_reply(message, incident_context)
    try:
        ctx_str = ""
        if incident_context:
            ctx_str = f"\nCurrent incident: category={incident_context.get('category')}, priority={incident_context.get('priority')}, status={incident_context.get('status')}, ETA={incident_context.get('eta_minutes')} min."
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=session_id,
            system_message=ASSISTANT_SYSTEM + ctx_str,
        ).with_model("anthropic", "claude-sonnet-4-6")
        resp = await chat.send_message(UserMessage(text=message))
        return resp if isinstance(resp, str) else str(resp)
    except Exception as e:
        LOG.warning(f"Assistant failed: {e}")
        return _fallback_reply(message, incident_context)


def _fallback_reply(message: str, ctx: Optional[dict]) -> str:
    dept = (ctx or {}).get("department", "security")
    tips = _fallback_safety(dept)
    eta = (ctx or {}).get("eta_minutes")
    eta_line = f" Responders ETA: {eta} minutes." if eta else ""
    return "Stay calm — help is coming." + eta_line + "\n\n- " + "\n- ".join(tips)


# =============== Localisation Agent ===============
LANG_NAMES = {"en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada"}

TRANSLATOR_SYSTEM = """You are the Localisation Agent for CampusResQ AI.
Translate the provided emergency classification into the requested target language.
Preserve meaning exactly. Do NOT invent new safety steps. Output STRICT JSON:
{"category": string, "reason": string, "safety_instructions": [string, ...]}.
Return ONLY JSON. No fences."""


async def translate_ai_analysis(ai: dict, target_lang: str, incident_id: str) -> Optional[dict]:
    """Translate category/reason/safety_instructions to target language. Returns None on failure."""
    if not target_lang or target_lang == "en":
        return None
    lang_name = LANG_NAMES.get(target_lang)
    if not lang_name:
        return None
    payload = {"category": ai.get("category", ""), "reason": ai.get("reason", ""),
               "safety_instructions": ai.get("safety_instructions", [])}
    user = f"Target language: {lang_name}\nTranslate this JSON:\n{json.dumps(payload)}"
    j = await _claude_json(TRANSLATOR_SYSTEM, user, f"translate-{incident_id}-{target_lang}")
    if not j or "category" not in j:
        return None
    return {"category": str(j.get("category", payload["category"]))[:200],
            "reason": str(j.get("reason", payload["reason"]))[:400],
            "safety_instructions": [str(s)[:200] for s in (j.get("safety_instructions") or [])][:5]}


NOTIFICATION_TEMPLATES = {
    "AI_CLASSIFIED": {
        "en": "Your report was classified as {category} ({priority}).",
        "hi": "आपकी रिपोर्ट को {category} ({priority}) के रूप में वर्गीकृत किया गया।",
        "ta": "உங்கள் புகார் {category} ({priority}) என வகைப்படுத்தப்பட்டது.",
        "te": "మీ నివేదిక {category} ({priority}) గా వర్గీకరించబడింది.",
        "kn": "ನಿಮ್ಮ ವರದಿಯನ್ನು {category} ({priority}) ಎಂದು ವರ್ಗೀಕರಿಸಲಾಗಿದೆ.",
    },
    "DEPARTMENT_NOTIFIED": {
        "en": "{dept} team notified. Waiting for acceptance.",
        "hi": "{dept} टीम को सूचित किया गया। स्वीकृति की प्रतीक्षा है।",
        "ta": "{dept} அணிக்கு தெரிவிக்கப்பட்டது. ஏற்பை எதிர்நோக்குகிறது.",
        "te": "{dept} బృందానికి తెలియజేయబడింది. అంగీకారం కోసం ఎదురు చూస్తోంది.",
        "kn": "{dept} ತಂಡಕ್ಕೆ ತಿಳಿಸಲಾಗಿದೆ. ಸ್ವೀಕಾರಕ್ಕಾಗಿ ಕಾಯುತ್ತಿದೆ.",
    },
    "RESPONDER_ACCEPTED": {
        "en": "Rescue team accepted your emergency. ETA {eta} min.",
        "hi": "बचाव दल ने आपकी आपात स्थिति स्वीकार की। ETA {eta} मिनट।",
        "ta": "மீட்பு அணி உங்கள் அவசரத்தை ஏற்றுக்கொண்டது. ETA {eta} நிமிடம்.",
        "te": "రెస్క్యూ బృందం మీ అత్యవసర పరిస్థితిని అంగీకరించింది. ETA {eta} నిమిషాలు.",
        "kn": "ರಕ್ಷಣಾ ತಂಡ ನಿಮ್ಮ ತುರ್ತನ್ನು ಸ್ವೀಕರಿಸಿದೆ. ETA {eta} ನಿಮಿಷಗಳು.",
    },
    "RESPONDER_EN_ROUTE": {
        "en": "Responder is on the way · ETA {eta} min.",
        "hi": "जवाबदेह रास्ते में हैं · ETA {eta} मिनट।",
        "ta": "பதிலளிப்பவர் வருகிறார் · ETA {eta} நிமிடம்.",
        "te": "ప్రతిస్పందించేవారు వస్తున్నారు · ETA {eta} నిమిషాలు.",
        "kn": "ಪ್ರತಿಕ್ರಿಯಿಸುವವರು ಬರುತ್ತಿದ್ದಾರೆ · ETA {eta} ನಿಮಿಷಗಳು.",
    },
    "RESPONDER_ARRIVED": {
        "en": "Responder has arrived.",
        "hi": "जवाबदेह पहुँच गए हैं।",
        "ta": "பதிலளிப்பவர் வந்துவிட்டார்.",
        "te": "ప్రతిస్పందించేవారు వచ్చారు.",
        "kn": "ಪ್ರತಿಕ್ರಿಯಿಸುವವರು ಬಂದಿದ್ದಾರೆ.",
    },
    "INCIDENT_RESOLVED": {
        "en": "Your incident was marked resolved.",
        "hi": "आपकी घटना को हल के रूप में चिह्नित किया गया।",
        "ta": "உங்கள் சம்பவம் தீர்க்கப்பட்டதாகக் குறிக்கப்பட்டது.",
        "te": "మీ సంఘటన పరిష్కరించబడినట్లు గుర్తించబడింది.",
        "kn": "ನಿಮ್ಮ ಘಟನೆಯನ್ನು ಪರಿಹರಿಸಲಾಗಿದೆ ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ.",
    },
}


def render_notification(ntype: str, lang: str, **fields) -> Optional[str]:
    tmpl = NOTIFICATION_TEMPLATES.get(ntype, {}).get(lang or "en")
    if not tmpl:
        return None
    try:
        return tmpl.format(**fields)
    except Exception:
        return None


# =============== Localised Email Templates ===============
BUDDY_EMAIL_LABELS = {
    "en": {"subject": "SOS alert from {name} on campus", "heading": "SOS alert · CampusResQ AI",
           "intro": "<strong>{name}</strong> triggered an SOS emergency on campus.",
           "category": "Category", "reported_at": "Reported at", "status": "Status",
           "status_value": "Rescue team notified — response in progress.",
           "footer": "You are receiving this because {name} listed you as their peer buddy in CampusResQ AI. We never ask for your password or card details by email."},
    "hi": {"subject": "{name} की ओर से कैंपस पर SOS अलर्ट",
           "heading": "SOS अलर्ट · CampusResQ AI",
           "intro": "<strong>{name}</strong> ने कैंपस पर SOS आपात स्थिति भेजी है।",
           "category": "श्रेणी", "reported_at": "रिपोर्ट का समय", "status": "स्थिति",
           "status_value": "बचाव दल को सूचित किया गया — प्रतिक्रिया चल रही है।",
           "footer": "आपको यह इसलिए मिल रहा है क्योंकि {name} ने आपको अपना पीयर बडी सूचीबद्ध किया है। हम कभी भी ईमेल से पासवर्ड नहीं मांगते।"},
    "ta": {"subject": "வளாகத்தில் {name}-இன் SOS எச்சரிக்கை",
           "heading": "SOS எச்சரிக்கை · CampusResQ AI",
           "intro": "<strong>{name}</strong> வளாகத்தில் SOS அவசர நிலையைத் தொடங்கினார்.",
           "category": "வகை", "reported_at": "தெரிவிக்கப்பட்ட நேரம்", "status": "நிலை",
           "status_value": "மீட்பு அணிக்கு தெரிவிக்கப்பட்டது — பதில் நடந்து வருகிறது.",
           "footer": "{name} உங்களை தங்கள் peer buddy-ஆக பட்டியலிட்டதால் இது வருகிறது. மின்னஞ்சலில் எங்கள் கடவுச்சொல் கேட்க மாட்டோம்."},
    "te": {"subject": "క్యాంపస్‌లో {name} నుండి SOS హెచ్చరిక",
           "heading": "SOS హెచ్చరిక · CampusResQ AI",
           "intro": "<strong>{name}</strong> క్యాంపస్‌లో SOS అత్యవసర పరిస్థితిని ప్రారంభించారు.",
           "category": "వర్గం", "reported_at": "నివేదించిన సమయం", "status": "స్థితి",
           "status_value": "రెస్క్యూ బృందానికి తెలియజేయబడింది — స్పందన కొనసాగుతోంది.",
           "footer": "{name} మిమ్మల్ని peer buddy గా జాబితా చేసినందున ఇది వస్తోంది. మేము ఇమెయిల్ ద్వారా పాస్‌వర్డ్‌లు అడగము."},
    "kn": {"subject": "ಕ್ಯಾಂಪಸ್‌ನಲ್ಲಿ {name} ರಿಂದ SOS ಎಚ್ಚರಿಕೆ",
           "heading": "SOS ಎಚ್ಚರಿಕೆ · CampusResQ AI",
           "intro": "<strong>{name}</strong> ಕ್ಯಾಂಪಸ್‌ನಲ್ಲಿ SOS ತುರ್ತು ಪರಿಸ್ಥಿತಿಯನ್ನು ಪ್ರಾರಂಭಿಸಿದ್ದಾರೆ.",
           "category": "ವರ್ಗ", "reported_at": "ವರದಿ ಮಾಡಿದ ಸಮಯ", "status": "ಸ್ಥಿತಿ",
           "status_value": "ರಕ್ಷಣಾ ತಂಡಕ್ಕೆ ತಿಳಿಸಲಾಗಿದೆ — ಪ್ರತಿಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ.",
           "footer": "{name} ನಿಮ್ಮನ್ನು peer buddy ಆಗಿ ಪಟ್ಟಿ ಮಾಡಿರುವುದರಿಂದ ಇದು ಬರುತ್ತಿದೆ. ನಾವು ಇಮೇಲ್ ಮೂಲಕ ಪಾಸ್‌ವರ್ಡ್‌ಗಳನ್ನು ಕೇಳುವುದಿಲ್ಲ."},
}

DIGEST_EMAIL_LABELS = {
    "en": {"subject": "CampusResQ AI · Weekly Safety Digest",
           "heading": "CampusResQ AI · Weekly Safety Digest", "window": "Rolling 7-day view · generated {date}",
           "incidents": "Incidents", "resolved": "Resolved", "critical": "Critical",
           "fraud": "Fraud flags", "avg_accept": "Avg acceptance time", "by_dept": "Incidents by department",
           "footer": "You are receiving this because you are a head admin on CampusResQ AI. We never ask for your password by email."},
    "hi": {"subject": "CampusResQ AI · साप्ताहिक सुरक्षा डाइजेस्ट",
           "heading": "CampusResQ AI · साप्ताहिक सुरक्षा डाइजेस्ट", "window": "पिछले 7 दिन · {date} को उत्पन्न",
           "incidents": "घटनाएँ", "resolved": "हल किए गए", "critical": "गंभीर",
           "fraud": "फ्रॉड फ्लैग", "avg_accept": "औसत स्वीकृति समय", "by_dept": "विभाग द्वारा घटनाएँ",
           "footer": "आप हेड एडमिन हैं इसलिए यह मिल रहा है। हम ईमेल से पासवर्ड नहीं मांगते।"},
    "ta": {"subject": "CampusResQ AI · வாராந்திர பாதுகாப்பு டைஜெஸ்ட்",
           "heading": "CampusResQ AI · வாராந்திர பாதுகாப்பு டைஜெஸ்ட்", "window": "7 நாள் காட்சி · {date}-இல் உருவாக்கப்பட்டது",
           "incidents": "சம்பவங்கள்", "resolved": "தீர்க்கப்பட்டவை", "critical": "மிக அவசரம்",
           "fraud": "மோசடி கொடிகள்", "avg_accept": "சராசரி ஏற்பு நேரம்", "by_dept": "துறை வாரியாக சம்பவங்கள்",
           "footer": "நீங்கள் head admin என்பதால் இது வருகிறது. மின்னஞ்சலில் கடவுச்சொல் கேட்க மாட்டோம்."},
    "te": {"subject": "CampusResQ AI · వారపు భద్రతా డైజెస్ట్",
           "heading": "CampusResQ AI · వారపు భద్రతా డైజెస్ట్", "window": "7 రోజుల వీక్షణ · {date}న రూపొందించబడింది",
           "incidents": "సంఘటనలు", "resolved": "పరిష్కరించబడినవి", "critical": "క్రిటికల్",
           "fraud": "మోసం జెండాలు", "avg_accept": "సగటు అంగీకార సమయం", "by_dept": "విభాగం వారీగా సంఘటనలు",
           "footer": "మీరు head admin కాబట్టి ఇది వస్తోంది. మేము ఇమెయిల్ ద్వారా పాస్‌వర్డ్‌లు అడగము."},
    "kn": {"subject": "CampusResQ AI · ಸಾಪ್ತಾಹಿಕ ಸುರಕ್ಷತಾ ಡೈಜೆಸ್ಟ್",
           "heading": "CampusResQ AI · ಸಾಪ್ತಾಹಿಕ ಸುರಕ್ಷತಾ ಡೈಜೆಸ್ಟ್", "window": "7 ದಿನಗಳ ವೀಕ್ಷಣೆ · {date} ರಂದು ರಚಿಸಲಾಗಿದೆ",
           "incidents": "ಘಟನೆಗಳು", "resolved": "ಪರಿಹರಿಸಲಾಗಿದೆ", "critical": "ಕ್ರಿಟಿಕಲ್",
           "fraud": "ವಂಚನೆ ಫ್ಲಾಗ್‌ಗಳು", "avg_accept": "ಸರಾಸರಿ ಸ್ವೀಕಾರ ಸಮಯ", "by_dept": "ವಿಭಾಗವಾರು ಘಟನೆಗಳು",
           "footer": "ನೀವು head admin ಆಗಿರುವುದರಿಂದ ಇದು ಬರುತ್ತಿದೆ. ನಾವು ಇಮೇಲ್ ಮೂಲಕ ಪಾಸ್‌ವರ್ಡ್‌ಗಳನ್ನು ಕೇಳುವುದಿಲ್ಲ."},
}


def buddy_email_labels(lang: str) -> dict:
    return BUDDY_EMAIL_LABELS.get(lang) or BUDDY_EMAIL_LABELS["en"]


def digest_email_labels(lang: str) -> dict:
    return DIGEST_EMAIL_LABELS.get(lang) or DIGEST_EMAIL_LABELS["en"]


# =============== Media Forensics Agent ===============
import hashlib

FORENSICS_SYSTEM = """You are the Media Forensics Agent for CampusResQ AI.
Given a textual description of an incident AND a list of attached evidence items (each with kind, filename, size_bytes, mime),
assess authenticity signals for coordination purposes. You cannot inspect pixels — you must reason from description consistency,
file counts, media kinds vs. the described event, unusually generic filenames, and duplication.
Output STRICT JSON: {verdict: authentic|suspicious|likely_manipulated|insufficient_data,
confidence: 0..1, reasons: [short strings], per_item: [{filename, note}]}.
Rules:
- If no evidence, verdict="insufficient_data", confidence <= 0.4.
- Never claim absolute certainty; cap confidence at 0.9.
- Return JSON only. No markdown fences."""


async def media_forensics(description: str, evidence: list, prior_hashes: list, incident_id: str) -> dict:
    """Hybrid rule-based + LLM textual forensics. Does NOT decode pixels."""
    per_item = []
    reasons = []
    # rule-based signals
    duplicate_count = 0
    seen = set()
    for i, ev in enumerate(evidence or []):
        data = ev.get("data_url") or ""
        # hash the base64 tail
        tail = data.split(",", 1)[-1] if data else ""
        h = hashlib.sha256(tail.encode("utf-8", "ignore")).hexdigest()[:16] if tail else None
        size = len(tail) * 3 // 4 if tail else 0
        mime = data.split(";", 1)[0].replace("data:", "") if data else ev.get("kind", "unknown")
        note = None
        if h:
            if h in prior_hashes:
                duplicate_count += 1
                note = "hash matches a previously submitted media item"
            elif h in seen:
                duplicate_count += 1
                note = "duplicate within this report"
            seen.add(h)
        if size and size < 4000:
            note = (note + "; " if note else "") + "very small file (possible thumbnail/placeholder)"
        per_item.append({"filename": ev.get("filename", f"item_{i}"), "kind": ev.get("kind"), "mime": mime, "size_bytes": size, "hash": h, "note": note})
    if duplicate_count:
        reasons.append(f"{duplicate_count} duplicate/reused media item(s) detected")

    # Text-based LLM signal (metadata only, no pixel data sent)
    llm_result = None
    if EMERGENT_KEY and LlmChat is not None and UserMessage is not None and evidence:
        meta_summary = [{"filename": p["filename"], "kind": p["kind"], "mime": p["mime"], "size_bytes": p["size_bytes"]} for p in per_item]
        user = f"Description: {description}\nEvidence metadata: {json.dumps(meta_summary)}"
        llm_result = await _claude_json(FORENSICS_SYSTEM, user, f"forensics-{incident_id}")

    if not evidence:
        return {"verdict": "insufficient_data", "confidence": 0.3, "reasons": ["No media attached."], "per_item": []}

    if llm_result and isinstance(llm_result, dict) and llm_result.get("verdict") in ("authentic", "suspicious", "likely_manipulated", "insufficient_data"):
        # merge rule-based reasons
        merged_reasons = list(dict.fromkeys((llm_result.get("reasons") or []) + reasons))
        conf = min(float(llm_result.get("confidence", 0.6)), 0.9)
        if duplicate_count and llm_result.get("verdict") == "authentic":
            # duplicates override authenticity to suspicious
            return {"verdict": "suspicious", "confidence": max(conf, 0.7), "reasons": merged_reasons, "per_item": per_item}
        return {"verdict": llm_result["verdict"], "confidence": conf, "reasons": merged_reasons, "per_item": per_item}

    # fallback verdict
    if duplicate_count >= 2:
        return {"verdict": "likely_manipulated", "confidence": 0.75, "reasons": reasons or ["Multiple duplicates."], "per_item": per_item}
    if duplicate_count == 1:
        return {"verdict": "suspicious", "confidence": 0.6, "reasons": reasons, "per_item": per_item}
    return {"verdict": "authentic", "confidence": 0.6, "reasons": reasons or ["No obvious tampering signals."], "per_item": per_item}


# =============== ETA Recalculation ===============
def recalc_eta_minutes(distance_km: float, speed_mps: Optional[float]) -> int:
    if distance_km is None:
        return 5
    # if speed available and reasonable (0.5..30 m/s), use it; else assume 20 km/h
    if speed_mps and 0.5 <= speed_mps <= 30:
        seconds = (distance_km * 1000) / speed_mps
    else:
        seconds = (distance_km / 20.0) * 3600  # 20 km/h assumed
    minutes = max(1, int(round(seconds / 60)))
    return minutes
