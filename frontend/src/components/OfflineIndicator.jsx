import React, { useEffect, useState } from "react";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";
import { flushQueue, getQueue } from "@/lib/api";

export default function OfflineIndicator() {
  const [online, setOnline] = useState(navigator.onLine);
  const [queueSize, setQueueSize] = useState(getQueue().length);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    const t = setInterval(() => setQueueSize(getQueue().length), 2000);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); clearInterval(t); };
  }, []);

  useEffect(() => {
    if (online && queueSize > 0 && !syncing) {
      setSyncing(true);
      flushQueue().then(() => { setQueueSize(getQueue().length); setSyncing(false); });
    }
  }, [online, queueSize, syncing]);

  if (online && queueSize === 0) {
    return (
      <div data-testid="online-indicator" className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600">
        <Wifi className="w-3.5 h-3.5" /> Online
      </div>
    );
  }
  if (!online) {
    return (
      <div data-testid="offline-indicator" className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded-full border border-amber-200">
        <WifiOff className="w-3.5 h-3.5" /> Offline · {queueSize} queued
      </div>
    );
  }
  return (
    <div data-testid="syncing-indicator" className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-600">
      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Syncing {queueSize}...
    </div>
  );
}
