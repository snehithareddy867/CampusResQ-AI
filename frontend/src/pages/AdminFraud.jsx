import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { FileWarning, CheckCircle2, XCircle } from "lucide-react";

export default function AdminFraud() {
  const [items, setItems] = useState([]);
  const load = () => client.get("/admin/fraud").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);

  const decide = async (id, decision) => {
    await client.post(`/emergencies/${id}/admin-override`, { fraud_decision: decision });
    toast.success(`Fraud decision: ${decision}`);
    load();
  };

  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><FileWarning className="w-6 h-6 text-amber-400"/>Fraud Review Queue</h1>
        {items.length === 0 && <div className="p-10 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400">No suspicious reports require review.</div>}
        <div className="space-y-3">
          {items.map(i => (
            <div key={i.id} className="rounded-xl bg-slate-900 border border-amber-500/30 p-5">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="min-w-0 flex-1">
                  <div className="font-display font-bold text-lg">{i.ai_analysis?.category || "Unclassified"}</div>
                  <p className="text-sm text-slate-300 mt-1">{i.description}</p>
                  <div className="mt-3 text-xs font-mono text-amber-300">
                    Risk: {i.fraud_analysis?.risk_level?.toUpperCase()} · Score {i.fraud_analysis?.risk_score}
                  </div>
                  <ul className="text-xs text-slate-400 list-disc list-inside mt-1">{i.fraud_analysis?.reasons?.map((r, idx) => <li key={idx}>{r}</li>)}</ul>
                  <div className="mt-2 text-xs text-slate-500">Reporter: {i.reporter_name}</div>
                </div>
                <div className="flex gap-2">
                  <Button data-testid={`fraud-approve-${i.id}`} onClick={()=>decide(i.id, "approve")} className="bg-emerald-500 hover:bg-emerald-600 text-white"><CheckCircle2 className="w-4 h-4 mr-1"/>Approve</Button>
                  <Button data-testid={`fraud-dismiss-${i.id}`} onClick={()=>decide(i.id, "dismiss")} variant="outline" className="border-slate-700 hover:bg-slate-800"><XCircle className="w-4 h-4 mr-1"/>Dismiss</Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
