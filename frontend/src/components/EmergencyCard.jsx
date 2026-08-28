import React from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, MapPin, Clock } from "lucide-react";
import { motion } from "framer-motion";

const STATUS_COLORS = {
  submitted: "bg-slate-100 text-slate-700",
  analyzing: "bg-cyan-50 text-cyan-700 border-cyan-200",
  classified: "bg-cyan-50 text-cyan-700 border-cyan-200",
  fraud_review: "bg-amber-50 text-amber-700 border-amber-200",
  assigning: "bg-blue-50 text-blue-700 border-blue-200",
  waiting_for_acceptance: "bg-amber-50 text-amber-800 border-amber-300 font-semibold",
  assigned: "bg-blue-100 text-blue-800 border-blue-300",
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  en_route: "bg-emerald-100 text-emerald-800 border-emerald-300",
  arrived: "bg-emerald-100 text-emerald-800 border-emerald-300",
  resolved: "bg-slate-100 text-slate-700 border-slate-200",
  reopened: "bg-red-50 text-red-700 border-red-200",
  cancelled: "bg-slate-100 text-slate-500",
  escalated: "bg-red-100 text-red-800 border-red-300",
};
const PRIO_COLORS = {
  low: "bg-slate-100 text-slate-700",
  medium: "bg-blue-50 text-blue-700",
  high: "bg-amber-50 text-amber-800",
  critical: "bg-red-100 text-red-800 border border-red-300",
};

export default function EmergencyCard({ incident, linkPrefix = "/emergency" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="group"
    >
      <Link
        to={`${linkPrefix}/${incident.id}`}
        data-testid={`incident-card-${incident.id}`}
        className="block rounded-xl bg-white border border-slate-200 hover:border-cyan-400 hover:shadow-lg transition-[border-color,box-shadow] p-5"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge className={`${STATUS_COLORS[incident.status] || "bg-slate-100"} border`}>{incident.status?.replace(/_/g, " ")}</Badge>
              {incident.priority && <Badge className={PRIO_COLORS[incident.priority]}>{incident.priority}</Badge>}
              {incident.is_sos && <Badge className="bg-red-600 text-white">SOS</Badge>}
            </div>
            <h3 className="font-display font-bold text-lg text-slate-900 truncate">
              {incident.ai_analysis?.category || "Analyzing..."}
            </h3>
            <p className="text-sm text-slate-600 line-clamp-2 mt-1">{incident.description}</p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{incident.location?.address || `${incident.location?.lat?.toFixed(4)}, ${incident.location?.lng?.toFixed(4)}`}</span>
              <span className="inline-flex items-center gap-1 font-mono"><Clock className="w-3.5 h-3.5" />{new Date(incident.reported_at).toLocaleTimeString()}</span>
              {incident.eta_minutes != null && <span className="font-mono text-cyan-700">ETA {incident.eta_minutes} min</span>}
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-cyan-500 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </Link>
    </motion.div>
  );
}
