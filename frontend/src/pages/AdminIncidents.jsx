import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import EmergencyCard from "@/components/EmergencyCard";
import client from "@/lib/api";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";
import { Link } from "react-router-dom";
import { Play } from "lucide-react";

export default function AdminIncidents() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  useEffect(() => { client.get("/admin/incidents").then(r => setItems(r.data)); }, []);
  const filtered = items.filter(i => !q || i.description.toLowerCase().includes(q.toLowerCase()) || i.status?.includes(q.toLowerCase()));
  const canReplay = ["head_admin", "dept_admin"].includes(user?.role);
  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl font-extrabold">All Incidents</h1>
          <Input placeholder="Filter…" value={q} onChange={(e)=>setQ(e.target.value)} className="max-w-xs bg-slate-900 border-slate-800" data-testid="incidents-filter"/>
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          {filtered.map(i => (
            <div key={i.id} className="relative">
              <EmergencyCard incident={i}/>
              {canReplay && ["resolved", "cancelled"].includes(i.status) && (
                <Link to={`/admin/replay/${i.id}`} data-testid={`replay-${i.id}`} className="absolute top-3 right-3 inline-flex items-center gap-1 text-[11px] uppercase font-bold px-2 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25">
                  <Play className="w-3 h-3"/>Replay
                </Link>
              )}
            </div>
          ))}
          {filtered.length === 0 && <div className="col-span-full p-10 text-center text-slate-400">No incidents.</div>}
        </div>
      </div>
    </Layout>
  );
}
