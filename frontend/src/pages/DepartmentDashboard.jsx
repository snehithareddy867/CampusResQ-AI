import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import EmergencyCard from "@/components/EmergencyCard";
import client from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { ShieldCheck } from "lucide-react";

export default function DepartmentDashboard() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const load = () => client.get("/emergencies").then(r => setItems(r.data));
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);
  const active = items.filter(i => !["resolved","cancelled"].includes(i.status));
  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] font-bold text-cyan-400">{user?.department?.replace(/_/g," ")} Department</p>
          <h1 className="font-display text-3xl font-extrabold mt-1 flex items-center gap-2"><ShieldCheck className="w-6 h-6 text-cyan-400"/>Operations</h1>
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          {active.map(i => <EmergencyCard key={i.id} incident={i} />)}
          {active.length === 0 && <div className="p-10 col-span-full rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400">No active incidents in your department.</div>}
        </div>
      </div>
    </Layout>
  );
}
