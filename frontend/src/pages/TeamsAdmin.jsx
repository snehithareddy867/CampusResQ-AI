import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Users, Shield, Clock, Trash2, Save, Plus } from "lucide-react";
import { toast } from "sonner";

const DEPARTMENTS = ["medical","fire_safety","security","electrical","construction","facilities","environmental","transport"];
const COMMON_SKILLS = ["CPR", "First Aid", "Ambulance", "Emergency Driving", "Crowd Control", "Fire Fighting", "Electrical Safety", "Rescue"];

export default function TeamsAdmin() {
  const { user } = useAuth();
  const scopedDept = user?.role === "dept_admin" ? user.department : null;
  const [teams, setTeams] = useState([]);
  const [responders, setResponders] = useState([]);
  const [dept, setDept] = useState(scopedDept || "medical");
  const [creating, setCreating] = useState(null); // {kind}

  const load = async () => {
    const [t, r] = await Promise.all([
      client.get(scopedDept ? `/teams?department=${scopedDept}` : "/teams"),
      client.get("/admin/responders"),
    ]);
    setTeams(t.data); setResponders(r.data);
  };
  useEffect(() => { load(); }, []);

  const deptResponders = responders.filter(r => r.department === dept);
  const primaryTeam = teams.find(t => t.department === dept && t.kind === "primary");
  const backupTeam = teams.find(t => t.department === dept && t.kind === "backup");

  const createTeam = async (kind) => {
    const name = prompt(`Name for ${kind} team of ${dept.replace(/_/g," ")}?`, `${dept.replace(/_/g," ")} ${kind} team`);
    if (!name) return;
    try {
      await client.post("/teams", { department: dept, kind, name, member_ids: [], acceptance_timeout_sec: 60 });
      toast.success("Team created"); load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  const saveTeam = async (team, changes) => {
    await client.put(`/teams/${team.id}`, changes);
    toast.success("Saved"); load();
  };

  const deleteTeam = async (team) => {
    if (!confirm(`Delete ${team.kind} team?`)) return;
    await client.delete(`/teams/${team.id}`);
    toast.success("Deleted"); load();
  };

  const updateSkills = async (userId, skills) => {
    await client.put(`/responders/${userId}/skills`, { user_id: userId, skills });
    toast.success("Skills updated"); load();
  };

  return (
    <Layout dark>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Configuration</p>
            <h1 className="font-display text-3xl font-extrabold mt-1 flex items-center gap-2"><Users className="w-6 h-6 text-cyan-400"/>Teams & Skills</h1>
          </div>
          {!scopedDept && (
            <Select value={dept} onValueChange={setDept}>
              <SelectTrigger data-testid="teams-dept-select" className="w-56 bg-slate-900 border-slate-800"><SelectValue /></SelectTrigger>
              <SelectContent>{DEPARTMENTS.map(d => <SelectItem key={d} value={d}>{d.replace(/_/g," ")}</SelectItem>)}</SelectContent>
            </Select>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-5">
          <TeamPanel data-testid="primary-team" title="Primary Team" kind="primary" team={primaryTeam} responders={deptResponders} onCreate={() => createTeam("primary")} onSave={saveTeam} onDelete={deleteTeam} accent="cyan" />
          <TeamPanel data-testid="backup-team" title="Backup Team" kind="backup" team={backupTeam} responders={deptResponders} onCreate={() => createTeam("backup")} onSave={saveTeam} onDelete={deleteTeam} accent="amber" />
        </div>

        <section>
          <h2 className="font-display font-bold text-lg mb-3">Responder skills</h2>
          <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-950 text-xs uppercase tracking-widest text-slate-400"><tr>
                <th className="text-left p-3">Name</th><th className="text-left p-3">Skills</th></tr></thead>
              <tbody className="divide-y divide-slate-800">
                {deptResponders.map(r => (
                  <SkillsRow key={r.id} responder={r} onSave={updateSkills} />
                ))}
                {deptResponders.length === 0 && <tr><td colSpan={2} className="p-6 text-center text-slate-500">No responders in this department.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </Layout>
  );
}

function TeamPanel({ title, kind, team, responders, onCreate, onSave, onDelete, accent }) {
  const [selected, setSelected] = useState([]);
  const [timeout_, setTimeout_] = useState(60);
  useEffect(() => {
    setSelected((team?.members || []).map(m => m.user_id));
    setTimeout_(team?.acceptance_timeout_sec || 60);
  }, [team]);
  const border = accent === "cyan" ? "border-cyan-500/30" : "border-amber-500/30";
  const badge = accent === "cyan" ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/30" : "bg-amber-500/10 text-amber-300 border-amber-500/30";

  if (!team) {
    return (
      <div className={`rounded-2xl border ${border} bg-slate-900 p-5`}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display font-bold text-lg flex items-center gap-2"><Shield className="w-5 h-5"/>{title}</h3>
          <span className={`text-xs uppercase font-bold px-2 py-1 rounded-full border ${badge}`}>{kind}</span>
        </div>
        <p className="text-sm text-slate-400 mb-4">No {kind} team configured yet.</p>
        <Button onClick={onCreate} data-testid={`create-${kind}-team`}><Plus className="w-4 h-4 mr-1"/>Create {kind} team</Button>
      </div>
    );
  }
  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  return (
    <div className={`rounded-2xl border ${border} bg-slate-900 p-5`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-display font-bold text-lg flex items-center gap-2"><Shield className="w-5 h-5"/>{title}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{team.name}</p>
        </div>
        <span className={`text-xs uppercase font-bold px-2 py-1 rounded-full border ${badge}`}>{kind}</span>
      </div>
      <div className="space-y-3">
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-slate-400">Members</Label>
          <div className="mt-2 max-h-52 overflow-y-auto space-y-1.5">
            {responders.map(r => (
              <label key={r.id} data-testid={`member-toggle-${kind}-${r.id}`} className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800 cursor-pointer">
                <Checkbox checked={selected.includes(r.id)} onCheckedChange={() => toggle(r.id)} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold">{r.name}</div>
                  <div className="text-[11px] text-slate-500 truncate">{(r.skills || []).join(", ") || "no skills yet"}</div>
                </div>
                <span className={`w-2 h-2 rounded-full ${r.available ? "bg-emerald-400" : "bg-slate-500"}`}/>
              </label>
            ))}
            {responders.length === 0 && <div className="text-xs text-slate-500 p-2">No responders in this department.</div>}
          </div>
        </div>
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3"/>Acceptance timeout (seconds)</Label>
          <Input type="number" min={15} max={300} value={timeout_} onChange={(e) => setTimeout_(parseInt(e.target.value || "60", 10))} className="mt-1 bg-slate-950 border-slate-800" data-testid={`timeout-${kind}`}/>
        </div>
        <div className="flex gap-2 pt-2">
          <Button onClick={() => onSave(team, { member_ids: selected, acceptance_timeout_sec: timeout_ })} data-testid={`save-${kind}`}><Save className="w-4 h-4 mr-1"/>Save</Button>
          <Button variant="outline" onClick={() => onDelete(team)} data-testid={`delete-${kind}`} className="border-red-500/40 text-red-300 hover:bg-red-500/10"><Trash2 className="w-4 h-4 mr-1"/>Delete</Button>
        </div>
      </div>
    </div>
  );
}

function SkillsRow({ responder, onSave }) {
  const [skills, setSkills] = useState(responder.skills || []);
  const toggle = (s) => setSkills(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
  return (
    <tr>
      <td className="p-3 font-semibold w-48">{responder.name}</td>
      <td className="p-3">
        <div className="flex flex-wrap gap-1.5">
          {COMMON_SKILLS.map(s => (
            <button key={s} data-testid={`skill-${responder.id}-${s}`} onClick={() => toggle(s)}
              className={`text-[11px] uppercase font-bold px-2 py-1 rounded-full border ${skills.includes(s) ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-200" : "bg-slate-950 border-slate-800 text-slate-500"}`}>{s}</button>
          ))}
          <Button size="sm" variant="ghost" onClick={() => onSave(responder.id, skills)} data-testid={`save-skills-${responder.id}`} className="ml-2 h-7 px-2 text-xs">Save</Button>
        </div>
      </td>
    </tr>
  );
}
