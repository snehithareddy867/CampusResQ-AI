import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield } from "lucide-react";

export default function Splash() {
  const nav = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem("crq_token");
    const t = setTimeout(() => nav(token ? "/go" : "/welcome"), 1500);
    return () => clearTimeout(t);
  }, [nav]);
  return (
    <div className="min-h-screen bg-slate-950 text-white grid place-items-center overflow-hidden relative">
      <div className="absolute inset-0 opacity-30" style={{backgroundImage:"radial-gradient(circle at 20% 20%, #00E5FF 0%, transparent 50%), radial-gradient(circle at 80% 80%, #0A192F 0%, transparent 60%)"}}/>
      <motion.div initial={{scale:.6, opacity:0}} animate={{scale:1, opacity:1}} transition={{duration:.6}} className="relative flex flex-col items-center gap-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-2xl shadow-cyan-500/50">
          <Shield className="w-11 h-11 text-slate-950" strokeWidth={2.5} />
        </div>
        <h1 data-testid="splash-title" className="font-display text-4xl font-extrabold tracking-tight">CampusResQ<span className="text-cyan-400">.AI</span></h1>
        <p className="text-sm text-slate-400 uppercase tracking-[0.3em]">Agentic Campus Safety</p>
      </motion.div>
    </div>
  );
}
