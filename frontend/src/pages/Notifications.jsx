import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { Bell, Check, HeartHandshake } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { toast } from "sonner";

export default function Notifications() {
  const [items, setItems] = useState([]);
  const load = () => client.get("/notifications").then(r => setItems(r.data));
  useEffect(() => { load(); const t = setInterval(load, 4000); return () => clearInterval(t); }, []);

  const readAll = async () => { await client.post("/notifications/read-all"); load(); };
  const readOne = async (id) => { await client.post(`/notifications/${id}/read`); load(); };

  const wellnessReply = async (incident_id, mood) => {
    try {
      await client.post(`/emergencies/${incident_id}/wellness-reply`, { mood, note: `Reporter selected: ${mood}` });
      toast.success(mood === "needs_help" ? "Medical team alerted" : "Thanks — logged for follow-up");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><Bell className="w-6 h-6 text-cyan-500"/>Notifications</h1>
          <Button data-testid="mark-all-read" size="sm" variant="outline" onClick={readAll}>Mark all read</Button>
        </div>
        {items.length === 0 && <div className="p-10 rounded-xl bg-white border border-slate-200 text-center text-slate-500">You&apos;re up to date.</div>}
        <div className="space-y-2">
          {items.map(n => (
            <div key={n.id} data-testid={`notif-${n.id}`} className={`p-4 rounded-xl border ${n.read_at ? "bg-white border-slate-200" : "bg-cyan-50 border-cyan-200"}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-xs uppercase font-bold tracking-widest text-slate-500">{n.type.replace(/_/g," ")}</div>
                  <div className="font-medium mt-0.5">{n.message}</div>
                  <div className="text-xs text-slate-500 mt-1 font-mono">{new Date(n.created_at).toLocaleString()}</div>
                  {n.incident_id && n.type !== "WELLNESS_CHECKIN" && <Link to={`/emergency/${n.incident_id}`} className="text-xs text-cyan-600 font-semibold hover:underline mt-1 inline-block">View incident →</Link>}
                  {n.type === "WELLNESS_CHECKIN" && n.incident_id && (
                    <div className="mt-3 p-3 rounded-lg bg-white border border-emerald-200 flex flex-wrap items-center gap-2" data-testid={`wellness-${n.incident_id}`}>
                      <HeartHandshake className="w-4 h-4 text-emerald-600"/>
                      <span className="text-xs text-slate-700 font-semibold">How are you now?</span>
                      <Button size="sm" onClick={()=>wellnessReply(n.incident_id, "ok")} className="bg-emerald-500 hover:bg-emerald-600 text-white h-7 text-xs" data-testid={`wellness-ok-${n.incident_id}`}>I&apos;m okay</Button>
                      <Button size="sm" onClick={()=>wellnessReply(n.incident_id, "recovering")} variant="outline" className="h-7 text-xs" data-testid={`wellness-rec-${n.incident_id}`}>Recovering</Button>
                      <Button size="sm" onClick={()=>wellnessReply(n.incident_id, "needs_help")} className="bg-red-500 hover:bg-red-600 text-white h-7 text-xs" data-testid={`wellness-help-${n.incident_id}`}>Need more help</Button>
                    </div>
                  )}
                </div>
                {!n.read_at && <button onClick={()=>readOne(n.id)} className="p-1.5 rounded hover:bg-white"><Check className="w-4 h-4 text-slate-500"/></button>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
