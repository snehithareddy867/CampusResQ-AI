# CampusResQ AI — PRD

## Problem
AI-powered, offline-aware campus emergency response with strict human-in-the-loop acceptance.

## Roles
Student · Responder · Dept Personnel · Dept Admin · Head Admin (RBAC enforced backend-side).

## Implemented (2026-02)
- JWT auth + role-based routing (portal-per-role)
- Emergency reporting (text/image/audio/video/location + SOS press-and-hold)
- Multi-agent AI pipeline via Claude Sonnet 4.6 (EMERGENT_LLM_KEY): Classifier, Fraud, Assistant + rule-based fallbacks
- WAITING_FOR_ACCEPTANCE state — AI recommends department; NO auto-assign; humans must click Accept
- Atomic accept endpoint (409 on race) + 60-second backup escalation watchdog
- Notifications, in-app; timeline audit per incident; global audit log
- Live map (Leaflet + OSM) with responder/reporter pins & route line
- Admin Command Center (metrics, live map, dept chart, incidents, fraud queue, responders table, audit)
- Department Dashboard, Responder Dashboard (availability toggle, accept/reject/arrived/resolved)
- AI Safety Assistant chat (Claude Sonnet 4.6)
- Offline queue (localStorage) + /api/sync/queue with client_op_id dedupe
- Seeded demo accounts (Campus@2026)

## Backlog (P0/P1)
- Web Push (Service Worker + VAPID) for background/closed-tab notifications
- SOS proximity broadcast + browser emergency tone
- Live GPS streaming from responder device (interval + heading/speed) + real routing ETA
- Media forensics agent (fake image/video/audio detection)
- Backup team configuration UI for Dept Heads
- Responder skills + skill-aware matching
- Unique registration numbers (student 24-1-FK, faculty FAC-XXXX)
- Full state machine validation with allowed transitions
- Resolution confirmation from both sides (I'm safe / Response completed)
- Real WebSocket real-time push (currently polling every 4-5s)
