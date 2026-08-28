import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertOctagon } from "lucide-react";

export default function SOSButton({ onTrigger, disabled }) {
  const [progress, setProgress] = useState(0);
  const [holding, setHolding] = useState(false);
  const timerRef = useRef(null);
  const rafRef = useRef(null);

  const start = () => {
    if (disabled) return;
    setHolding(true);
    const startT = performance.now();
    const tick = () => {
      const p = Math.min(1, (performance.now() - startT) / 1500);
      setProgress(p);
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    timerRef.current = setTimeout(() => {
      setHolding(false); setProgress(0);
      onTrigger?.();
    }, 1500);
  };
  const cancel = () => {
    setHolding(false); setProgress(0);
    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  };

  return (
    <div className="relative inline-flex flex-col items-center gap-3">
      <motion.button
        data-testid="sos-trigger-btn"
        aria-label="Emergency SOS. Press and hold to trigger."
        onMouseDown={start} onMouseUp={cancel} onMouseLeave={cancel}
        onTouchStart={(e) => { e.preventDefault(); start(); }} onTouchEnd={cancel}
        whileTap={{ scale: 0.94 }}
        className="relative w-52 h-52 rounded-full bg-gradient-to-br from-red-500 to-red-600 text-white font-display font-extrabold text-4xl tracking-widest shadow-[0_0_60px_rgba(239,68,68,0.35)] pulse-critical select-none"
      >
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="4" />
          <circle cx="50" cy="50" r="46" fill="none" stroke="#fff" strokeWidth="4"
            strokeDasharray={`${progress * 289} 289`} strokeLinecap="round" />
        </svg>
        <div className="relative flex flex-col items-center justify-center h-full">
          <AlertOctagon className="w-12 h-12 mb-1" strokeWidth={2.5} />
          <span>SOS</span>
        </div>
      </motion.button>
      <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">
        {holding ? "Keep Holding..." : "Press & Hold 1.5s"}
      </p>
    </div>
  );
}
