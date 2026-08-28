import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Layout from "@/components/Layout";
import LiveMap from "@/components/LiveMap";
import client from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, ShieldAlert, Sparkles, Clock, ShieldCheck, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { subscribeWS } from "@/lib/ws";
import { getLang } from "@/lib/i18n";

export default function EmergencyDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [inc, setInc] = useState(null);

  const load = () => client.get(`/emergencies/${id}`).then(r => setInc(r.data)).catch(()=>{});
  useEffect(() => {
    load();
    const t = setInterval(load, 6000);
    // realtime: refetch on any related ws event
    const unsub = subscribeWS((evt) => {
      if (evt?.incident_id === id || evt?.event === "notification") load();
    });
    return () => { clearInterval(t); unsub(); };
  }, [id]);

  const confirmSafe = async () => {
    try { await client.post(`/emergencies/${id}/reporter-safe`); toast.success("You confirmed safe. Thank you."); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };
  const responderComplete = async () => {
    try { await client.post(`/emergencies/${id}/responder-complete`); toast.success("Marked response complete."); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  if (!inc) return <Layout><div className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 animate-spin inline"/></div></Layout>;

  const isReporter = user?.id === inc.reporter_id;
  const isResponder = user?.id === inc.assigned_responder_id;
  const activeForResolution = ["accepted", "en_route", "arrived", "resolution_pending"].includes(inc.status);
  const uiLang = getLang();
  const localAI = isReporter ? (inc.ai_analysis_localized || {})[uiLang] : null;
  const shownAI = inc.ai_analysis ? {
    ...inc.ai_analysis,
    category: localAI?.category || inc.ai_analysis.category,
    reason: localAI?.reason || inc.ai_analysis.reason,
    safety_instructions: (localAI?.safety_instructions?.length ? localAI.safety_instructions : inc.ai_analysis.safety_instructions),
  } : null;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className="bg-slate-100 text-slate-700 border">{inc.status?.replace(/_/g," ")}</Badge>
          {inc.priority && <Badge className={inc.priority === "critical" ? "bg-red-100 text-red-800 border border-red-300" : "bg-blue-50 text-blue-700"}>{inc.priority}</Badge>}
          {inc.is_sos && <Badge className="bg-red-600 text-white">SOS</Badge>}
          {inc.reporter_confirmed_safe && <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-300">Reporter safe</Badge>}
          {inc.responder_marked_complete && <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-300">Responder complete</Badge>}
        </div>
        <h1 className="font-display text-3xl font-extrabold tracking-tight">{inc.ai_analysis?.category || "Analyzing incident..."}</h1>
        <p className="text-slate-600">{inc.description}</p>

        {activeForResolution && (
          <div className="rounded-2xl border-2 border-emerald-200 bg-emerald-50 p-5 flex flex-wrap items-center justify-between gap-3" data-testid="resolution-panel">
            <div>
              <p className="text-xs uppercase tracking-widest font-bold text-emerald-700">Resolution</p>
              <p className="font-semibold text-slate-900 mt-1">
                {inc.status === "resolution_pending"
                  ? (inc.reporter_confirmed_safe ? "Waiting for responder to mark complete." : inc.responder_marked_complete ? "Please confirm you are safe." : "Awaiting both confirmations.")
                  : "Both sides can confirm resolution when ready."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {isReporter && !inc.reporter_confirmed_safe && (
                <Button data-testid="reporter-safe-btn" onClick={confirmSafe} className="bg-emerald-500 hover:bg-emerald-600 text-white"><ShieldCheck className="w-4 h-4 mr-1"/>I&apos;m Safe</Button>
              )}
              {isResponder && !inc.responder_marked_complete && (
                <Button data-testid="responder-complete-btn" onClick={responderComplete} className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold"><CheckCircle2 className="w-4 h-4 mr-1"/>Response Complete</Button>
              )}
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center gap-2 mb-3 text-cyan-700"><Sparkles className="w-4 h-4"/><span className="uppercase text-xs font-bold tracking-widest">AI Classification</span></div>
            {inc.ai_analysis ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><div className="text-slate-500 text-xs">Category</div><div className="font-semibold">{inc.ai_analysis.category}</div></div>
                  <div><div className="text-slate-500 text-xs">Department</div><div className="font-semibold capitalize">{inc.ai_analysis.department.replace(/_/g," ")}</div></div>
                  <div><div className="text-slate-500 text-xs">Priority</div><div className="font-semibold capitalize">{inc.ai_analysis.priority}</div></div>
                  <div><div className="text-slate-500 text-xs">Confidence</div><div className="font-semibold font-mono">{Math.round((inc.ai_analysis.confidence||0)*100)}%</div></div>
                </div>
                <p className="text-xs text-slate-500 italic">{inc.ai_analysis.reason}</p>
                <div>
                  <div className="text-xs uppercase font-bold text-slate-500 tracking-widest mb-1.5">Safety Guidance</div>
                  <ul className="space-y-1.5 text-sm">{inc.ai_analysis.safety_instructions?.map((s, i) => <li key={i} className="pl-4 relative before:absolute before:left-0 before:top-2 before:w-1.5 before:h-1.5 before:bg-cyan-500 before:rounded-full">{s}</li>)}</ul>
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-500 relative scan-line py-6"><Loader2 className="w-4 h-4 inline animate-spin mr-2"/>Analyzing…</div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
            <div>
              <div className="flex items-center gap-2 mb-3 text-amber-700"><ShieldAlert className="w-4 h-4"/><span className="uppercase text-xs font-bold tracking-widest">Fraud Risk</span></div>
              {inc.fraud_analysis ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${inc.fraud_analysis.risk_level==='low'?'bg-emerald-100 text-emerald-800':inc.fraud_analysis.risk_level==='medium'?'bg-amber-100 text-amber-800':'bg-red-100 text-red-800'}`}>{inc.fraud_analysis.risk_level}</div>
                    <span className="font-mono text-sm text-slate-600">score {inc.fraud_analysis.risk_score}</span>
                  </div>
                  <ul className="text-xs text-slate-600 list-disc list-inside">{inc.fraud_analysis.reasons?.map((r, i) => <li key={i}>{r}</li>)}</ul>
                </div>
              ) : <div className="text-sm text-slate-500">Awaiting analysis…</div>}
            </div>
            {inc.media_forensics && (
              <div className="pt-4 border-t border-slate-100" data-testid="media-forensics-card">
                <div className="flex items-center gap-2 mb-2 text-purple-700"><Sparkles className="w-4 h-4"/><span className="uppercase text-xs font-bold tracking-widest">Media Forensics</span></div>
                <div className="flex items-center gap-3">
                  <div className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${inc.media_forensics.verdict==='authentic'?'bg-emerald-100 text-emerald-800':inc.media_forensics.verdict==='suspicious'?'bg-amber-100 text-amber-800':inc.media_forensics.verdict==='likely_manipulated'?'bg-red-100 text-red-800':'bg-slate-100 text-slate-700'}`}>{inc.media_forensics.verdict.replace(/_/g," ")}</div>
                  <span className="font-mono text-sm text-slate-600">{Math.round((inc.media_forensics.confidence||0)*100)}%</span>
                </div>
                <ul className="text-xs text-slate-600 list-disc list-inside mt-2">{inc.media_forensics.reasons?.map((r, i) => <li key={i}>{r}</li>)}</ul>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h3 className="font-display font-bold">Live Location</h3>
            {inc.eta_minutes != null && (
              <div className="font-mono text-cyan-700 text-sm">
                ETA {inc.eta_minutes} min · {inc.distance_km != null ? `${inc.distance_km} km · ` : ""}Responder: {inc.assigned_responder_name || "—"}
              </div>
            )}
          </div>
          <LiveMap incident={inc} height={340} />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2 mb-3"><Clock className="w-4 h-4 text-cyan-600"/><h3 className="font-display font-bold">Timeline</h3></div>
          <ol className="space-y-3">
            {(inc.timeline || []).map((t, i) => (
              <motion.li key={i} initial={{opacity:0, x:-8}} animate={{opacity:1, x:0}} transition={{delay: i*0.03}} className="flex gap-3 text-sm">
                <span className="font-mono text-xs text-slate-500 w-20 shrink-0">{new Date(t.at).toLocaleTimeString()}</span>
                <span className="w-2 h-2 rounded-full bg-cyan-500 mt-1.5 shrink-0"/>
                <span className="text-slate-700">{t.text}</span>
              </motion.li>
            ))}
          </ol>
        </div>
      </div>
    </Layout>
  );
}
