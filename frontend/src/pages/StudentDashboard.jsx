import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import SOSButton from "@/components/SOSButton";
import VoiceSOSButton from "@/components/VoiceSOSButton";
import EmergencyCard from "@/components/EmergencyCard";
import client from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { AlertOctagon, MessageCircle, Bell, Activity } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { subscribeWS } from "@/lib/ws";
import { useT } from "@/lib/i18n";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function StudentDashboard() {
  const { user } = useAuth();
  const nav = useNavigate();
  const { t } = useT();
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get("/emergencies?mine=true").then(r => setIncidents(r.data)).finally(()=>setLoading(false));
    const t = setInterval(() => { client.get("/emergencies?mine=true").then(r=>setIncidents(r.data)).catch(()=>{}); }, 8000);
    const unsub = subscribeWS(() => { client.get("/emergencies?mine=true").then(r=>setIncidents(r.data)).catch(()=>{}); });
    return () => { clearInterval(t); unsub(); };
  }, []);

  const triggerSOS = async () => {
    if (!navigator.geolocation) return toast.error("Geolocation not supported");
    navigator.geolocation.getCurrentPosition(async (pos) => {
      try {
        const r = await client.post("/emergencies", {
          description: "SOS triggered by user - urgent assistance required.",
          location: { lat: pos.coords.latitude, lng: pos.coords.longitude, address: "SOS location" },
          is_sos: true,
        });
        toast.success("SOS sent!");
        nav(`/emergency/${r.data.id}`);
      } catch (e) { toast.error(e?.response?.data?.detail || "SOS failed"); }
    }, () => {
      // fallback to campus center
      client.post("/emergencies", {
        description: "SOS triggered — location unavailable.",
        location: { lat: 12.9716, lng: 77.5946, address: "Approx. campus location" },
        is_sos: true,
      }).then((r) => { toast.warning("SOS sent (approx. location)"); nav(`/emergency/${r.data.id}`); });
    });
  };

  const active = incidents.filter(i => !["resolved", "cancelled"].includes(i.status));
  const past = incidents.filter(i => ["resolved", "cancelled"].includes(i.status));

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        <section>
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <p className="text-sm text-slate-500">{t("hello")}, <span className="font-semibold text-slate-900">{user?.name}</span></p>
            <LanguageSwitcher />
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-extrabold mt-1 tracking-tight">{t("protected")}</h1>
        </section>

        <section className="grid md:grid-cols-2 gap-6 items-center bg-gradient-to-br from-red-50 to-white rounded-2xl border border-red-100 p-6 sm:p-8">
          <div className="flex justify-center">
            <SOSButton onTrigger={triggerSOS} />
          </div>
          <div className="space-y-4">
            <div>
              <p className="uppercase text-xs font-bold tracking-[0.2em] text-red-600">Emergency SOS</p>
              <h2 className="font-display text-2xl font-extrabold mt-1">{t("sos_title")}<br/>{t("sos_hint")}</h2>
              <p className="text-sm text-slate-600 mt-3 leading-relaxed">{t("sos_desc")}</p>
              <Link to="/report" data-testid="report-detailed-link" className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-cyan-600 hover:underline">
                <AlertOctagon className="w-4 h-4"/> {t("report_link")}
              </Link>
            </div>
            <VoiceSOSButton />
          </div>
        </section>

        <section className="grid grid-cols-3 gap-3 sm:gap-4">
          {[{ to:"/report", icon: AlertOctagon, label:t("quick_report"), tid:"quick-report" },
            { to:"/assistant", icon: MessageCircle, label:t("quick_assistant"), tid:"quick-assistant" },
            { to:"/notifications", icon: Bell, label:t("quick_notifs"), tid:"quick-notifs" }].map((q) => (
            <Link key={q.to} data-testid={q.tid} to={q.to} className="p-4 rounded-xl bg-white border border-slate-200 hover:border-cyan-400 transition-colors">
              <q.icon className="w-5 h-5 text-cyan-600" />
              <div className="mt-2 text-sm font-semibold">{q.label}</div>
            </Link>
          ))}
        </section>

        <section>
          <div className="flex items-center gap-2 mb-3"><Activity className="w-4 h-4 text-cyan-600"/><h2 className="font-display font-bold text-lg">{t("active")}</h2></div>
          {loading ? <div className="text-slate-500 text-sm">Loading…</div>
            : active.length === 0 ? <div className="p-8 rounded-xl bg-white border border-slate-200 text-center text-slate-500">{t("all_clear")}</div>
            : <div className="space-y-3">{active.map(i => <EmergencyCard key={i.id} incident={i} />)}</div>}
        </section>

        {past.length > 0 && (
          <section>
            <h2 className="font-display font-bold text-lg mb-3">{t("history")}</h2>
            <div className="space-y-3">{past.map(i => <EmergencyCard key={i.id} incident={i} />)}</div>
          </section>
        )}
      </div>
    </Layout>
  );
}
