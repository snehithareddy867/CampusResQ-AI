import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import client from "@/lib/api";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import { Flame } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function HeatLayer({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points || points.length === 0) return;
    const layer = L.heatLayer(
      points.map(p => [p.lat, p.lng, p.weight || 0.5]),
      { radius: 30, blur: 24, maxZoom: 17,
        gradient: { 0.2: "#22d3ee", 0.4: "#3b82f6", 0.6: "#f59e0b", 0.8: "#ef4444", 1.0: "#7f1d1d" } }
    ).addTo(map);
    // fit bounds
    const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]));
    if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
    return () => { map.removeLayer(layer); };
  }, [points, map]);
  return null;
}

export default function AdminHeatmap() {
  const [data, setData] = useState({ points: [], window_hours: 168 });
  const [hours, setHours] = useState("168");
  useEffect(() => { client.get(`/admin/heatmap?hours=${hours}`).then(r => setData(r.data)); }, [hours]);

  const byDept = data.points.reduce((acc, p) => {
    const k = p.department || "unknown";
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});

  return (
    <Layout dark>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-xs uppercase font-bold tracking-[0.25em] text-cyan-400">Analytics</p>
            <h1 className="font-display text-3xl font-extrabold mt-1 flex items-center gap-2"><Flame className="w-6 h-6 text-red-400"/>Campus Incident Heatmap</h1>
            <p className="text-sm text-slate-400 mt-1">{data.points.length} incidents in last {data.window_hours}h</p>
          </div>
          <Select value={hours} onValueChange={setHours}>
            <SelectTrigger data-testid="heatmap-hours" className="w-40 bg-slate-900 border-slate-800"><SelectValue/></SelectTrigger>
            <SelectContent>
              <SelectItem value="24">Last 24 hours</SelectItem>
              <SelectItem value="72">Last 3 days</SelectItem>
              <SelectItem value="168">Last 7 days</SelectItem>
              <SelectItem value="720">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="rounded-2xl overflow-hidden border border-slate-800" style={{ height: 500 }} data-testid="heatmap-container">
          <MapContainer center={[12.9716, 77.5946]} zoom={15} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
            <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <HeatLayer points={data.points} />
          </MapContainer>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(byDept).map(([d, c]) => (
            <div key={d} className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-xs uppercase text-slate-400 tracking-widest capitalize">{d.replace(/_/g," ")}</div>
              <div className="font-mono text-2xl font-bold mt-1">{c}</div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
