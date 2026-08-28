import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Loader2 } from "lucide-react";
import { toast } from "sonner";
import client from "@/lib/api";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const u = await login(email, password);
      toast.success(`Welcome, ${u.name}`);
      nav("/go");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  };

  const seed = async () => {
    try { await client.post("/dev/seed"); toast.success("Demo accounts ready. Password: Campus@2026"); }
    catch { toast.error("Seed failed"); }
  };

  const quickFill = (em) => { setEmail(em); setPassword("Campus@2026"); };

  return (
    <div className="min-h-screen grid md:grid-cols-2 bg-slate-50">
      <div className="hidden md:flex flex-col justify-between p-12 bg-slate-950 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-40" style={{backgroundImage:"radial-gradient(circle at 20% 30%, #00E5FF 0%, transparent 40%)"}}/>
        <div className="relative flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500 flex items-center justify-center"><Shield className="w-5 h-5 text-slate-950" strokeWidth={2.5}/></div>
          <span className="font-display font-extrabold text-lg">CampusResQ<span className="text-cyan-400">.AI</span></span>
        </div>
        <div className="relative">
          <h2 className="font-display text-3xl font-extrabold leading-tight">Sign in to your role.<br/><span className="text-cyan-400">One portal per person.</span></h2>
          <p className="text-slate-400 mt-4 max-w-md text-sm leading-relaxed">Students, responders, department leads and head admins each get an experience built for their job — with strict access boundaries.</p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6 sm:p-10">
        <form onSubmit={submit} className="w-full max-w-sm space-y-5">
          <div>
            <h1 className="font-display text-3xl font-extrabold">Welcome back</h1>
            <p className="text-sm text-slate-500 mt-1">Sign in with your campus credentials.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input data-testid="login-email" id="email" type="email" required value={email} onChange={(e)=>setEmail(e.target.value)} placeholder="you@campus.edu" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input data-testid="login-password" id="password" type="password" required value={password} onChange={(e)=>setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <Button data-testid="login-submit" type="submit" disabled={loading} className="w-full h-11 bg-slate-950 hover:bg-slate-800">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign in"}
          </Button>
          <p className="text-sm text-center text-slate-500">
            New here? <Link to="/register" className="text-cyan-600 font-semibold hover:underline">Create account</Link>
          </p>
          <div className="border-t border-slate-200 pt-4">
            <p className="text-xs uppercase tracking-widest font-bold text-slate-400 mb-2">Demo Accounts</p>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <button type="button" onClick={()=>quickFill("student@campus.edu")} className="text-left px-2 py-1.5 rounded bg-slate-100 hover:bg-cyan-50">Student</button>
              <button type="button" onClick={()=>quickFill("medic@campus.edu")} className="text-left px-2 py-1.5 rounded bg-slate-100 hover:bg-cyan-50">Responder</button>
              <button type="button" onClick={()=>quickFill("deptmed@campus.edu")} className="text-left px-2 py-1.5 rounded bg-slate-100 hover:bg-cyan-50">Dept Admin</button>
              <button type="button" onClick={()=>quickFill("admin@campus.edu")} className="text-left px-2 py-1.5 rounded bg-slate-100 hover:bg-cyan-50">Head Admin</button>
            </div>
            <button type="button" onClick={seed} data-testid="seed-btn" className="mt-2 text-xs text-cyan-600 hover:underline">Seed demo data</button>
          </div>
        </form>
      </div>
    </div>
  );
}
