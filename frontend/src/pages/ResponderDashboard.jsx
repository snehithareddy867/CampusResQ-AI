import React, { useEffect, useRef, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { CheckCircle2, XCircle, MapPin, Navigation } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { subscribeWS } from "@/lib/ws";
import { playSiren } from "@/lib/siren";

export default function ResponderDashboard() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [available, setAvailable] = useState(user?.available !== false);
  const [streaming, setStreaming] = useState({});  // {incident_id: true}
  const watchers = useRef({});

  const load = () => client.get("/emergencies").then(r => setItems(r.data));
  useEffect(() => {
    load();
    const t = setInterval(load, 6000);
    const unsub = subscribeWS((evt) => {
      if (evt?.type === "SOS_NEARBY") {
        playSiren(4000);
        toast.error("🚨 SOS EMERGENCY nearby — check queue", { duration: 8000 });
      }
      if (evt?.event === "notification" || evt?.incident_id) load();
    });
    return () => { clearInterval(t); unsub(); };
  }, []);

  // auto-start GPS streaming for any active incident assigned to me
  useEffect(() => {
    const active = items.filter(i => ["accepted", "en_route", "arrived"].includes(i.status) && i.assigned_responder_id === user?.id);
    active.forEach(i => { if (!watchers.current[i.id]) startStreaming(i.id); });
    // stop for incidents no longer active
    Object.keys(watchers.current).forEach(id => {
      const still = active.find(a => a.id === id);
      if (!still) stopStreaming(id);
    });
    // eslint-disable-next-line
  }, [items]);

  useEffect(() => () => { Object.keys(watchers.current).forEach(stopStreaming); }, []);

  const startStreaming = (incident_id) => {
    if (!navigator.geolocation) return;
    const wid = navigator.geolocation.watchPosition(async (pos) => {
      const c = pos.coords;
      try {
        await client.post(`/emergencies/${incident_id}/location`, {
          incident_id,
          location: { lat: c.latitude, lng: c.longitude },
          heading: c.heading ?? undefined,
          speed_mps: c.speed ?? undefined,
          accuracy: c.accuracy ?? undefined,
        });
      } catch {}
    }, (err) => { console.warn("gps err", err); }, { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 });
    watchers.current[incident_id] = wid;
    setStreaming(s => ({ ...s, [incident_id]: true }));
  };
  const stopStreaming = (incident_id) => {
    const wid = watchers.current[incident_id];
    if (wid != null && navigator.geolocation) navigator.geolocation.clearWatch(wid);
    delete watchers.current[incident_id];
    setStreaming(s => { const n = { ...s }; delete n[incident_id]; return n; });
  };

  const toggle = async (v) => {
    setAvailable(v);
    await client.post("/responders/availability", { available: v });
    toast.success(v ? "You are now available" : "You are offline");
  };

  const accept = async (id) => {
    const doAccept = (extra) => client.post(`/emergencies/${id}/accept`, { incident_id: id, eta_minutes: 5, ...extra })
      .then(() => { toast.success("Accepted — live GPS streaming starting"); load(); nav(`/emergency/${id}`); })
      .catch(e => { toast.error(e?.response?.data?.detail || "Failed to accept"); load(); });
    if (!navigator.geolocation) return doAccept({});
    navigator.geolocation.getCurrentPosition(
      (pos) => doAccept({ current_location: { lat: pos.coords.latitude, lng: pos.coords.longitude } }),
      () => doAccept({}),
      { enableHighAccuracy: true, timeout: 6000 }
    );
  };
  const reject = async (id) => { await client.post(`/emergencies/${id}/reject`, { incident_id: id, reason: "Unavailable" }); toast.info("Rejected — trying another responder"); load(); };
  const setStatus = async (id, status) => { await client.post(`/emergencies/${id}/status`, { status }); load(); };
  const completeResponse = async (id) => {
    try { await client.post(`/emergencies/${id}/responder-complete`); toast.success("Marked response complete"); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  const newQueue = items.filter(i => ["waiting_for_acceptance", "escalated"].includes(i.status) && !i.assigned_responder_id);
  const active = items.filter(i => ["accepted", "en_route", "arrived"].includes(i.status) && i.assigned_responder_id === user?.id);

  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] font-bold text-cyan-400">Responder · {user?.department}</p>
            <h1 className="font-display text-3xl font-extrabold mt-1">On-call console</h1>
          </div>
          <div className="flex items-center gap-3 rounded-full bg-slate-900 border border-slate-800 px-4 py-2">
            <span className={`w-2 h-2 rounded-full ${available ? "bg-emerald-400" : "bg-slate-500"}`}/>
            <span className="text-sm font-semibold">{available ? "Available" : "Off-duty"}</span>
            <Switch data-testid="availability-switch" checked={available} onCheckedChange={toggle}/>
          </div>
        </div>

        <section>
          <h2 className="font-display font-bold text-lg mb-3 text-cyan-300 uppercase tracking-widest text-sm">Awaiting Acceptance</h2>
          {newQueue.length === 0 ? <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400">Queue clear.</div>
            : <div className="space-y-3">{newQueue.map(i => (
              <div key={i.id} className="rounded-xl bg-slate-900 border border-cyan-500/30 p-5">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[11px] uppercase font-bold px-2 py-0.5 rounded-full ${i.priority==='critical'?'bg-red-500/20 text-red-300':'bg-amber-500/20 text-amber-300'}`}>{i.priority}</span>
                      {i.status === "escalated" && <span className="text-[11px] uppercase font-bold px-2 py-0.5 rounded-full bg-red-600 text-white">BACKUP</span>}
                    </div>
                    <div className="font-display font-bold text-lg">{i.ai_analysis?.category || "Incident"}</div>
                    <p className="text-sm text-slate-300 mt-1">{i.description}</p>
                    <p className="text-xs font-mono text-slate-500 mt-2">{i.location?.address}</p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button data-testid={`accept-${i.id}`} onClick={()=>accept(i.id)} className="bg-emerald-500 hover:bg-emerald-600 text-white"><CheckCircle2 className="w-4 h-4 mr-1"/>Accept</Button>
                    <Button data-testid={`reject-${i.id}`} onClick={()=>reject(i.id)} variant="outline" className="border-slate-700 hover:bg-slate-800"><XCircle className="w-4 h-4 mr-1"/>Reject</Button>
                  </div>
                </div>
              </div>
            ))}</div>}
        </section>

        <section>
          <h2 className="font-display font-bold text-lg mb-3 text-cyan-300 uppercase tracking-widest text-sm">My Active Response</h2>
          {active.length === 0 ? <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400">No active incidents.</div>
            : <div className="space-y-3">{active.map(i => (
              <div key={i.id} className="rounded-xl bg-slate-900 border border-slate-800 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-display font-bold text-lg">{i.ai_analysis?.category}</div>
                    <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
                      <span>{i.status}</span>·<span>ETA {i.eta_minutes ?? "—"} min</span>·<span>{i.distance_km ?? "—"} km</span>
                      {streaming[i.id] && <span className="inline-flex items-center gap-1 text-emerald-400"><Navigation className="w-3 h-3 animate-pulse"/>Streaming GPS</span>}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={()=>setStatus(i.id, "arrived")} className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold" data-testid={`arrived-${i.id}`}>I've Arrived</Button>
                    <Button size="sm" onClick={()=>completeResponse(i.id)} className="bg-emerald-500 hover:bg-emerald-600 text-white" data-testid={`complete-${i.id}`}>Response Complete</Button>
                    <Button size="sm" variant="outline" onClick={()=>nav(`/emergency/${i.id}`)} className="border-slate-700 hover:bg-slate-800" data-testid={`view-${i.id}`}><MapPin className="w-4 h-4 mr-1"/>View Live</Button>
                  </div>
                </div>
              </div>
            ))}</div>}
        </section>
      </div>
    </Layout>
  );
}
