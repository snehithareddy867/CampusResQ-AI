import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import Splash from "@/pages/Splash";
import Welcome from "@/pages/Welcome";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import StudentDashboard from "@/pages/StudentDashboard";
import ReportEmergency from "@/pages/ReportEmergency";
import EmergencyDetail from "@/pages/EmergencyDetail";
import Notifications from "@/pages/Notifications";
import AssistantChat from "@/pages/AssistantChat";
import Profile from "@/pages/Profile";
import ResponderDashboard from "@/pages/ResponderDashboard";
import AdminCommandCenter from "@/pages/AdminCommandCenter";
import AdminIncidents from "@/pages/AdminIncidents";
import AdminFraud from "@/pages/AdminFraud";
import AdminResponders from "@/pages/AdminResponders";
import AdminAudit from "@/pages/AdminAudit";
import TeamsAdmin from "@/pages/TeamsAdmin";
import AdminHeatmap from "@/pages/AdminHeatmap";
import AdminReplay from "@/pages/AdminReplay";
import AgentsInfo from "@/pages/AgentsInfo";
import Announcements from "@/pages/Announcements";
import DepartmentDashboard from "@/pages/DepartmentDashboard";
import "@/App.css";

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen grid place-items-center text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function RoleRouter() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "student") return <Navigate to="/dashboard" replace />;
  if (user.role === "responder") return <Navigate to="/responder" replace />;
  if (user.role === "head_admin") return <Navigate to="/admin" replace />;
  if (user.role === "dept_admin" || user.role === "dept_personnel") return <Navigate to="/department" replace />;
  return <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Toaster position="top-right" richColors />
          <Routes>
            <Route path="/" element={<Splash />} />
            <Route path="/welcome" element={<Welcome />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/go" element={<RoleRouter />} />

            <Route path="/dashboard" element={<Protected roles={["student"]}><StudentDashboard /></Protected>} />
            <Route path="/report" element={<Protected roles={["student"]}><ReportEmergency /></Protected>} />
            <Route path="/emergency/:id" element={<Protected><EmergencyDetail /></Protected>} />
            <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
            <Route path="/assistant" element={<Protected><AssistantChat /></Protected>} />
            <Route path="/profile" element={<Protected><Profile /></Protected>} />

            <Route path="/responder" element={<Protected roles={["responder"]}><ResponderDashboard /></Protected>} />

            <Route path="/department" element={<Protected roles={["dept_admin", "dept_personnel"]}><DepartmentDashboard /></Protected>} />

            <Route path="/admin" element={<Protected roles={["head_admin"]}><AdminCommandCenter /></Protected>} />
            <Route path="/admin/incidents" element={<Protected roles={["head_admin", "dept_admin"]}><AdminIncidents /></Protected>} />
            <Route path="/admin/fraud" element={<Protected roles={["head_admin"]}><AdminFraud /></Protected>} />
            <Route path="/admin/responders" element={<Protected roles={["head_admin", "dept_admin"]}><AdminResponders /></Protected>} />
            <Route path="/admin/audit" element={<Protected roles={["head_admin"]}><AdminAudit /></Protected>} />
            <Route path="/admin/teams" element={<Protected roles={["head_admin", "dept_admin"]}><TeamsAdmin /></Protected>} />
            <Route path="/admin/heatmap" element={<Protected roles={["head_admin", "dept_admin"]}><AdminHeatmap /></Protected>} />
            <Route path="/admin/replay/:id" element={<Protected roles={["head_admin", "dept_admin"]}><AdminReplay /></Protected>} />
            <Route path="/admin/agents" element={<Protected roles={["head_admin", "dept_admin"]}><AgentsInfo /></Protected>} />
            <Route path="/admin/announcements" element={<Protected roles={["head_admin"]}><Announcements /></Protected>} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}
