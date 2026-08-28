import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Zap, MapPin, Users } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Welcome() {
  const features = [
    { icon: Zap, title: "Instant AI Triage", body: "Multi-agent classification, fraud detection & routing in seconds." },
    { icon: MapPin, title: "Live Tracking", body: "Real-time responder location & ETA on a campus map." },
    { icon: Users, title: "Coordinated Response", body: "Every department, one command center." },
  ];
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-6xl mx-auto px-6 sm:px-10 pt-16 pb-24">
        <header className="flex items-center justify-between mb-16">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-slate-950 flex items-center justify-center"><Shield className="w-5 h-5 text-cyan-400" /></div>
            <span className="font-display font-extrabold text-lg">CampusResQ<span className="text-cyan-500">.AI</span></span>
          </div>
          <div className="flex gap-2">
            <Link to="/login"><Button data-testid="nav-login-btn" variant="ghost">Login</Button></Link>
            <Link to="/register"><Button data-testid="nav-register-btn" className="bg-slate-950 hover:bg-slate-800">Get Started</Button></Link>
          </div>
        </header>

        <motion.div initial={{opacity:0, y:24}} animate={{opacity:1, y:0}} transition={{duration:.6}} className="max-w-3xl">
          <p className="uppercase text-xs font-bold tracking-[0.25em] text-cyan-600 mb-4">Agentic Campus Safety Platform</p>
          <h1 className="font-display text-5xl sm:text-6xl font-extrabold tracking-tight leading-[1.05] text-slate-950">
            Every emergency, <span className="text-cyan-500">answered</span>.<br/>Every second, <span className="text-cyan-500">accounted</span>.
          </h1>
          <p className="mt-6 text-lg text-slate-600 max-w-2xl leading-relaxed">
            A multi-agent AI command system that classifies, triages, dispatches and coordinates every campus emergency — with humans in the loop for the critical calls.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register"><Button data-testid="cta-start-btn" size="lg" className="bg-red-500 hover:bg-red-600 text-white font-semibold text-base h-12 px-8">Report an Emergency</Button></Link>
            <Link to="/login"><Button data-testid="cta-signin-btn" size="lg" variant="outline" className="h-12 px-8">Sign in to your Portal</Button></Link>
          </div>
        </motion.div>

        <div className="mt-24 grid md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div key={i} initial={{opacity:0, y:16}} animate={{opacity:1, y:0}} transition={{delay: 0.1*i}}
              className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-cyan-400 transition-colors">
              <div className="w-11 h-11 rounded-lg bg-cyan-50 border border-cyan-200 flex items-center justify-center mb-4"><f.icon className="w-5 h-5 text-cyan-600"/></div>
              <h3 className="font-display font-bold text-lg mb-1.5">{f.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
