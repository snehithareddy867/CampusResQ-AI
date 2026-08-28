import React from "react";
import Layout from "@/components/Layout";
import { Sparkles, ShieldAlert, Users, Bell, Radio, MapPin, Zap, HeartPulse } from "lucide-react";

const AGENTS = [
  { icon: Sparkles, name: "Classifier Agent", model: "Claude Sonnet 4.6 (via Emergent LLM key)", where: "backend/agents.py · classify_incident()", triggeredBy: "process_incident_pipeline on every new report", input: "description, is_sos flag, category hint", output: "category, department, priority (low|medium|high|critical), confidence, safety_instructions[]", fallback: "Rule-based keyword scoring across 8 departments" },
  { icon: ShieldAlert, name: "Fraud Detection Agent", model: "Claude Sonnet 4.6 + rule-based scoring", where: "backend/agents.py · fraud_analyze()", triggeredBy: "Right after classification for every incident", input: "description, reporter's recent report count (24h), duplicate description flag", output: "risk_score (0..1), risk_level (low|medium|high|critical), reasons[], recommended_action", fallback: "Heuristic: dup×0.5 + high-rate×0.2 + short-desc×0.2 + prank-words×0.3" },
  { icon: Zap, name: "Media Forensics Agent", model: "Claude Sonnet 4.6 + SHA-256 dedupe + file heuristics", where: "backend/agents.py · media_forensics()", triggeredBy: "After fraud, only if evidence attached", input: "description + metadata of each evidence item (mime, size, hash)", output: "verdict (authentic|suspicious|likely_manipulated|insufficient_data), confidence, reasons[], per_item[]", fallback: "Duplicate hash × small-size heuristic overrides authenticity" },
  { icon: MapPin, name: "Assignment & Proximity Agent", model: "Deterministic (haversine distance + availability)", where: "backend/server.py · process_incident_pipeline() SOS branch", triggeredBy: "SOS incidents", input: "incident location, all responders in the classified dept with last_location", output: "sorted candidate list within sos_radius_m (config)", fallback: "Department-wide broadcast if none in radius" },
  { icon: Users, name: "Escalation Watchdog", model: "Deterministic timer + team-config lookup", where: "backend/server.py · _escalation_watchdog()", triggeredBy: "60-second (configurable) timer per waiting incident", input: "incident id, primary team acceptance_timeout_sec", output: "Escalation state + backup-team notification", fallback: "Any available responders + all head admins" },
  { icon: HeartPulse, name: "AI Safety Assistant", model: "Claude Sonnet 4.6 (streaming-capable)", where: "backend/agents.py · assistant_reply()  +  frontend AssistantChat", triggeredBy: "User opens /assistant or messages during an active incident", input: "user message + current incident context (category, dept, ETA)", output: "Short (≤150 words) safety guidance in Markdown-ish bullets", fallback: "Curated per-department safety tips" },
  { icon: Bell, name: "Notification / Push Agent", model: "Deterministic + pywebpush (VAPID)", where: "backend/server.py · notify() + send_push_to_user()", triggeredBy: "Every state change: REPORT_CREATED, AI_CLASSIFIED, DEPT_NEW_INCIDENT, RESPONDER_ACCEPTED, RESPONDER_EN_ROUTE, RESPONDER_ARRIVED, INCIDENT_RESOLVED, ADMIN_ESCALATION, SOS_NEARBY, SOS_TAKEN, MEDIA_FORENSICS_ALERT, CONFIRM_SAFETY, BACKUP_ESCALATION, REPORTER_SAFE", input: "user_id, type, message, incident_id, priority", output: "In-app row + WS event + Web Push over service worker", fallback: "In-app only if push permission denied" },
  { icon: Radio, name: "Realtime Broadcaster", model: "FastAPI WebSockets", where: "backend/server.py · WSManager + broadcast_incident_update()", triggeredBy: "Every notify + accept / location / status change", input: "incident id, event type", output: "JSON event pushed to reporter + assigned responder + department staff + head admins", fallback: "Client polling every 6–8 s if WS drops (auto-reconnects with 3 s backoff)" },
];

export default function AgentsInfo() {
  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Architecture</p>
          <h1 className="font-display text-3xl font-extrabold mt-1 flex items-center gap-2"><Sparkles className="w-6 h-6 text-cyan-400"/>AI Agents in this system</h1>
          <p className="text-sm text-slate-400 mt-2">~90% automated triage + coordination, humans remain the final signature on Accept / Complete / Safe. All LLM calls use Claude Sonnet 4.6 via the Emergent Universal LLM key — no keys are exposed to the browser.</p>
        </div>
        <div className="grid gap-4">
          {AGENTS.map((a) => (
            <div key={a.name} data-testid={`agent-${a.name}`} className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center shrink-0"><a.icon className="w-5 h-5 text-cyan-300"/></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-display font-bold text-lg">{a.name}</h3>
                    <span className="text-[11px] uppercase font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-mono">{a.model}</span>
                  </div>
                  <p className="text-xs text-slate-500 font-mono mt-1">{a.where}</p>
                  <div className="grid md:grid-cols-2 gap-3 mt-3 text-sm">
                    <div><div className="text-[11px] uppercase font-bold text-slate-500 tracking-widest mb-1">Triggered by</div><div className="text-slate-300">{a.triggeredBy}</div></div>
                    <div><div className="text-[11px] uppercase font-bold text-slate-500 tracking-widest mb-1">Input</div><div className="text-slate-300">{a.input}</div></div>
                    <div className="md:col-span-2"><div className="text-[11px] uppercase font-bold text-slate-500 tracking-widest mb-1">Output</div><div className="text-slate-300">{a.output}</div></div>
                    <div className="md:col-span-2"><div className="text-[11px] uppercase font-bold text-slate-500 tracking-widest mb-1">Fallback (if AI unavailable)</div><div className="text-slate-400">{a.fallback}</div></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
