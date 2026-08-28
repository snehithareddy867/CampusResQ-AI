import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Layout from "@/components/Layout";
import LiveMap from "@/components/LiveMap";
import client from "@/lib/api";
import { Play, Pause, Rewind } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

export default function AdminReplay() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [tick, setTick] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => { client.get(`/admin/incidents/${id}/replay`).then(r => setData(r.data)); }, [id]);
  useEffect(() => {
    if (!playing || !data) return;
    const t = setInterval(() => setTick(v => Math.min(v + 1, totalSteps - 1)), 500);
    return () => clearInterval(t);
  }, [playing, data, totalSteps]);

  const totalSteps = data ? Math.max(1, (data.timeline?.length || 0)) : 1;

  const events = useMemo(() => {
    if (!data) return [];
    // merge timeline entries + location updates by timestamp
    const items = [
      ...(data.timeline || []).map(t => ({ ...t, kind: "timeline" })),
      ...(data.location_history || []).map(l => ({ at: l.updated_at, text: `GPS: ${l.lat.toFixed(5)}, ${l.lng.toFixed(5)}`, loc: l, kind: "location" })),
    ].filter(x => x.at).sort((a, b) => a.at.localeCompare(b.at));
    return items;
  }, [data]);

  const currentIdx = Math.min(tick, events.length - 1);
  const uptoNow = events.slice(0, currentIdx + 1);
  const lastLoc = [...uptoNow].reverse().find(e => e.kind === "location");
  const snapshotIncident = data ? {
    location: data.location,
    responder_location: lastLoc?.loc,
    assigned_responder_name: data.assigned_responder_name,
  } : null;

  if (!data) return <Layout dark><div className="p-10 text-slate-400 text-center">Loading replay…</div></Layout>;

  return (
    <Layout dark>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <div>
          <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Incident Replay</p>
          <h1 className="font-display text-3xl font-extrabold mt-1">{data.ai_analysis?.category || "Incident"}</h1>
          <p className="text-slate-400 text-sm mt-1">{data.description} · Reporter: {data.reporter_name}</p>
        </div>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <LiveMap incident={snapshotIncident} height={360} />
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 max-h-[400px] overflow-y-auto">
            <div className="text-xs uppercase font-bold tracking-widest text-slate-400 mb-3">Events (up to now)</div>
            <ol className="space-y-2">
              {uptoNow.map((e, i) => (
                <li key={i} className="flex gap-2 text-xs">
                  <span className="font-mono text-slate-500 w-16 shrink-0">{new Date(e.at).toLocaleTimeString()}</span>
                  <span className={e.kind === "location" ? "text-cyan-300" : "text-slate-200"}>{e.text}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Button data-testid="replay-play" size="sm" onClick={() => setPlaying(p => !p)} className="bg-cyan-500 hover:bg-cyan-600 text-slate-950">
              {playing ? <Pause className="w-4 h-4"/> : <Play className="w-4 h-4"/>}
            </Button>
            <Button data-testid="replay-rewind" size="sm" variant="outline" className="border-slate-700 hover:bg-slate-800" onClick={() => { setTick(0); setPlaying(false); }}>
              <Rewind className="w-4 h-4"/>
            </Button>
            <div className="font-mono text-xs text-slate-400">step {currentIdx + 1} / {events.length}</div>
          </div>
          <Slider data-testid="replay-slider" value={[tick]} min={0} max={Math.max(0, events.length - 1)} step={1} onValueChange={(v) => setTick(v[0])} />
        </div>
      </div>
    </Layout>
  );
}
