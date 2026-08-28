import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import LiveMap from "@/components/LiveMap";
import EmergencyCard from "@/components/EmergencyCard";
import { Activity, AlertOctagon, Clock, ShieldCheck, TrendingUp, Users, HeartPulse } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, PieChart, Pie, Cell } from "recharts";

function Metric({ icon: Icon, label, value, tone = "cyan" }) {
  const tones = {
    cyan: "text-cyan-400 border-cyan-500/30 bg-cyan-500/5",
    red: "text-red-400 border-red-500/30 bg-red-500/5",
    amber: "text-amber-400 border-amber-500/30 bg-amber-500/5",
    emerald: "text-emerald-400 border-emerald-500/30 bg-emerald-500/5",
  };
  return (
    <div className={`p-4 rounded-xl border ${tones[tone]}`}>
      <div className="flex items-center gap-2 text-xs uppercase tracking-widest font-bold"><Icon className="w-3.5 h-3.5"/>{label}</div>
      <div className="mt-1.5 font-mono text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

export default function AdminCommandCenter() {
  const [m, setM] = useState(null);
  const [incs, setIncs] = useState([]);
  const [wellness, setWellness] = useState(null);

  const load = async () => {
    const [mr, ir, wr] = await Promise.all([
      client.get("/admin/metrics"),
      client.get("/admin/incidents"),
      client.get("/admin/wellness-stats?days=7").catch(() => ({ data: null })),
    ]);
    setM(mr.data); setIncs(ir.data); setWellness(wr.data);
  };
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);

  const active = incs.filter(i => !["resolved","cancelled"].includes(i.status));
  const chartData = m ? Object.entries(m.by_department).map(([k, v]) => ({ dept: k.replace(/_/g," "), count: v })) : [];
  const mapMarkers = active.slice(0, 20).map(i => ({ lat: i.location.lat, lng: i.location.lng, label: `${i.ai_analysis?.category || 'Incident'} · ${i.status}`, critical: i.priority === "critical" }));

  return (
    <Layout dark>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Command Center</p>
            <h1 className="font-display text-3xl sm:text-4xl font-extrabold mt-1 tracking-tight">Campus Live Ops</h1>
          </div>
          <div className="text-xs text-slate-400 font-mono">{new Date().toLocaleString()}</div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <Metric icon={Activity} label="Active" value={m?.active ?? "—"} tone="cyan"/>
          <Metric icon={AlertOctagon} label="Critical" value={m?.critical ?? "—"} tone="red"/>
          <Metric icon={Clock} label="Pending" value={m?.pending ?? "—"} tone="amber"/>
          <Metric icon={ShieldCheck} label="Resolved (today)" value={m?.resolved_today ?? "—"} tone="emerald"/>
          <Metric icon={AlertOctagon} label="Fraud flags" value={m?.fraud_flags ?? "—"} tone="amber"/>
          <Metric icon={Users} label="Responders on" value={`${m?.online_responders ?? 0}/${(m?.online_responders ?? 0)+(m?.offline_responders ?? 0)}`} tone="cyan"/>
        </div>

        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-bold text-lg">Live Map</h3>
              <div className="text-xs text-slate-400">{active.length} active incidents</div>
            </div>
            <LiveMap markers={mapMarkers} height={380} />
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="flex items-center gap-2 mb-3"><TrendingUp className="w-4 h-4 text-cyan-400"/><h3 className="font-display font-bold">By Department</h3></div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="dept" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={0} angle={-30} height={60} textAnchor="end"/>
                <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }}/>
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}/>
                <Bar dataKey="count" fill="#00E5FF" radius={[4, 4, 0, 0]}/>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-2 text-xs mt-3 pt-3 border-t border-slate-800">
              <div><div className="text-slate-400">Avg accept</div><div className="font-mono text-cyan-300 text-base font-bold">{m?.avg_accept_min ?? 0} min</div></div>
              <div><div className="text-slate-400">Avg resolve</div><div className="font-mono text-cyan-300 text-base font-bold">{m?.avg_resolve_min ?? 0} min</div></div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="font-display font-bold text-lg mb-3">Active incidents</h3>
          <div className="grid md:grid-cols-2 gap-3">
            {active.length === 0 && <div className="p-8 col-span-full text-center text-slate-400 bg-slate-900 border border-slate-800 rounded-xl">All quiet.</div>}
            {active.map(i => <EmergencyCard key={i.id} incident={i}/>)}
          </div>
        </div>

        {wellness && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5" data-testid="wellness-trend-card">
            <div className="flex items-center gap-2 mb-3">
              <HeartPulse className="w-5 h-5 text-emerald-400"/>
              <h3 className="font-display font-bold text-lg">Wellness follow-ups · last {wellness.days} days</h3>
              <span className="ml-auto text-xs text-slate-400 font-mono">{wellness.total} replies</span>
            </div>
            {wellness.total === 0 ? (
              <div className="text-sm text-slate-400 py-6 text-center">No wellness replies in this window.</div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie data={[
                      { name: "Okay", value: wellness.counts.ok, color: "#10b981" },
                      { name: "Recovering", value: wellness.counts.recovering, color: "#f59e0b" },
                      { name: "Needs help", value: wellness.counts.needs_help, color: "#ef4444" },
                    ]} dataKey="value" nameKey="name" outerRadius={70} label>
                      {[{c:"#10b981"},{c:"#f59e0b"},{c:"#ef4444"}].map((e,i) => <Cell key={i} fill={e.c}/>)}
                    </Pie>
                    <Tooltip contentStyle={{ background:"#0f172a", border:"1px solid #1e293b", borderRadius:8 }}/>
                  </PieChart>
                </ResponsiveContainer>
                <div className="max-h-44 overflow-y-auto space-y-1.5 text-sm">
                  {wellness.recent.map((r, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800">
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${r.mood==='ok'?'bg-emerald-500/20 text-emerald-300':r.mood==='recovering'?'bg-amber-500/20 text-amber-300':'bg-red-500/20 text-red-300'}`}>{r.mood}</span>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-slate-300">{r.reporter} · {r.category}</div>
                        <div className="truncate text-xs text-slate-500">{r.note || "—"}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
