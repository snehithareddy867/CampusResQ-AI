import React, { useState, useEffect } from "react";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, Send, Loader2 } from "lucide-react";
import client from "@/lib/api";
import { useSearchParams } from "react-router-dom";

export default function AssistantChat() {
  const [msgs, setMsgs] = useState([
    { role: "assistant", text: "Hi — I'm your safety assistant. Ask me anything about emergencies, safety steps, or your active incident." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [params] = useSearchParams();
  const incident_id = params.get("incident") || null;

  const send = async () => {
    if (!input.trim()) return;
    const q = input.trim();
    setMsgs(m => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const r = await client.post("/ai/assistant", { message: q, incident_id });
      setMsgs(m => [...m, { role: "assistant", text: r.data.reply }]);
    } catch {
      setMsgs(m => [...m, { role: "assistant", text: "I'm having trouble reaching the AI service. Stay calm; if this is critical, use SOS." }]);
    } finally { setBusy(false); }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 flex flex-col h-[calc(100vh-6rem)]">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-9 h-9 rounded-lg bg-cyan-500 flex items-center justify-center"><Sparkles className="w-4.5 h-4.5 text-white"/></div>
          <div>
            <h1 className="font-display font-extrabold text-xl">AI Safety Assistant</h1>
            <p className="text-xs text-slate-500">Powered by Claude Sonnet 4.6 · Guidance only</p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {msgs.map((m, i) => (
            <div key={i} data-testid={`chat-msg-${i}`} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={`${m.role === "user" ? "bg-slate-950 text-white" : "bg-white border border-slate-200"} max-w-[85%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed`}>{m.text}</div>
            </div>
          ))}
          {busy && <div className="flex justify-start"><div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-500"><Loader2 className="w-4 h-4 inline animate-spin mr-2"/>Thinking…</div></div>}
        </div>
        <div className="mt-4 flex gap-2">
          <Input data-testid="chat-input" value={input} onChange={(e)=>setInput(e.target.value)}
            onKeyDown={(e)=>e.key==='Enter' && !busy && send()} placeholder="Ask about first aid, evacuation, safety…" />
          <Button data-testid="chat-send" onClick={send} disabled={busy}><Send className="w-4 h-4"/></Button>
        </div>
      </div>
    </Layout>
  );
}
