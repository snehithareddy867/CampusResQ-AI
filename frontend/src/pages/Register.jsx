import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Shield } from "lucide-react";
import { toast } from "sonner";

const DEPARTMENTS = ["medical","fire_safety","security","electrical","construction","facilities","environmental","transport"];

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "", role: "student", department: "", registration_number: "" });
  const [loading, setLoading] = useState(false);

  const setF = (k, v) => setForm((s) => ({ ...s, [k]: v }));

  const strength = (() => {
    const p = form.password;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[a-z]/.test(p)) s++;
    if (/\d/.test(p)) s++;
    if (/[!@#$%^&*(),.?":{}|<>\/`~_+=\-\[\]]/.test(p)) s++;
    return s;
  })();

  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) return toast.error("Passwords don't match");
    if (strength < 5) return toast.error("Password must have upper, lower, number, special & 8+ chars");
    setLoading(true);
    try {
      const payload = { name: form.name, email: form.email, password: form.password, role: form.role, registration_number: form.registration_number || undefined };
      if (form.role !== "student" && form.department) payload.department = form.department;
      const u = await register(payload);
      toast.success(`Welcome, ${u.name}`);
      nav("/go");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally { setLoading(false); }
  };

  const strengthColors = ["bg-slate-200","bg-red-400","bg-orange-400","bg-yellow-400","bg-lime-400","bg-emerald-500"];

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <form onSubmit={submit} className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 space-y-5 shadow-xl shadow-slate-200/50">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-slate-950 flex items-center justify-center"><Shield className="w-4.5 h-4.5 text-cyan-400" /></div>
          <span className="font-display font-extrabold">CampusResQ<span className="text-cyan-500">.AI</span></span>
        </div>
        <div>
          <h1 className="font-display text-2xl font-extrabold">Create your account</h1>
          <p className="text-sm text-slate-500 mt-1">Choose the portal that matches your campus role.</p>
        </div>
        <div className="space-y-2"><Label>Full name</Label><Input data-testid="reg-name" required value={form.name} onChange={(e)=>setF("name", e.target.value)} /></div>
        <div className="space-y-2"><Label>Email</Label><Input data-testid="reg-email" type="email" required value={form.email} onChange={(e)=>setF("email", e.target.value)} /></div>
        <div className="space-y-2">
          <Label>{form.role === "student" ? "Registration number (e.g., 24-1-FK)" : "Staff ID (e.g., FAC-1234)"}</Label>
          <Input data-testid="reg-regnum" required={form.role === "student"} value={form.registration_number}
            onChange={(e)=>setF("registration_number", e.target.value.toUpperCase())}
            placeholder={form.role === "student" ? "24-1-FK" : "FAC-1234"} />
          <p className="text-[11px] text-slate-500">
            {form.role === "student" ? "Format YY-N-XX (year-batch-branch). Must be unique." : "Format PREFIX-NNNN (e.g., FAC-1234, ADM-0001). Must be unique."}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={form.role} onValueChange={(v)=>setF("role", v)}>
              <SelectTrigger data-testid="reg-role"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="student">Student</SelectItem>
                <SelectItem value="responder">Responder</SelectItem>
                <SelectItem value="dept_personnel">Dept Personnel</SelectItem>
                <SelectItem value="dept_admin">Dept Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {form.role !== "student" && (
            <div className="space-y-2">
              <Label>Department</Label>
              <Select value={form.department} onValueChange={(v)=>setF("department", v)}>
                <SelectTrigger data-testid="reg-dept"><SelectValue placeholder="Pick" /></SelectTrigger>
                <SelectContent>
                  {DEPARTMENTS.map(d => <SelectItem key={d} value={d}>{d.replace(/_/g," ")}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <div className="space-y-2">
          <Label>Password</Label>
          <Input data-testid="reg-password" type="password" required value={form.password} onChange={(e)=>setF("password", e.target.value)} />
          <div className="flex gap-1 mt-1.5">
            {[1,2,3,4,5].map(i => (<div key={i} className={`h-1.5 flex-1 rounded-full ${i <= strength ? strengthColors[strength] : "bg-slate-200"}`}/>))}
          </div>
          <p className="text-[11px] text-slate-500">8+ chars, upper, lower, number, special. Try: <code className="font-mono">Campus@2026</code></p>
        </div>
        <div className="space-y-2"><Label>Confirm password</Label><Input data-testid="reg-confirm" type="password" required value={form.confirm} onChange={(e)=>setF("confirm", e.target.value)} /></div>
        <Button data-testid="reg-submit" type="submit" disabled={loading} className="w-full h-11 bg-slate-950 hover:bg-slate-800">{loading ? "Creating…" : "Create account"}</Button>
        <p className="text-sm text-center text-slate-500">Have an account? <Link to="/login" className="text-cyan-600 font-semibold">Sign in</Link></p>
      </form>
    </div>
  );
}
