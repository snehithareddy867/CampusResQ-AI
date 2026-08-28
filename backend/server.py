"""CampusResQ AI - FastAPI backend."""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import math
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from models import (  # noqa: E402
    RegisterRequest, LoginRequest, UserPublic, ReportRequest, Incident,
    IncidentStatus, Priority, Department, Role, FraudLevel, AIAnalysis,
    FraudAnalysis, Notification, AuditLog, ResponderAcceptRequest,
    ResponderRejectRequest, ResponderLocationUpdate, StatusUpdateRequest,
    AdminOverrideRequest, AssistantChatRequest, Location, now_iso, uid,
    Team, TeamCreateRequest, TeamUpdateRequest, ResponderSkillsUpdate,
    PushSubscriptionRequest,
)
from auth import (  # noqa: E402
    hash_password, verify_password, create_token, current_user_ctx,
    require_roles, validate_password_strength, decode_token,
)
import agents  # noqa: E402
from emailer import send_email  # noqa: E402
from sms import send_sms, sms_configured  # noqa: E402
from html import escape as html_escape  # noqa: E402
import secrets  # noqa: E402

WEBHOOK_CRON_SECRET = os.environ.get("WEBHOOK_CRON_SECRET", "")


# ---------------- WebSocket manager (realtime) ----------------
class WSManager:
    def __init__(self):
        self.conns: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.conns.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        lst = self.conns.get(user_id, [])
        if ws in lst:
            lst.remove(ws)

    async def send(self, user_id: str, message: dict):
        dead = []
        for ws in list(self.conns.get(user_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, user_ids: List[str], message: dict):
        for _uid in set(user_ids):
            await self.send(_uid, message)


ws_manager = WSManager()


REGNUM_STUDENT_RE = re.compile(r"^\d{2}-\d-[A-Z]{2,4}$")
REGNUM_STAFF_RE = re.compile(r"^[A-Z]{2,6}-\d{2,6}$")


def validate_registration_number(role: str, regnum: Optional[str]) -> Optional[str]:
    if role == Role.STUDENT.value:
        if not regnum:
            return "Registration number is required (e.g., 24-1-FK)."
        if not REGNUM_STUDENT_RE.match(regnum):
            return "Student registration number must be like 24-1-FK (YY-N-XX)."
    else:
        if regnum and not REGNUM_STAFF_RE.match(regnum):
            return "Staff ID must be like FAC-1234."
    return None

# Mongo
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="CampusResQ AI")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("campusresq")


# ---------------- Helpers ----------------
async def get_user(user_id: str) -> Optional[dict]:
    return await db.users.find_one({"id": user_id}, {"_id": 0})


async def log_audit(actor: dict, action: str, entity_type: str, entity_id: str, prev=None, new=None):
    a = AuditLog(
        actor_id=actor.get("id", "system"),
        actor_name=actor.get("name", "System"),
        actor_role=actor.get("role", "system"),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        prev_value=prev,
        new_value=new,
    ).model_dump()
    await db.audit_logs.insert_one(a)


async def notify(user_id: str, ntype: str, message: str, incident_id: Optional[str] = None, priority: Priority = Priority.MEDIUM):
    n = Notification(user_id=user_id, type=ntype, message=message, incident_id=incident_id, priority=priority).model_dump()
    await db.notifications.insert_one(n)
    # realtime push over websocket
    asyncio.create_task(ws_manager.send(user_id, {
        "event": "notification",
        "type": ntype,
        "message": message,
        "incident_id": incident_id,
        "priority": priority.value if hasattr(priority, "value") else str(priority),
        "at": n["created_at"],
    }))
    # fire-and-forget web push
    asyncio.create_task(send_push_to_user(user_id, ntype, message, incident_id, priority.value))


async def broadcast_incident_update(incident_id: str, event: str = "incident_update"):
    """Notify reporter, assigned responder, dept staff, heads to refetch."""
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        return
    ids = {inc["reporter_id"]}
    if inc.get("assigned_responder_id"):
        ids.add(inc["assigned_responder_id"])
    dept = inc.get("assigned_department")
    if dept:
        async for u in db.users.find({"$or": [{"role": Role.DEPT_ADMIN.value, "department": dept}, {"role": Role.DEPT_PERSONNEL.value, "department": dept}, {"role": Role.RESPONDER.value, "department": dept}]}, {"_id": 0, "id": 1}):
            ids.add(u["id"])
    async for u in db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0, "id": 1}):
        ids.add(u["id"])
    await ws_manager.broadcast(list(ids), {"event": event, "incident_id": incident_id, "status": inc.get("status"), "type": "incident_update"})


# ---------------- Web Push ----------------
try:
    from pywebpush import webpush, WebPushException
    PUSH_AVAILABLE = True
except Exception:
    PUSH_AVAILABLE = False

VAPID_PUBLIC = os.environ.get("VAPID_PUBLIC", "")
VAPID_PRIVATE = os.environ.get("VAPID_PRIVATE", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@campus.edu")


async def send_push_to_user(user_id: str, ntype: str, message: str, incident_id: Optional[str], priority: str):
    if not PUSH_AVAILABLE or not VAPID_PRIVATE:
        return
    subs = await db.push_subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(50)
    if not subs:
        return
    payload = json.dumps({
        "title": ntype.replace("_", " "),
        "body": message,
        "incident_id": incident_id,
        "priority": priority,
        "url": f"/emergency/{incident_id}" if incident_id else "/notifications",
    })
    dead = []
    for s in subs:
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info={"endpoint": s["endpoint"], "keys": s["keys"]},
                data=payload,
                vapid_private_key=VAPID_PRIVATE,
                vapid_claims={"sub": VAPID_SUBJECT},
            )
        except Exception as e:
            log.warning(f"push failed for {user_id}: {e}")
            dead.append(s["endpoint"])
    if dead:
        await db.push_subscriptions.delete_many({"endpoint": {"$in": dead}})


def add_timeline(incident: dict, text: str):
    incident.setdefault("timeline", []).append({"at": now_iso(), "text": text})


def haversine_km(a: dict, b: dict) -> float:
    if not a or not b:
        return 9999
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(h))


# ---------------- Auth ----------------
@api.post("/auth/register")
async def register(req: RegisterRequest):
    err = validate_password_strength(req.password)
    if err:
        raise HTTPException(400, err)
    reg_err = validate_registration_number(req.role.value, req.registration_number)
    if reg_err:
        raise HTTPException(400, reg_err)
    existing = await db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(400, "Email already registered")
    if req.registration_number:
        dup = await db.users.find_one({"registration_number": req.registration_number})
        if dup:
            raise HTTPException(400, f"Registration number '{req.registration_number}' already exists")
    user_doc = {
        "id": uid(),
        "name": req.name,
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "role": req.role.value,
        "department": req.department.value if req.department else None,
        "phone": req.phone,
        "registration_number": req.registration_number,
        "available": True,
        "buddy_email": None,
        "buddy_name": None,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_doc["id"], user_doc["role"])
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    return {"token": token, "user": user_doc}


@api.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email.lower()}, {"_id": 0})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_token(user["id"], user["role"])
    user.pop("password_hash", None)
    return {"token": token, "user": user}


@api.get("/auth/me")
async def me(ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    if not user:
        raise HTTPException(404, "User not found")
    user.pop("password_hash", None)
    return user


# ---------------- Incidents ----------------
async def process_incident_pipeline(incident_id: str):
    """Async pipeline: classify -> fraud -> assign responder."""
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        return
    # 1. Classify
    inc["status"] = IncidentStatus.ANALYZING.value
    add_timeline(inc, "AI analyzing incident")
    await db.incidents.update_one({"id": incident_id}, {"$set": {"status": inc["status"], "timeline": inc["timeline"]}})

    ai = await agents.classify_incident(inc["description"], inc.get("is_sos", False), inc.get("category_hint"), incident_id)
    dept = ai["department"]
    priority = ai["priority"]

    # 2. Fraud
    recent_count = await db.incidents.count_documents({
        "reporter_id": inc["reporter_id"],
        "reported_at": {"$gt": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()},
    })
    recent_dup = False
    async for prev in db.incidents.find({"reporter_id": inc["reporter_id"], "id": {"$ne": incident_id}}, {"_id": 0, "description": 1}).sort("reported_at", -1).limit(3):
        if prev.get("description", "").strip().lower() == inc["description"].strip().lower():
            recent_dup = True
            break
    fraud = await agents.fraud_analyze(inc["description"], recent_count, recent_dup, incident_id)

    # 2b. Media Forensics (parallel-friendly)
    prior_hashes = []
    forensics = await agents.media_forensics(inc["description"], inc.get("evidence") or [], prior_hashes, incident_id)

    # 3. Assign responder if not fraud escalated
    status = IncidentStatus.CLASSIFIED.value
    add_timeline(inc, f"Classified as {ai['category']} → {dept}, priority {priority}")
    add_timeline(inc, f"Fraud risk: {fraud['risk_level']} ({fraud['risk_score']})")

    # AI RECOMMENDS ONLY. Humans must accept. Broadcast to department responders.
    if fraud["risk_level"] in ("high", "critical") and not inc.get("is_sos"):
        status = IncidentStatus.FRAUD_REVIEW.value
        add_timeline(inc, "Flagged for human fraud review (AI recommendation)")
    else:
        # If SOS with a peer buddy, email the buddy
        if inc.get("is_sos"):
            reporter = await get_user(inc["reporter_id"])
            if reporter and reporter.get("buddy_email"):
                asyncio.create_task(notify_buddy_of_sos(reporter, incident_id, ai.get("category")))
                add_timeline(inc, f"Peer buddy alert sent to {reporter.get('buddy_email')}")
        status = IncidentStatus.WAITING_FOR_ACCEPTANCE.value
        candidates = await db.users.find({"role": Role.RESPONDER.value, "department": dept, "available": True}, {"_id": 0, "password_hash": 0}).to_list(200)
        sos_ids = []
        if inc.get("is_sos"):
            # SOS proximity broadcast — only nearby responders
            cfg = await db.system_config.find_one({"id": "global"}, {"_id": 0}) or {}
            radius_m = int(cfg.get("sos_radius_m", 2000))
            nearby = []
            for r in candidates:
                loc = r.get("last_location")
                if not loc:
                    continue
                dist_m = haversine_km(inc["location"], loc) * 1000
                if dist_m <= radius_m:
                    nearby.append((dist_m, r))
            nearby.sort(key=lambda x: x[0])
            if nearby:
                candidates = [r for _, r in nearby]
                sos_ids = [r["id"] for r in candidates]
                add_timeline(inc, f"SOS proximity broadcast: {len(candidates)} responders within {radius_m}m (closest {int(nearby[0][0])}m)")
            else:
                add_timeline(inc, f"SOS: no responders within {radius_m}m — falling back to department-wide broadcast")
        if candidates:
            if not inc.get("is_sos"):
                add_timeline(inc, f"AI recommended department: {dept}. Awaiting human acceptance ({len(candidates)} responders notified).")
            ntype = "SOS_NEARBY" if inc.get("is_sos") else "DEPT_NEW_INCIDENT"
            body_prefix = "SOS EMERGENCY nearby — " if inc.get("is_sos") else "NEW "
            for r in candidates:
                await notify(r["id"], ntype, f"{body_prefix}{priority.upper()} incident requires acceptance: {ai['category']}", incident_id, Priority(priority))
        else:
            status = IncidentStatus.ESCALATED.value
            add_timeline(inc, "No responder available — escalated to head admin")
            heads = await db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0}).to_list(20)
            for h in heads:
                await notify(h["id"], "ADMIN_ESCALATION", f"No responder available for {ai['category']}", incident_id, Priority.CRITICAL)

    upd = {
        "ai_analysis": ai, "fraud_analysis": fraud, "media_forensics": forensics,
        "assigned_department": dept, "priority": priority, "status": status,
        "classified_at": now_iso(), "timeline": inc["timeline"],
        "sos_broadcast_ids": sos_ids if inc.get("is_sos") else [],
    }
    # Localise AI analysis for reporter's language (best effort)
    reporter_full = await get_user(inc["reporter_id"])
    reporter_lang = (reporter_full or {}).get("language") or "en"
    if reporter_lang != "en":
        localised = await agents.translate_ai_analysis(ai, reporter_lang, incident_id)
        if localised:
            upd["ai_analysis_localized"] = {reporter_lang: localised}
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    ai_cat_local = ((upd.get("ai_analysis_localized") or {}).get(reporter_lang) or {}).get("category") or ai["category"]
    msg = agents.render_notification("AI_CLASSIFIED", reporter_lang, category=ai_cat_local, priority=priority) or f"Your report was classified as {ai_cat_local} ({priority})."
    await notify(inc["reporter_id"], "AI_CLASSIFIED", msg, incident_id, Priority(priority))
    if forensics.get("verdict") in ("suspicious", "likely_manipulated"):
        heads = await db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0}).to_list(20)
        for h in heads:
            await notify(h["id"], "MEDIA_FORENSICS_ALERT", f"Media flagged {forensics['verdict']} on incident.", incident_id, Priority.HIGH)
    if status == IncidentStatus.WAITING_FOR_ACCEPTANCE.value:
        dept_pretty = dept.replace('_', ' ').title()
        dept_msg = agents.render_notification("DEPARTMENT_NOTIFIED", reporter_lang, dept=dept_pretty) or f"{dept_pretty} team notified. Waiting for acceptance."
        await notify(inc["reporter_id"], "DEPARTMENT_NOTIFIED", dept_msg, incident_id)
        # Get configured timeout from primary team if present, else default 60s
        team = await db.teams.find_one({"department": dept, "kind": "primary"}, {"_id": 0})
        timeout = (team or {}).get("acceptance_timeout_sec", 60)
        asyncio.create_task(_escalation_watchdog(incident_id, dept, timeout))
    asyncio.create_task(broadcast_incident_update(incident_id, "classified"))


async def _escalation_watchdog(incident_id: str, dept: str, seconds: int):
    await asyncio.sleep(seconds)
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc or inc.get("status") != IncidentStatus.WAITING_FOR_ACCEPTANCE.value:
        return
    add_timeline(inc, f"No acceptance in {seconds}s — escalating to backup team.")
    await db.incidents.update_one({"id": incident_id}, {"$set": {"status": IncidentStatus.ESCALATED.value, "escalated": True, "timeline": inc["timeline"]}})
    # Prefer explicit backup team members
    backup_team = await db.teams.find_one({"department": dept, "kind": "backup"}, {"_id": 0})
    notified_ids = set()
    if backup_team and backup_team.get("members"):
        for m in backup_team["members"]:
            await notify(m["user_id"], "BACKUP_ESCALATION", f"BACKUP: incident needs acceptance ({dept}).", incident_id, Priority.CRITICAL)
            notified_ids.add(m["user_id"])
    # fallback: any available responders in dept + heads
    if not notified_ids:
        resp = await db.users.find({"role": Role.RESPONDER.value, "available": True, "department": dept}, {"_id": 0}).to_list(200)
        for r in resp:
            await notify(r["id"], "BACKUP_ESCALATION", f"BACKUP: incident needs acceptance ({dept}).", incident_id, Priority.CRITICAL)
    heads = await db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0}).to_list(20)
    for h in heads:
        await notify(h["id"], "ADMIN_ESCALATION", f"Escalation: {dept} did not accept in {seconds}s.", incident_id, Priority.CRITICAL)


@api.post("/emergencies")
async def create_emergency(req: ReportRequest, ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    # dedupe by client_op_id
    if req.client_op_id:
        existing = await db.incidents.find_one({"client_op_id": req.client_op_id, "reporter_id": user["id"]}, {"_id": 0})
        if existing:
            return existing
    inc = Incident(
        reporter_id=user["id"],
        reporter_name=user["name"],
        description=req.description,
        location=req.location,
        category_hint=req.category_hint,
        is_sos=req.is_sos,
        evidence=req.evidence,
        client_op_id=req.client_op_id,
    ).model_dump()
    add_timeline(inc, "Report created")
    await db.incidents.insert_one(inc)
    await notify(user["id"], "REPORT_CREATED", "Your emergency report was received.", inc["id"])
    await log_audit(user, "create_incident", "incident", inc["id"], None, {"description": inc["description"]})
    # kick off pipeline
    asyncio.create_task(process_incident_pipeline(inc["id"]))
    inc.pop("_id", None)
    return inc


@api.get("/emergencies")
async def list_emergencies(status: Optional[str] = None, mine: bool = False, ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    q = {}
    role = user["role"]
    if mine or role == Role.STUDENT.value:
        q["reporter_id"] = user["id"]
    elif role == Role.RESPONDER.value:
        q["$or"] = [
            {"assigned_responder_id": user["id"]},
            {"assigned_department": user.get("department"), "assigned_responder_id": None, "status": {"$in": ["waiting_for_acceptance", "escalated"]}},
            {"status": "escalated"},  # backup broadcast
        ]
    elif role in (Role.DEPT_PERSONNEL.value, Role.DEPT_ADMIN.value):
        q["assigned_department"] = user.get("department")
    if status:
        q["status"] = status
    docs = await db.incidents.find(q, {"_id": 0}).sort("reported_at", -1).limit(200).to_list(200)
    return docs


@api.get("/emergencies/{incident_id}")
async def get_emergency(incident_id: str, ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    role = user["role"]
    # RBAC: student only own; responder own dept; dept staff own dept; admin all
    if role == Role.STUDENT.value and inc["reporter_id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if role == Role.RESPONDER.value and inc.get("assigned_department") != user.get("department") and inc.get("assigned_responder_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    if role in (Role.DEPT_PERSONNEL.value, Role.DEPT_ADMIN.value) and inc.get("assigned_department") != user.get("department"):
        raise HTTPException(403, "Forbidden")
    return inc


@api.post("/emergencies/{incident_id}/accept")
async def responder_accept(incident_id: str, req: ResponderAcceptRequest, ctx: dict = Depends(require_roles(Role.RESPONDER.value))):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    # Allow same-dept OR backup (during escalation)
    same_dept = inc.get("assigned_department") == user.get("department")
    escalated = inc.get("status") == IncidentStatus.ESCALATED.value
    if not (same_dept or escalated):
        raise HTTPException(403, "Not your department")
    # Only allow accept from waiting/escalated states — atomic guard
    now = now_iso()
    upd = {
        "status": IncidentStatus.ACCEPTED.value, "accepted_at": now,
        "eta_minutes": req.eta_minutes,
        "assigned_responder_id": user["id"], "assigned_responder_name": user["name"],
        "accepted_by_department": user.get("department"),
    }
    if req.current_location:
        upd["responder_location"] = req.current_location.model_dump()
    add_timeline(inc, f"HUMAN ACCEPT: {user['name']} ({user.get('department')}) — ETA {req.eta_minutes} min")
    upd["timeline"] = inc["timeline"]
    # atomic: only accept if still waiting/escalated and not yet accepted by someone else
    result = await db.incidents.update_one(
        {"id": incident_id, "assigned_responder_id": None,
         "status": {"$in": [IncidentStatus.WAITING_FOR_ACCEPTANCE.value, IncidentStatus.ESCALATED.value, IncidentStatus.ASSIGNED.value]}},
        {"$set": upd},
    )
    if result.modified_count == 0:
        raise HTTPException(409, "Incident already accepted or not acceptable")
    reporter = await get_user(inc["reporter_id"])
    r_lang = (reporter or {}).get("language") or "en"
    acc_msg = agents.render_notification("RESPONDER_ACCEPTED", r_lang, eta=req.eta_minutes) or f"Rescue team accepted your emergency. ETA {req.eta_minutes} min."
    await notify(inc["reporter_id"], "RESPONDER_ACCEPTED", acc_msg, incident_id, Priority.HIGH)
    await log_audit(user, "accept_incident", "incident", incident_id)
    asyncio.create_task(broadcast_incident_update(incident_id, "accepted"))
    # Notify other broadcast recipients that SOS has been taken
    if inc.get("sos_broadcast_ids"):
        for rid in inc["sos_broadcast_ids"]:
            if rid != user["id"]:
                await notify(rid, "SOS_TAKEN", f"SOS was accepted by {user['name']}. Standing down.", incident_id)
    return {"ok": True}


# ---------------- Resolution (dual confirmation) ----------------
@api.post("/emergencies/{incident_id}/reporter-safe")
async def reporter_confirm_safe(incident_id: str, ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    if inc["reporter_id"] != user["id"]:
        raise HTTPException(403, "Only the reporter can confirm safety")
    if inc["status"] in (IncidentStatus.RESOLVED.value, IncidentStatus.CANCELLED.value):
        return {"ok": True}
    now = now_iso()
    upd = {"reporter_confirmed_safe": True, "reporter_safe_at": now}
    add_timeline(inc, f"REPORTER SAFE: {user['name']} confirmed safety")
    if inc.get("responder_marked_complete"):
        upd["status"] = IncidentStatus.RESOLVED.value
        upd["resolved_at"] = now
        add_timeline(inc, "Both sides confirmed — incident RESOLVED")
    else:
        upd["status"] = IncidentStatus.RESOLUTION_PENDING.value
        add_timeline(inc, "Awaiting responder to mark response complete")
    upd["timeline"] = inc["timeline"]
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    if inc.get("assigned_responder_id"):
        await notify(inc["assigned_responder_id"], "REPORTER_SAFE", f"{user['name']} confirmed safety.", incident_id)
    await log_audit(user, "reporter_confirmed_safe", "incident", incident_id)
    asyncio.create_task(broadcast_incident_update(incident_id, "reporter_safe"))
    return {"ok": True, "status": upd.get("status")}


@api.post("/emergencies/{incident_id}/responder-complete")
async def responder_mark_complete(incident_id: str, ctx: dict = Depends(require_roles(Role.RESPONDER.value))):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    if inc.get("assigned_responder_id") != user["id"]:
        raise HTTPException(403, "Only the assigned responder can complete")
    now = now_iso()
    upd = {"responder_marked_complete": True, "responder_complete_at": now}
    add_timeline(inc, f"RESPONDER COMPLETE: {user['name']} marked response complete")
    if inc.get("reporter_confirmed_safe"):
        upd["status"] = IncidentStatus.RESOLVED.value
        upd["resolved_at"] = now
        add_timeline(inc, "Both sides confirmed — incident RESOLVED")
    else:
        upd["status"] = IncidentStatus.RESOLUTION_PENDING.value
        add_timeline(inc, "Awaiting reporter safety confirmation")
        await notify(inc["reporter_id"], "CONFIRM_SAFETY", "Responder marked response complete. Please confirm you are safe.", incident_id, Priority.HIGH)
    upd["timeline"] = inc["timeline"]
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    await log_audit(user, "responder_marked_complete", "incident", incident_id)
    asyncio.create_task(broadcast_incident_update(incident_id, "responder_complete"))
    return {"ok": True, "status": upd.get("status")}


@api.post("/emergencies/{incident_id}/reject")
async def responder_reject(incident_id: str, req: ResponderRejectRequest, ctx: dict = Depends(require_roles(Role.RESPONDER.value))):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    add_timeline(inc, f"Responder {user['name']} rejected: {req.reason or 'n/a'}")
    # find another responder in same dept, excluding this one
    dept = inc.get("assigned_department")
    candidates = await db.users.find({"role": Role.RESPONDER.value, "department": dept, "available": True, "id": {"$ne": user["id"]}}, {"_id": 0}).to_list(50)
    if candidates:
        candidates.sort(key=lambda u: haversine_km(inc["location"], u.get("last_location") or inc["location"]))
        r = candidates[0]
        await db.incidents.update_one({"id": incident_id}, {"$set": {
            "assigned_responder_id": r["id"], "assigned_responder_name": r["name"],
            "status": IncidentStatus.ASSIGNED.value, "timeline": inc["timeline"], "assigned_at": now_iso(),
        }})
        await notify(r["id"], "RESPONDER_ASSIGNED", "Emergency reassigned to you.", incident_id)
    else:
        await db.incidents.update_one({"id": incident_id}, {"$set": {"status": IncidentStatus.ESCALATED.value, "timeline": inc["timeline"], "escalated": True}})
        heads = await db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0}).to_list(20)
        for h in heads:
            await notify(h["id"], "ADMIN_ESCALATION", "Responder rejected & no backup available.", incident_id, Priority.CRITICAL)
    await log_audit(user, "reject_incident", "incident", incident_id, new={"reason": req.reason})
    return {"ok": True}


@api.post("/emergencies/{incident_id}/location")
async def responder_update_location(incident_id: str, req: ResponderLocationUpdate, ctx: dict = Depends(require_roles(Role.RESPONDER.value))):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc or inc.get("assigned_responder_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    loc = req.location.model_dump()
    # attach heading/speed/accuracy
    if req.heading is not None: loc["heading"] = req.heading
    if req.speed_mps is not None: loc["speed_mps"] = req.speed_mps
    if req.accuracy is not None: loc["accuracy"] = req.accuracy
    loc["updated_at"] = now_iso()
    upd = {"responder_location": loc}
    # append to history for replay
    hist = inc.get("location_history") or []
    hist.append(loc)
    upd["location_history"] = hist[-500:]
    # recalculate ETA from distance & speed
    dist_km = haversine_km(inc["location"], req.location.model_dump())
    upd["distance_km"] = round(dist_km, 2)
    computed_eta = agents.recalc_eta_minutes(dist_km, req.speed_mps)
    upd["eta_minutes"] = req.eta_minutes if req.eta_minutes is not None else computed_eta
    # promote status to en_route on first stream
    if inc["status"] == IncidentStatus.ACCEPTED.value:
        upd["status"] = IncidentStatus.EN_ROUTE.value
        upd["en_route_at"] = now_iso()
        add_timeline(inc, "Responder en route (live GPS streaming started)")
        upd["timeline"] = inc["timeline"]
        reporter = await get_user(inc["reporter_id"])
        r_lang = (reporter or {}).get("language") or "en"
        enr = agents.render_notification("RESPONDER_EN_ROUTE", r_lang, eta=upd['eta_minutes']) or f"Responder is on the way · ETA {upd['eta_minutes']} min."
        await notify(inc["reporter_id"], "RESPONDER_EN_ROUTE", enr, incident_id)
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_location": req.location.model_dump()}})
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    return {"ok": True, "eta_minutes": upd["eta_minutes"], "distance_km": upd["distance_km"]}


@api.post("/emergencies/{incident_id}/status")
async def update_status(incident_id: str, req: StatusUpdateRequest, ctx: dict = Depends(current_user_ctx)):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    role = user["role"]
    allowed = False
    if role == Role.RESPONDER.value and inc.get("assigned_responder_id") == user["id"]:
        allowed = True
    if role in (Role.DEPT_ADMIN.value, Role.HEAD_ADMIN.value):
        allowed = True
    if not allowed:
        raise HTTPException(403, "Forbidden")
    prev = inc["status"]
    upd = {"status": req.status.value}
    now = now_iso()
    if req.status == IncidentStatus.ARRIVED:
        upd["arrived_at"] = now
        add_timeline(inc, "Responder arrived")
        reporter = await get_user(inc["reporter_id"])
        r_lang = (reporter or {}).get("language") or "en"
        arv = agents.render_notification("RESPONDER_ARRIVED", r_lang) or "Responder has arrived."
        await notify(inc["reporter_id"], "RESPONDER_ARRIVED", arv, incident_id)
    elif req.status == IncidentStatus.RESOLVED:
        upd["resolved_at"] = now
        add_timeline(inc, f"Incident resolved by {user['name']}")
        reporter = await get_user(inc["reporter_id"])
        r_lang = (reporter or {}).get("language") or "en"
        rsv = agents.render_notification("INCIDENT_RESOLVED", r_lang) or "Your incident was marked resolved."
        await notify(inc["reporter_id"], "INCIDENT_RESOLVED", rsv, incident_id)
    elif req.status == IncidentStatus.REOPENED:
        upd["reopened_at"] = now
        add_timeline(inc, "Incident reopened")
    upd["timeline"] = inc["timeline"]
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    await log_audit(user, f"status:{prev}->{req.status.value}", "incident", incident_id, prev, req.status.value)
    return {"ok": True}


@api.post("/emergencies/{incident_id}/admin-override")
async def admin_override(incident_id: str, req: AdminOverrideRequest, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    user = await get_user(ctx["sub"])
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    upd = {}
    if req.department:
        upd["assigned_department"] = req.department.value
        add_timeline(inc, f"Admin re-routed to {req.department.value}")
    if req.priority:
        upd["priority"] = req.priority.value
        add_timeline(inc, f"Admin set priority {req.priority.value}")
    if req.responder_id:
        r = await db.users.find_one({"id": req.responder_id}, {"_id": 0})
        if r:
            upd["assigned_responder_id"] = r["id"]
            upd["assigned_responder_name"] = r["name"]
            upd["status"] = IncidentStatus.ASSIGNED.value
            add_timeline(inc, f"Admin assigned responder {r['name']}")
            await notify(r["id"], "RESPONDER_ASSIGNED", "Assigned by admin.", incident_id)
    if req.fraud_decision:
        add_timeline(inc, f"Fraud decision: {req.fraud_decision}")
        if req.fraud_decision == "approve":
            upd["status"] = IncidentStatus.ASSIGNING.value
            # trigger re-pipeline
            asyncio.create_task(process_incident_pipeline(incident_id))
        elif req.fraud_decision == "dismiss":
            upd["status"] = IncidentStatus.CANCELLED.value
    upd["timeline"] = inc["timeline"]
    await db.incidents.update_one({"id": incident_id}, {"$set": upd})
    await log_audit(user, "admin_override", "incident", incident_id, None, req.model_dump())
    return {"ok": True}


# ---------------- Notifications ----------------
@api.get("/notifications")
async def list_notifs(ctx: dict = Depends(current_user_ctx)):
    docs = await db.notifications.find({"user_id": ctx["sub"]}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return docs


@api.post("/notifications/{nid}/read")
async def read_notif(nid: str, ctx: dict = Depends(current_user_ctx)):
    await db.notifications.update_one({"id": nid, "user_id": ctx["sub"]}, {"$set": {"read_at": now_iso()}})
    return {"ok": True}


@api.post("/notifications/read-all")
async def read_all(ctx: dict = Depends(current_user_ctx)):
    await db.notifications.update_many({"user_id": ctx["sub"], "read_at": None}, {"$set": {"read_at": now_iso()}})
    return {"ok": True}


# ---------------- Responders ----------------
@api.post("/responders/availability")
async def set_availability(payload: dict, ctx: dict = Depends(require_roles(Role.RESPONDER.value))):
    await db.users.update_one({"id": ctx["sub"]}, {"$set": {"available": bool(payload.get("available", True))}})
    return {"ok": True}


@api.get("/responders")
async def list_responders(department: Optional[str] = None, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    q = {"role": Role.RESPONDER.value}
    if department:
        q["department"] = department
    docs = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(500)
    return docs


# ---------------- Admin ----------------
@api.get("/admin/metrics")
async def metrics(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    total_active = await db.incidents.count_documents({"status": {"$in": [s.value for s in [IncidentStatus.SUBMITTED, IncidentStatus.ANALYZING, IncidentStatus.CLASSIFIED, IncidentStatus.ASSIGNING, IncidentStatus.ASSIGNED, IncidentStatus.ACCEPTED, IncidentStatus.EN_ROUTE, IncidentStatus.ARRIVED]]}})
    critical = await db.incidents.count_documents({"priority": "critical", "status": {"$ne": "resolved"}})
    pending = await db.incidents.count_documents({"status": {"$in": ["submitted", "analyzing", "classified", "assigning"]}})
    resolved_today = await db.incidents.count_documents({"resolved_at": {"$gt": today}})
    fraud_flags = await db.incidents.count_documents({"status": "fraud_review"})
    online_responders = await db.users.count_documents({"role": Role.RESPONDER.value, "available": True})
    offline_responders = await db.users.count_documents({"role": Role.RESPONDER.value, "available": False})
    # avg response time (accepted_at - reported_at)
    docs = await db.incidents.find({"accepted_at": {"$ne": None}}, {"_id": 0, "reported_at": 1, "accepted_at": 1, "resolved_at": 1}).limit(500).to_list(500)
    def diff_min(a, b):
        try:
            return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60
        except Exception:
            return None
    accepts = [diff_min(d["reported_at"], d["accepted_at"]) for d in docs if d.get("accepted_at")]
    accepts = [x for x in accepts if x is not None]
    avg_accept = round(sum(accepts) / len(accepts), 1) if accepts else 0
    resolves = [diff_min(d["reported_at"], d["resolved_at"]) for d in docs if d.get("resolved_at")]
    resolves = [x for x in resolves if x is not None]
    avg_resolve = round(sum(resolves) / len(resolves), 1) if resolves else 0
    # By department
    by_dept = {}
    async for d in db.incidents.aggregate([{"$group": {"_id": "$assigned_department", "count": {"$sum": 1}}}]):
        by_dept[d["_id"] or "unknown"] = d["count"]
    return {
        "active": total_active, "critical": critical, "pending": pending,
        "resolved_today": resolved_today, "fraud_flags": fraud_flags,
        "online_responders": online_responders, "offline_responders": offline_responders,
        "avg_accept_min": avg_accept, "avg_resolve_min": avg_resolve,
        "by_department": by_dept,
    }


@api.get("/admin/incidents")
async def admin_incidents(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    return await db.incidents.find({}, {"_id": 0}).sort("reported_at", -1).limit(500).to_list(500)


@api.get("/admin/fraud")
async def admin_fraud(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    return await db.incidents.find({"$or": [{"status": "fraud_review"}, {"fraud_analysis.risk_level": {"$in": ["high", "critical"]}}]}, {"_id": 0}).sort("reported_at", -1).limit(200).to_list(200)


@api.get("/admin/audit")
async def admin_audit(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    return await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(300).to_list(300)


@api.get("/admin/responders")
async def admin_all_responders(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    docs = await db.users.find({"role": Role.RESPONDER.value}, {"_id": 0, "password_hash": 0}).to_list(500)
    return docs


# ---------------- AI Assistant ----------------
@api.post("/ai/assistant")
async def ai_assistant(req: AssistantChatRequest, ctx: dict = Depends(current_user_ctx)):
    inc_ctx = None
    if req.incident_id:
        inc = await db.incidents.find_one({"id": req.incident_id}, {"_id": 0})
        if inc:
            inc_ctx = {
                "category": (inc.get("ai_analysis") or {}).get("category"),
                "department": inc.get("assigned_department"),
                "priority": inc.get("priority"),
                "status": inc.get("status"),
                "eta_minutes": inc.get("eta_minutes"),
            }
    session = req.session_id or f"assist-{ctx['sub']}"
    reply = await agents.assistant_reply(req.message, inc_ctx, session)
    return {"reply": reply}


# ---------------- Sync ----------------
@api.post("/sync/queue")
async def sync_queue(payload: dict, ctx: dict = Depends(current_user_ctx)):
    """Accept batched offline operations."""
    ops = payload.get("operations", [])
    results = []
    for op in ops:
        try:
            if op.get("type") == "report":
                req = ReportRequest(**op.get("payload", {}))
                r = await create_emergency(req, ctx)  # reuses dedupe
                results.append({"op_id": op.get("op_id"), "status": "synced", "incident_id": r["id"]})
            else:
                results.append({"op_id": op.get("op_id"), "status": "failed", "error": "unknown type"})
        except Exception as e:
            results.append({"op_id": op.get("op_id"), "status": "failed", "error": str(e)})
    return {"results": results}


# ---------------- Seed demo ----------------
@api.post("/dev/seed")
async def seed():
    """Seed demo users. Idempotent."""
    demo = [
        ("Aarav Student", "student@campus.edu", "Campus@2026", Role.STUDENT, None),
        ("Priya Medic", "medic@campus.edu", "Campus@2026", Role.RESPONDER, Department.MEDICAL),
        ("Rohan Fire", "fire@campus.edu", "Campus@2026", Role.RESPONDER, Department.FIRE_SAFETY),
        ("Meera Security", "security@campus.edu", "Campus@2026", Role.RESPONDER, Department.SECURITY),
        ("Vikram Elec", "elec@campus.edu", "Campus@2026", Role.RESPONDER, Department.ELECTRICAL),
        ("Anita Fac", "facilities@campus.edu", "Campus@2026", Role.RESPONDER, Department.FACILITIES),
        ("Kabir Transport", "transport@campus.edu", "Campus@2026", Role.RESPONDER, Department.TRANSPORT),
        ("Dept Head Medical", "deptmed@campus.edu", "Campus@2026", Role.DEPT_ADMIN, Department.MEDICAL),
        ("Head Admin", "admin@campus.edu", "Campus@2026", Role.HEAD_ADMIN, None),
    ]
    created = []
    for name, email, pwd, role, dept in demo:
        if await db.users.find_one({"email": email}):
            continue
        doc = {
            "id": uid(), "name": name, "email": email,
            "password_hash": hash_password(pwd),
            "role": role.value, "department": dept.value if dept else None,
            "available": True, "created_at": now_iso(),
            "last_location": {"lat": 12.9716 + (hash(email) % 100) / 10000, "lng": 77.5946 + (hash(email) % 100) / 10000, "address": "Campus"},
        }
        await db.users.insert_one(doc)
        created.append(email)
    return {"created": created, "total_demo_users": len(demo)}


@api.get("/")
async def root():
    return {"app": "CampusResQ AI", "status": "ok"}


# ---------------- Push subscription ----------------
@api.get("/push/vapid-public")
async def push_public():
    return {"public_key": VAPID_PUBLIC}


@api.post("/push/subscribe")
async def push_subscribe(req: PushSubscriptionRequest, ctx: dict = Depends(current_user_ctx)):
    doc = {"user_id": ctx["sub"], "endpoint": req.endpoint, "keys": req.keys, "created_at": now_iso()}
    await db.push_subscriptions.update_one({"endpoint": req.endpoint}, {"$set": doc}, upsert=True)
    return {"ok": True}


@api.post("/push/unsubscribe")
async def push_unsubscribe(payload: dict, ctx: dict = Depends(current_user_ctx)):
    ep = payload.get("endpoint")
    if ep:
        await db.push_subscriptions.delete_one({"endpoint": ep, "user_id": ctx["sub"]})
    return {"ok": True}


# ---------------- Teams (backup team configuration) ----------------
@api.get("/teams")
async def list_teams(department: Optional[str] = None, ctx: dict = Depends(current_user_ctx)):
    q = {}
    if department:
        q["department"] = department
    elif ctx.get("role") in (Role.DEPT_ADMIN.value, Role.DEPT_PERSONNEL.value):
        user = await get_user(ctx["sub"])
        q["department"] = user.get("department")
    elif ctx.get("role") not in (Role.HEAD_ADMIN.value,):
        raise HTTPException(403, "Forbidden")
    return await db.teams.find(q, {"_id": 0}).to_list(200)


@api.post("/teams")
async def create_team(req: TeamCreateRequest, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    user = await get_user(ctx["sub"])
    if user["role"] == Role.DEPT_ADMIN.value and user.get("department") != req.department.value:
        raise HTTPException(403, "Cannot manage other departments")
    if req.kind not in ("primary", "backup"):
        raise HTTPException(400, "kind must be primary or backup")
    # existing team of same kind+dept -> replace by upsert with same name? Allow multiple? Enforce one primary + one backup per dept.
    existing = await db.teams.find_one({"department": req.department.value, "kind": req.kind}, {"_id": 0})
    if existing:
        raise HTTPException(409, f"A {req.kind} team already exists for {req.department.value}. Update it instead.")
    # resolve members
    members = []
    if req.member_ids:
        users = await db.users.find({"id": {"$in": req.member_ids}, "role": Role.RESPONDER.value, "department": req.department.value}, {"_id": 0, "password_hash": 0}).to_list(200)
        for u in users:
            members.append({"user_id": u["id"], "name": u["name"], "role_title": u.get("role_title"), "skills": u.get("skills", [])})
    team = Team(department=req.department, kind=req.kind, name=req.name, members=members, acceptance_timeout_sec=req.acceptance_timeout_sec).model_dump()
    await db.teams.insert_one(team)
    await log_audit(user, "team_created", "team", team["id"], None, {"name": team["name"], "kind": team["kind"]})
    team.pop("_id", None)
    return team


@api.put("/teams/{team_id}")
async def update_team(team_id: str, req: TeamUpdateRequest, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    user = await get_user(ctx["sub"])
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(404, "Not found")
    if user["role"] == Role.DEPT_ADMIN.value and user.get("department") != team["department"]:
        raise HTTPException(403, "Forbidden")
    upd = {}
    if req.name is not None: upd["name"] = req.name
    if req.kind is not None: upd["kind"] = req.kind
    if req.acceptance_timeout_sec is not None: upd["acceptance_timeout_sec"] = req.acceptance_timeout_sec
    if req.member_ids is not None:
        users = await db.users.find({"id": {"$in": req.member_ids}, "role": Role.RESPONDER.value, "department": team["department"]}, {"_id": 0, "password_hash": 0}).to_list(200)
        upd["members"] = [{"user_id": u["id"], "name": u["name"], "role_title": u.get("role_title"), "skills": u.get("skills", [])} for u in users]
    await db.teams.update_one({"id": team_id}, {"$set": upd})
    await log_audit(user, "team_updated", "team", team_id, team, upd)
    return {"ok": True}


@api.delete("/teams/{team_id}")
async def delete_team(team_id: str, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    user = await get_user(ctx["sub"])
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(404, "Not found")
    if user["role"] == Role.DEPT_ADMIN.value and user.get("department") != team["department"]:
        raise HTTPException(403, "Forbidden")
    await db.teams.delete_one({"id": team_id})
    await log_audit(user, "team_deleted", "team", team_id, team, None)
    return {"ok": True}


@api.put("/responders/{user_id}/skills")
async def set_responder_skills(user_id: str, req: ResponderSkillsUpdate, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    admin = await get_user(ctx["sub"])
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if admin["role"] == Role.DEPT_ADMIN.value and admin.get("department") != target.get("department"):
        raise HTTPException(403, "Forbidden")
    await db.users.update_one({"id": user_id}, {"$set": {"skills": req.skills}})
    await log_audit(admin, "responder_skills_updated", "user", user_id, target.get("skills"), req.skills)
    return {"ok": True}


# ---------------- Admin config (SOS radius etc.) ----------------
@api.get("/admin/config")
async def get_config(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    cfg = await db.system_config.find_one({"id": "global"}, {"_id": 0})
    return cfg or {"id": "global", "sos_radius_m": 2000, "default_acceptance_timeout_sec": 60}


@api.put("/admin/config")
async def put_config(payload: dict, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    doc = {"id": "global",
           "sos_radius_m": int(payload.get("sos_radius_m", 2000)),
           "default_acceptance_timeout_sec": int(payload.get("default_acceptance_timeout_sec", 60))}
    await db.system_config.update_one({"id": "global"}, {"$set": doc}, upsert=True)
    return doc


# ---------------- Heatmap ----------------
@api.get("/admin/heatmap")
async def admin_heatmap(hours: int = 168, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    q = {"reported_at": {"$gte": since}}
    if ctx.get("role") == Role.DEPT_ADMIN.value:
        user = await get_user(ctx["sub"])
        q["assigned_department"] = user.get("department")
    points = []
    async for i in db.incidents.find(q, {"_id": 0, "location": 1, "priority": 1, "assigned_department": 1, "reported_at": 1, "ai_analysis": 1}):
        loc = i.get("location") or {}
        if loc.get("lat") is None: continue
        weight = {"low": 0.3, "medium": 0.55, "high": 0.8, "critical": 1.0}.get(i.get("priority") or "medium", 0.5)
        points.append({
            "lat": loc["lat"], "lng": loc["lng"], "weight": weight,
            "department": i.get("assigned_department"),
            "category": (i.get("ai_analysis") or {}).get("category"),
            "at": i.get("reported_at"),
        })
    return {"points": points, "window_hours": hours}


# ---------------- Incident Replay ----------------
@api.get("/admin/incidents/{incident_id}/replay")
async def incident_replay(incident_id: str, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    return {
        "id": inc["id"], "description": inc["description"], "reporter_name": inc.get("reporter_name"),
        "location": inc.get("location"),
        "status": inc.get("status"),
        "priority": inc.get("priority"),
        "ai_analysis": inc.get("ai_analysis"),
        "fraud_analysis": inc.get("fraud_analysis"),
        "media_forensics": inc.get("media_forensics"),
        "timeline": inc.get("timeline", []),
        "location_history": inc.get("location_history", []),
        "assigned_responder_name": inc.get("assigned_responder_name"),
        "reported_at": inc.get("reported_at"),
        "resolved_at": inc.get("resolved_at"),
    }


# ---------------- Voice SOS ----------------
@api.post("/voice/sos")
async def voice_sos(payload: dict, ctx: dict = Depends(current_user_ctx)):
    """Accept a client-transcribed voice SOS + location and create an SOS incident."""
    transcript = (payload.get("transcript") or "").strip()
    loc = payload.get("location")
    if not transcript:
        raise HTTPException(400, "Empty transcript")
    if not loc or "lat" not in loc:
        raise HTTPException(400, "Location required")
    user = await get_user(ctx["sub"])
    inc = Incident(
        reporter_id=user["id"], reporter_name=user["name"],
        description=transcript, location=Location(**loc),
        is_sos=True, voice_transcript=transcript,
    ).model_dump()
    add_timeline(inc, f"VOICE SOS received: '{transcript[:80]}...'")
    await db.incidents.insert_one(inc)
    await notify(user["id"], "REPORT_CREATED", "Voice SOS received. Analyzing…", inc["id"], Priority.CRITICAL)
    await log_audit(user, "voice_sos_created", "incident", inc["id"], None, {"transcript": transcript})
    asyncio.create_task(process_incident_pipeline(inc["id"]))
    inc.pop("_id", None)
    return inc


app.include_router(api)


# ---------------- Announcements (Faculty-Alert Broadcast) ----------------
@api.post("/announcements")
async def create_announcement(payload: dict, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    title = (payload.get("title") or "").strip()[:120]
    body = (payload.get("body") or "").strip()[:2000]
    priority_raw = (payload.get("priority") or "high").lower()
    if priority_raw not in ("low", "medium", "high", "critical"):
        priority_raw = "high"
    if not title or not body:
        raise HTTPException(400, "title and body required")
    user = await get_user(ctx["sub"])
    ann_id = uid()
    doc = {"id": ann_id, "title": title, "body": body, "priority": priority_raw,
           "author_id": user["id"], "author_name": user["name"], "created_at": now_iso()}
    await db.announcements.insert_one(doc)
    # broadcast to every registered user
    async for u in db.users.find({}, {"_id": 0, "id": 1}):
        await notify(u["id"], "CAMPUS_ANNOUNCEMENT", f"[{title}] {body[:120]}", None, Priority(priority_raw))
    await log_audit(user, "announcement_created", "announcement", ann_id, None, {"title": title})
    doc.pop("_id", None)
    return doc


@api.get("/announcements")
async def list_announcements(ctx: dict = Depends(current_user_ctx)):
    return await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)


# ---------------- Peer-Buddy ----------------
@api.put("/users/me")
async def update_me(payload: dict, ctx: dict = Depends(current_user_ctx)):
    upd = {}
    if "buddy_email" in payload:
        be = (payload.get("buddy_email") or "").strip().lower() or None
        if be and "@" not in be:
            raise HTTPException(400, "Invalid buddy email")
        upd["buddy_email"] = be
    if "buddy_phone" in payload:
        upd["buddy_phone"] = (payload.get("buddy_phone") or "").strip() or None
    if "language" in payload:
        upd["language"] = (payload.get("language") or "en").strip() or "en"
    if "buddy_name" in payload:
        upd["buddy_name"] = (payload.get("buddy_name") or "").strip() or None
    if "phone" in payload:
        upd["phone"] = (payload.get("phone") or "").strip() or None
    if upd:
        await db.users.update_one({"id": ctx["sub"]}, {"$set": upd})
    user = await get_user(ctx["sub"])
    user.pop("password_hash", None)
    return user


async def notify_buddy_of_sos(reporter: dict, incident_id: str, ai_category: Optional[str]):
    buddy_email = reporter.get("buddy_email")
    buddy_phone = reporter.get("buddy_phone")
    if not buddy_email and not buddy_phone:
        return
    lang = reporter.get("language") or "en"
    L = agents.buddy_email_labels(lang)
    safe_name = html_escape(reporter.get("name") or "Your buddy")
    # localise category using stored translation if available
    ai_local = None
    try:
        inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0, "ai_analysis_localized": 1})
        ai_local = ((inc or {}).get("ai_analysis_localized") or {}).get(lang)
    except Exception:
        pass
    cat_display = (ai_local or {}).get("category") or ai_category or "Emergency"
    safe_cat = html_escape(cat_display)
    safe_time = html_escape(datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"))
    subject = L["subject"].format(name=reporter.get("name", "a friend"))
    html = (
        '<table role="presentation" width="100%" style="max-width:560px;margin:auto;background:#f8fafc;">'
        '<tr><td style="padding:24px;font-family:Arial,sans-serif;color:#0f172a">'
        f'<h2 style="margin:0 0 8px 0;color:#dc2626">{html_escape(L["heading"])}</h2>'
        f'<p style="margin:0 0 16px 0">{L["intro"].format(name=safe_name)}</p>'
        '<table role="presentation" width="100%" style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:16px">'
        f'<tr><td><strong>{html_escape(L["category"])}</strong>: {safe_cat}</td></tr>'
        f'<tr><td><strong>{html_escape(L["reported_at"])}</strong>: {safe_time}</td></tr>'
        f'<tr><td><strong>{html_escape(L["status"])}</strong>: {html_escape(L["status_value"])}</td></tr></table>'
        f'<p style="margin:16px 0 0 0;font-size:12px;color:#64748b">{L["footer"].format(name=safe_name)}</p>'
        f'<p style="font-size:12px;color:#94a3b8">Sent by {html_escape(os.environ.get("EMAIL_FROM_NAME", "CampusResQ AI"))}.</p>'
        '</td></tr></table>')
    email_ok = False
    if buddy_email:
        r = await send_email(to=buddy_email, subject=subject, html=html)
        email_ok = r is not None
    # SMS fallback
    if buddy_phone and (not email_ok or not buddy_email):
        sms_body = f"CampusResQ AI: {reporter.get('name','A friend')} SOS ({cat_display}). Rescue team notified."
        sms_sid = await send_sms(to=buddy_phone, body=sms_body)
        if sms_sid:
            log.info(f"buddy SMS sent sid={sms_sid}")


# ---------------- Weekly Digest cron ----------------
@app.post("/api/cron/weekly-digest")
async def weekly_digest_cron(request: Request):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {WEBHOOK_CRON_SECRET}"
    if not WEBHOOK_CRON_SECRET or not secrets.compare_digest(auth, expected):
        raise HTTPException(401, "Unauthorized")
    run_id = request.headers.get("x-webhook-id", uid())
    # dedupe
    if await db.cron_runs.find_one({"run_id": run_id}, {"_id": 0}):
        return {"ok": True, "dup": True}
    await db.cron_runs.insert_one({"run_id": run_id, "at": now_iso(), "kind": "weekly-digest"})
    asyncio.create_task(_do_weekly_digest())
    return {"ok": True, "queued": True, "run_id": run_id}


async def _do_weekly_digest():
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        total = await db.incidents.count_documents({"reported_at": {"$gte": since}})
        resolved = await db.incidents.count_documents({"resolved_at": {"$gte": since}})
        critical = await db.incidents.count_documents({"reported_at": {"$gte": since}, "priority": "critical"})
        fraud_flags = await db.incidents.count_documents({"reported_at": {"$gte": since}, "fraud_analysis.risk_level": {"$in": ["high", "critical"]}})
        # avg response
        docs = await db.incidents.find({"reported_at": {"$gte": since}, "accepted_at": {"$ne": None}}, {"_id": 0, "reported_at": 1, "accepted_at": 1}).to_list(1000)
        def diff_min(a, b):
            try: return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60
            except Exception: return None
        accepts = [x for x in (diff_min(d["reported_at"], d["accepted_at"]) for d in docs) if x is not None]
        avg_accept = round(sum(accepts) / len(accepts), 1) if accepts else 0
        # by dept
        dept_agg = []
        async for d in db.incidents.aggregate([
            {"$match": {"reported_at": {"$gte": since}}},
            {"$group": {"_id": "$assigned_department", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}]):
            dept_agg.append(d)
        dept_rows = "".join(
            f'<tr><td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">{html_escape((d["_id"] or "unknown").replace("_"," ").title())}</td>'
            f'<td style="padding:6px 12px;border-bottom:1px solid #e2e8f0;text-align:right">{d["count"]}</td></tr>'
            for d in dept_agg[:8]) or '<tr><td colspan="2" style="padding:12px;color:#64748b">No incidents this week.</td></tr>'
        sent = 0
        async for u in db.users.find({"role": Role.HEAD_ADMIN.value}, {"_id": 0, "email": 1, "name": 1, "language": 1}):
            lang = u.get("language") or "en"
            L = agents.digest_email_labels(lang)
            html = (
                '<table role="presentation" width="100%" style="max-width:640px;margin:auto;background:#f8fafc">'
                '<tr><td style="padding:24px;font-family:Arial,sans-serif;color:#0f172a">'
                f'<h2 style="margin:0 0 8px 0;color:#0891b2">{html_escape(L["heading"])}</h2>'
                f'<p style="margin:0 0 16px 0;color:#64748b">{L["window"].format(date=html_escape(datetime.now(timezone.utc).strftime("%d %b %Y")))}</p>'
                '<table role="presentation" width="100%" style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px;margin-bottom:16px">'
                f'<tr><td style="padding:12px"><strong>{html_escape(L["incidents"])}</strong>: {total}</td>'
                f'<td style="padding:12px"><strong>{html_escape(L["resolved"])}</strong>: {resolved}</td></tr>'
                f'<tr><td style="padding:12px"><strong>{html_escape(L["critical"])}</strong>: {critical}</td>'
                f'<td style="padding:12px"><strong>{html_escape(L["fraud"])}</strong>: {fraud_flags}</td></tr>'
                f'<tr><td style="padding:12px" colspan="2"><strong>{html_escape(L["avg_accept"])}</strong>: {avg_accept} min</td></tr></table>'
                f'<h3 style="margin:16px 0 8px 0">{html_escape(L["by_dept"])}</h3>'
                '<table role="presentation" width="100%" style="background:#fff;border:1px solid #e2e8f0;border-radius:8px">'
                + dept_rows + '</table>'
                f'<p style="margin:24px 0 0 0;font-size:12px;color:#94a3b8">{html_escape(L["footer"])}</p></td></tr></table>')
            r = await send_email(to=u["email"], subject=L["subject"], html=html)
            if r: sent += 1
        log.info(f"weekly-digest sent to {sent} head admins")
    except Exception as e:
        log.exception(f"weekly-digest failed: {e}")


# Endpoint for admin to trigger digest manually (dev/demo)
@api.post("/admin/weekly-digest/test")
async def admin_trigger_digest(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    asyncio.create_task(_do_weekly_digest())
    return {"ok": True, "queued": True}


# ---------------- Wellness Check-in ----------------
@app.post("/api/cron/wellness-check")
async def wellness_check_cron(request: Request):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {WEBHOOK_CRON_SECRET}"
    if not WEBHOOK_CRON_SECRET or not secrets.compare_digest(auth, expected):
        raise HTTPException(401, "Unauthorized")
    run_id = request.headers.get("x-webhook-id", uid())
    if await db.cron_runs.find_one({"run_id": run_id}, {"_id": 0}):
        return {"ok": True, "dup": True}
    await db.cron_runs.insert_one({"run_id": run_id, "at": now_iso(), "kind": "wellness-check"})
    asyncio.create_task(_do_wellness_checks())
    return {"ok": True, "queued": True, "run_id": run_id}


async def _do_wellness_checks():
    try:
        now = datetime.now(timezone.utc)
        window_end = (now - timedelta(hours=24)).isoformat()
        window_start = (now - timedelta(hours=25)).isoformat()
        # medical incidents resolved 24-25h ago and not yet checked
        q = {"resolved_at": {"$gte": window_start, "$lt": window_end},
             "assigned_department": "medical",
             "wellness_checked": {"$ne": True}}
        count = 0
        async for inc in db.incidents.find(q, {"_id": 0}):
            await notify(inc["reporter_id"], "WELLNESS_CHECKIN",
                         "Checking in — how are you now? Tap to share an update with the medical team.",
                         inc["id"], Priority.MEDIUM)
            await db.incidents.update_one({"id": inc["id"]}, {"$set": {"wellness_checked": True, "wellness_checked_at": now_iso()}})
            add_timeline(inc, "Wellness check-in DM sent to reporter (24h post-resolution)")
            await db.incidents.update_one({"id": inc["id"]}, {"$set": {"timeline": inc["timeline"]}})
            count += 1
        log.info(f"wellness-check DMs sent: {count}")
    except Exception as e:
        log.exception(f"wellness-check failed: {e}")


@api.post("/emergencies/{incident_id}/wellness-reply")
async def wellness_reply(incident_id: str, payload: dict, ctx: dict = Depends(current_user_ctx)):
    inc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not inc:
        raise HTTPException(404, "Not found")
    if inc["reporter_id"] != ctx["sub"]:
        raise HTTPException(403, "Only the reporter can reply")
    mood = (payload.get("mood") or "").strip()[:20]  # ok | recovering | needs_help
    note = (payload.get("note") or "").strip()[:500]
    reply = {"mood": mood, "note": note, "at": now_iso()}
    add_timeline(inc, f"Wellness reply: {mood} · {note[:60]}")
    await db.incidents.update_one({"id": incident_id}, {"$set": {"wellness_reply": reply, "timeline": inc["timeline"]}})
    # if needs help, ping medical department
    if mood == "needs_help":
        async for u in db.users.find({"role": {"$in": [Role.RESPONDER.value, Role.DEPT_ADMIN.value]}, "department": "medical"}, {"_id": 0, "id": 1}):
            await notify(u["id"], "WELLNESS_ALERT", f"Post-incident wellness reply: reporter reports NEEDS HELP. Note: {note[:120]}", incident_id, Priority.HIGH)
    return {"ok": True}


# Manual trigger for demo
@api.post("/admin/wellness-check/test")
async def admin_trigger_wellness(ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value))):
    asyncio.create_task(_do_wellness_checks())
    return {"ok": True, "queued": True}


# ---------------- Wellness trend stats ----------------
@api.get("/admin/wellness-stats")
async def wellness_stats(days: int = 7, ctx: dict = Depends(require_roles(Role.HEAD_ADMIN.value, Role.DEPT_ADMIN.value))):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = {"wellness_reply.at": {"$gte": since}}
    if ctx.get("role") == Role.DEPT_ADMIN.value:
        user = await get_user(ctx["sub"])
        q["assigned_department"] = user.get("department")
    counts = {"ok": 0, "recovering": 0, "needs_help": 0, "other": 0}
    recent = []
    async for i in db.incidents.find(q, {"_id": 0, "wellness_reply": 1, "id": 1, "reporter_name": 1, "ai_analysis": 1, "resolved_at": 1}):
        wr = i.get("wellness_reply") or {}
        mood = (wr.get("mood") or "").lower()
        if mood in counts: counts[mood] += 1
        else: counts["other"] += 1
        recent.append({"id": i["id"], "reporter": i.get("reporter_name"),
                       "category": (i.get("ai_analysis") or {}).get("category"),
                       "mood": mood, "note": (wr.get("note") or "")[:120], "at": wr.get("at")})
    recent.sort(key=lambda x: x.get("at") or "", reverse=True)
    total = sum(counts.values())
    return {"counts": counts, "total": total, "days": days, "recent": recent[:20]}


app.include_router(api)




# ---------------- WebSocket endpoint ----------------
@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    try:
        payload = decode_token(token)
    except Exception:
        await ws.close(code=1008)
        return
    uid = payload["sub"]
    await ws_manager.connect(uid, ws)
    try:
        await ws.send_json({"event": "connected", "user_id": uid})
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if msg == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                # keepalive
                try: await ws.send_text("ping")
                except Exception: break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        ws_manager.disconnect(uid, ws)


# ---------------- Startup: indexes ----------------
@app.on_event("startup")
async def _startup_indexes():
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index(
            "registration_number", unique=True,
            partialFilterExpression={"registration_number": {"$type": "string"}},
        )
        await db.incidents.create_index("id", unique=True)
        await db.incidents.create_index("reporter_id")
        await db.incidents.create_index("assigned_department")
        await db.incidents.create_index("status")
        await db.teams.create_index([("department", 1), ("kind", 1)], unique=True)
        await db.push_subscriptions.create_index("endpoint", unique=True)
        log.info("indexes ensured")
    except Exception as e:
        log.warning(f"index setup failed: {e}")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown():
    client.close()
