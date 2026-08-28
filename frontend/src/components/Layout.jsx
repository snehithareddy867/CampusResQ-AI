import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Shield, Home, Bell, MessageCircle, User, LogOut, AlertOctagon, LayoutDashboard, ShieldCheck, Users, Activity, FileWarning, ScrollText, UserPlus, Flame, Sparkles, Megaphone } from "lucide-react";
import OfflineIndicator from "@/components/OfflineIndicator";
import { Button } from "@/components/ui/button";

const STUDENT_TABS = [
  { to: "/dashboard", label: "Home", icon: Home, id: "nav-home" },
  { to: "/report", label: "Report", icon: AlertOctagon, id: "nav-report" },
  { to: "/notifications", label: "Alerts", icon: Bell, id: "nav-notifs" },
  { to: "/assistant", label: "AI Aid", icon: MessageCircle, id: "nav-assistant" },
  { to: "/profile", label: "Me", icon: User, id: "nav-profile" },
];

const RESPONDER_TABS = [
  { to: "/responder", label: "Queue", icon: LayoutDashboard, id: "nav-responder-queue" },
  { to: "/notifications", label: "Alerts", icon: Bell, id: "nav-notifs" },
  { to: "/profile", label: "Me", icon: User, id: "nav-profile" },
];

const ADMIN_TABS = [
  { to: "/admin", label: "Command", icon: LayoutDashboard, id: "nav-admin-cmd" },
  { to: "/admin/incidents", label: "Incidents", icon: Activity, id: "nav-admin-inc" },
  { to: "/admin/heatmap", label: "Heatmap", icon: Flame, id: "nav-admin-heat" },
  { to: "/admin/announcements", label: "Alerts", icon: Megaphone, id: "nav-admin-ann" },
  { to: "/admin/fraud", label: "Fraud", icon: FileWarning, id: "nav-admin-fraud" },
  { to: "/admin/teams", label: "Teams", icon: UserPlus, id: "nav-admin-teams" },
  { to: "/admin/agents", label: "Agents", icon: Sparkles, id: "nav-admin-agents" },
];

const DEPT_TABS = [
  { to: "/department", label: "Ops", icon: ShieldCheck, id: "nav-dept-ops" },
  { to: "/admin/incidents", label: "Incidents", icon: Activity, id: "nav-dept-inc" },
  { to: "/admin/teams", label: "Teams", icon: UserPlus, id: "nav-dept-teams" },
  { to: "/notifications", label: "Alerts", icon: Bell, id: "nav-notifs" },
  { to: "/profile", label: "Me", icon: User, id: "nav-profile" },
];

export default function Layout({ children, dark = false }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const role = user?.role;
  const tabs = role === "student" ? STUDENT_TABS
    : role === "responder" ? RESPONDER_TABS
    : role === "head_admin" ? ADMIN_TABS
    : role === "dept_admin" || role === "dept_personnel" ? DEPT_TABS
    : STUDENT_TABS;

  const doLogout = () => { logout(); nav("/login"); };

  return (
    <div className={dark ? "min-h-screen bg-slate-950 text-slate-100" : "min-h-screen bg-slate-50 text-slate-900"}>
      <header className={`sticky top-0 z-30 border-b ${dark ? "bg-slate-900/80 border-slate-800 backdrop-blur-lg" : "bg-white/90 border-slate-200 backdrop-blur"}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Shield className="w-5 h-5 text-slate-950" strokeWidth={2.5} />
            </div>
            <div className="min-w-0">
              <div className="font-display font-extrabold text-base leading-tight tracking-tight">CampusResQ<span className="text-cyan-500">.AI</span></div>
              <div className={`text-[10px] uppercase tracking-[0.18em] ${dark ? "text-slate-400" : "text-slate-500"}`}>{role?.replace(/_/g, " ")}</div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-1">
            {tabs.map((t) => (
              <NavLink key={t.to} to={t.to} data-testid={t.id}
                className={({ isActive }) => `px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${isActive ? (dark ? "bg-cyan-500/15 text-cyan-300" : "bg-cyan-50 text-cyan-700") : (dark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-100")}`}>
                <t.icon className="w-4 h-4 inline mr-1.5 -mt-0.5" />{t.label}
              </NavLink>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <OfflineIndicator />
            <Button data-testid="logout-btn" size="sm" variant="ghost" onClick={doLogout} className="gap-1.5">
              <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="pb-24 md:pb-8">{children}</main>

      {/* Mobile bottom nav */}
      <nav className={`md:hidden fixed bottom-0 inset-x-0 z-30 border-t ${dark ? "bg-slate-900/95 border-slate-800" : "bg-white/95 border-slate-200"} backdrop-blur-lg`}>
        <div className="grid grid-cols-5 max-w-lg mx-auto">
          {tabs.slice(0, 5).map((t) => (
            <NavLink key={t.to} to={t.to} data-testid={`m-${t.id}`}
              className={({ isActive }) => `flex flex-col items-center gap-1 py-2.5 text-[11px] font-semibold ${isActive ? "text-cyan-500" : (dark ? "text-slate-400" : "text-slate-600")}`}>
              <t.icon className="w-5 h-5" /> {t.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
