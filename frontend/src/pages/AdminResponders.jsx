import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { Users } from "lucide-react";

export default function AdminResponders() {
  const [items, setItems] = useState([]);
  useEffect(() => { client.get("/admin/responders").then(r => setItems(r.data)); }, []);
  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><Users className="w-6 h-6 text-cyan-400"/>Responders</h1>
        <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-widest text-slate-400">
              <tr><th className="text-left p-3">Name</th><th className="text-left p-3">Department</th><th className="text-left p-3">Status</th><th className="text-left p-3">Email</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {items.map(r => (
                <tr key={r.id} data-testid={`resp-row-${r.id}`}>
                  <td className="p-3 font-semibold">{r.name}</td>
                  <td className="p-3 capitalize">{r.department?.replace(/_/g," ")}</td>
                  <td className="p-3"><span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${r.available ? "text-emerald-400" : "text-slate-500"}`}><span className={`w-2 h-2 rounded-full ${r.available ? "bg-emerald-400" : "bg-slate-500"}`}/>{r.available ? "Available" : "Off-duty"}</span></td>
                  <td className="p-3 font-mono text-slate-400 text-xs">{r.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
