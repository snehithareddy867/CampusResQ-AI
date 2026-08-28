import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Megaphone, Mail, Send } from "lucide-react";

export default function Announcements() {
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [priority, setPriority] = useState("high");
  const [busy, setBusy] = useState(false);

  const load = () => client.get("/announcements").then(r => setItems(r.data));
  useEffect(() => { load(); }, []);

  const send = async () => {
    if (!title.trim() || !body.trim()) return toast.error("Title and body required");
    setBusy(true);
    try {
      await client.post("/announcements", { title: title.trim(), body: body.trim(), priority });
      toast.success("Announcement broadcast to all users");
      setTitle(""); setBody(""); load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setBusy(false); }
  };

  const triggerDigest = async () => {
    try { await client.post("/admin/weekly-digest/test"); toast.success("Weekly digest queued to head admins"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  return (
    <Layout dark>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Broadcast</p>
          <h1 className="font-display text-3xl font-extrabold mt-1 flex items-center gap-2"><Megaphone className="w-6 h-6 text-cyan-400"/>Campus-Wide Alerts</h1>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
          <div className="space-y-2"><Label>Title</Label><Input data-testid="ann-title" value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="Severe weather warning" className="bg-slate-950 border-slate-800"/></div>
          <div className="space-y-2"><Label>Body</Label><Textarea data-testid="ann-body" value={body} onChange={(e)=>setBody(e.target.value)} rows={4} placeholder="Please shelter indoors until 5 PM. Stay away from Block C." className="bg-slate-950 border-slate-800"/></div>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="space-y-1">
              <Label className="text-xs uppercase tracking-widest font-bold text-slate-400">Priority</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger data-testid="ann-priority" className="w-40 bg-slate-950 border-slate-800"><SelectValue/></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button data-testid="ann-send" onClick={send} disabled={busy} className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold mt-4"><Send className="w-4 h-4 mr-1"/>Broadcast to campus</Button>
            <Button data-testid="digest-test" onClick={triggerDigest} variant="outline" className="border-slate-700 hover:bg-slate-800 mt-4"><Mail className="w-4 h-4 mr-1"/>Send weekly digest now</Button>
          </div>
          <p className="text-xs text-slate-500">Every registered device receives an in-app + push notification. Weekly digest emails go to head-admin registered emails every Monday 09:00 IST.</p>
        </div>
        <div>
          <h2 className="font-display font-bold text-lg mb-3">Recent announcements</h2>
          <div className="space-y-2">
            {items.map(a => (
              <div key={a.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[11px] uppercase font-bold px-2 py-0.5 rounded-full ${a.priority==='critical'?'bg-red-500/20 text-red-300':a.priority==='high'?'bg-amber-500/20 text-amber-300':'bg-slate-700 text-slate-300'}`}>{a.priority}</span>
                  <span className="font-mono text-xs text-slate-500">{new Date(a.created_at).toLocaleString()}</span>
                </div>
                <div className="font-display font-bold mt-1">{a.title}</div>
                <p className="text-sm text-slate-300 mt-1">{a.body}</p>
                <p className="text-xs text-slate-500 mt-2">By {a.author_name}</p>
              </div>
            ))}
            {items.length === 0 && <div className="p-8 text-center text-slate-500">No announcements yet.</div>}
          </div>
        </div>
      </div>
    </Layout>
  );
}
