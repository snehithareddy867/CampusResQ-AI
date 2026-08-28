import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MapPin, Loader2, Upload, AlertOctagon } from "lucide-react";
import client, { enqueueOfflineOp } from "@/lib/api";
import { toast } from "sonner";

export default function ReportEmergency() {
  const nav = useNavigate();
  const [desc, setDesc] = useState("");
  const [loc, setLoc] = useState(null);
  const [address, setAddress] = useState("");
  const [evidence, setEvidence] = useState([]);
  const [busy, setBusy] = useState(false);

  const detectLocation = () => {
    if (!navigator.geolocation) return toast.error("Geolocation not supported");
    setBusy(true);
    navigator.geolocation.getCurrentPosition((pos) => {
      setLoc({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      setAddress(`${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}`);
      setBusy(false);
      toast.success("Location captured");
    }, () => {
      setLoc({ lat: 12.9716, lng: 77.5946 });
      setAddress("Approx campus center");
      setBusy(false);
      toast.warning("Using approx. location");
    }, { timeout: 8000, enableHighAccuracy: true });
  };

  const onFile = (e) => {
    const files = Array.from(e.target.files || []).slice(0, 3);
    const reads = files.map(f => new Promise((res) => {
      const r = new FileReader();
      r.onload = () => res({ kind: f.type.startsWith("image") ? "image" : f.type.startsWith("audio") ? "audio" : "video", data_url: r.result, filename: f.name });
      r.readAsDataURL(f);
    }));
    Promise.all(reads).then(setEvidence);
  };

  const submit = async () => {
    if (!desc.trim()) return toast.error("Describe the emergency");
    if (!loc) return toast.error("Location required");
    setBusy(true);
    const op_id = `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const payload = { description: desc, location: { ...loc, address }, evidence, client_op_id: op_id };
    if (!navigator.onLine) {
      enqueueOfflineOp({ type: "report", op_id, payload });
      toast.warning("Saved offline. Will sync when online.");
      setBusy(false);
      nav("/dashboard");
      return;
    }
    try {
      const r = await client.post("/emergencies", payload);
      toast.success("Report received");
      nav(`/emergency/${r.data.id}`);
    } catch (e) {
      enqueueOfflineOp({ type: "report", op_id, payload });
      toast.warning("Backend unreachable — saved to offline queue");
      nav("/dashboard");
    } finally { setBusy(false); }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <div className="inline-flex items-center gap-2 text-red-600 font-semibold text-sm"><AlertOctagon className="w-4 h-4" /> Report Emergency</div>
          <h1 className="font-display text-3xl font-extrabold mt-1">Tell us what&apos;s happening</h1>
          <p className="text-slate-500 text-sm mt-1">Our AI will classify, route and dispatch. Focus on facts.</p>
        </div>

        <div className="space-y-2">
          <Label>What&apos;s the situation?</Label>
          <Textarea data-testid="report-desc" rows={5} value={desc} onChange={(e)=>setDesc(e.target.value)}
            placeholder="e.g., There is smoke coming from the electrical room in Block C. Two students nearby coughing."/>
        </div>

        <div className="space-y-2">
          <Label>Location</Label>
          <div className="flex gap-2">
            <Input data-testid="report-address" value={address} onChange={(e)=>setAddress(e.target.value)} placeholder="Auto-detect or type" />
            <Button data-testid="report-locate-btn" type="button" variant="outline" onClick={detectLocation} disabled={busy}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin"/> : <MapPin className="w-4 h-4"/>}
            </Button>
          </div>
          {loc && <p className="text-xs text-slate-500 font-mono">lat {loc.lat.toFixed(5)}, lng {loc.lng.toFixed(5)}</p>}
        </div>

        <div className="space-y-2">
          <Label>Evidence (optional)</Label>
          <label className="block cursor-pointer border-2 border-dashed border-slate-200 hover:border-cyan-400 rounded-xl p-6 text-center transition-colors">
            <Upload className="w-6 h-6 mx-auto text-slate-400 mb-2"/>
            <div className="text-sm text-slate-600">Photos, audio, or short videos</div>
            <input data-testid="report-file-input" type="file" multiple accept="image/*,audio/*,video/*" className="hidden" onChange={onFile} />
          </label>
          {evidence.length > 0 && <p className="text-xs text-emerald-700">{evidence.length} file(s) attached</p>}
        </div>

        <Button data-testid="report-submit-btn" onClick={submit} disabled={busy} className="w-full h-12 bg-red-500 hover:bg-red-600 text-base font-semibold">
          {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2"/> : null} Send Report
        </Button>
      </div>
    </Layout>
  );
}
