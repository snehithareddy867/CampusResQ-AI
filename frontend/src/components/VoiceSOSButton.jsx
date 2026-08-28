import React, { useRef, useState } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import client from "@/lib/api";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const LANGS = [
  { code: "en-US", label: "English" },
  { code: "hi-IN", label: "हिन्दी" },
  { code: "ta-IN", label: "தமிழ்" },
  { code: "te-IN", label: "తెలుగు" },
  { code: "kn-IN", label: "ಕನ್ನಡ" },
];

export default function VoiceSOSButton() {
  const nav = useNavigate();
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [lang, setLang] = useState("en-US");
  const [submitting, setSubmitting] = useState(false);
  const recRef = useRef(null);

  if (!SpeechRecognition) return null;

  const start = () => {
    setTranscript("");
    const rec = new SpeechRecognition();
    rec.lang = lang;
    rec.interimResults = true;
    rec.continuous = true;
    let text = "";
    rec.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const s = e.results[i][0].transcript;
        if (e.results[i].isFinal) text += s + " ";
        else interim += s;
      }
      setTranscript((text + interim).trim());
    };
    rec.onerror = (e) => { toast.error("Voice error: " + e.error); setRecording(false); };
    rec.onend = () => { setRecording(false); };
    recRef.current = rec;
    setRecording(true);
    rec.start();
  };

  const stop = async () => {
    if (recRef.current) { try { recRef.current.stop(); } catch {} }
    setRecording(false);
    const text = transcript.trim();
    if (!text) return toast.info("No speech captured");
    submitVoice(text);
  };

  const submitVoice = async (text) => {
    setSubmitting(true);
    const send = (loc) => client.post("/voice/sos", { transcript: text, location: loc, language: lang })
      .then((r) => { toast.success("Voice SOS sent"); nav(`/emergency/${r.data.id}`); })
      .catch((e) => toast.error(e?.response?.data?.detail || "Failed"))
      .finally(() => setSubmitting(false));
    if (!navigator.geolocation) return send({ lat: 12.9716, lng: 77.5946, address: "Approx." });
    navigator.geolocation.getCurrentPosition(
      (p) => send({ lat: p.coords.latitude, lng: p.coords.longitude, address: "Voice SOS location" }),
      () => send({ lat: 12.9716, lng: 77.5946, address: "Approx." }),
      { timeout: 6000 }
    );
  };

  return (
    <div className="rounded-2xl border border-cyan-200 bg-cyan-50/60 p-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <p className="uppercase text-xs font-bold tracking-[0.2em] text-cyan-700 flex items-center gap-1"><Mic className="w-3.5 h-3.5"/>Voice SOS</p>
          <p className="text-sm text-slate-700 mt-0.5">Hands-free · speak in your language.</p>
        </div>
        <div className="flex items-center gap-2">
          <select data-testid="voice-lang-select" value={lang} onChange={(e)=>setLang(e.target.value)} disabled={recording}
            className="text-xs rounded-md border border-slate-300 bg-white px-2 py-1.5">
            {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
          {!recording ? (
            <Button data-testid="voice-sos-start" onClick={start} size="sm" className="bg-slate-950 hover:bg-slate-800">
              <Mic className="w-4 h-4 mr-1"/>Speak
            </Button>
          ) : (
            <Button data-testid="voice-sos-stop" onClick={stop} disabled={submitting} size="sm" className="bg-red-500 hover:bg-red-600 text-white">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-1"/> : <MicOff className="w-4 h-4 mr-1"/>}
              {submitting ? "Sending..." : "Stop & Send"}
            </Button>
          )}
        </div>
      </div>
      {(recording || transcript) && (
        <div className="mt-3 p-3 rounded-lg bg-white border border-slate-200 min-h-[3rem] text-sm text-slate-800" data-testid="voice-transcript">
          {transcript || <span className="text-slate-400 italic">Listening…</span>}
        </div>
      )}
    </div>
  );
}
