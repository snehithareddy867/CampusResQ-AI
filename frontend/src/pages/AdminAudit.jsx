import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { ScrollText } from "lucide-react";

export default function AdminAudit() {
  const [items, setItems] = useState([]);
  useEffect(() => { client.get("/admin/audit").then(r => setItems(r.data)); }, []);
  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><ScrollText className="w-6 h-6 text-cyan-400"/>Audit Log</h1>
        <div className="rounded-xl bg-slate-900 border border-slate-800 divide-y divide-slate-800">
          {items.map(a => (
            <div key={a.id} className="p-4 flex flex-wrap gap-3 items-start text-sm">
              <span className="font-mono text-xs text-slate-500 w-40 shrink-0">{new Date(a.created_at).toLocaleString()}</span>
              <span className="flex-1 min-w-0">
                <span className="font-semibold text-cyan-300">{a.actor_name}</span> <span className="text-slate-400">({a.actor_role})</span> — <span className="font-mono">{a.action}</span> on <span className="text-slate-300">{a.entity_type}</span>
                <span className="text-xs text-slate-500 font-mono ml-1">#{a.entity_id.slice(0,8)}</span>
              </span>
            </div>
          ))}
          {items.length === 0 && <div className="p-8 text-center text-slate-400">No audit records yet.</div>}
        </div>
      </div>
    </Layout>
  );
}
