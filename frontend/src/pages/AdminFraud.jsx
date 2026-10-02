import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { FileWarning } from "lucide-react";

export default function AdminFraud() {
  const [items, setItems] = useState([]);
  const load = () => client.get("/admin/fraud").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);

  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><FileWarning className="w-6 h-6 text-amber-400"/>Fraud flags (observer)</h1>
        <p className="text-sm text-slate-400">Routing is automatic. This queue is for visibility only — incidents are not held for admin approval.</p>
        {items.length === 0 && <div className="p-10 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400">No high-risk flags.</div>}
        <div className="space-y-3">
          {items.map(i => (
            <div key={i.id} className="rounded-xl bg-slate-900 border border-amber-500/30 p-5">
              <div className="min-w-0">
                <div className="font-display font-bold text-lg">{i.ai_analysis?.category || "Unclassified"}</div>
                <p className="text-sm text-slate-300 mt-1">{i.description}</p>
                <div className="mt-3 text-xs font-mono text-amber-300">
                  Risk: {i.fraud_analysis?.risk_level?.toUpperCase()} · Score {i.fraud_analysis?.risk_score} · Team: {i.assigned_team_name || i.assigned_department} · Routing: {i.routing_status || "—"}
                </div>
                <ul className="text-xs text-slate-400 list-disc list-inside mt-1">{i.fraud_analysis?.reasons?.map((r, idx) => <li key={idx}>{r}</li>)}</ul>
                <div className="mt-2 text-xs text-slate-500">Reporter: {i.reporter_name}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
