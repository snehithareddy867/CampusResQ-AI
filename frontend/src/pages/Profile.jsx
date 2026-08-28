import React, { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Mail, Shield, Building2, HeartHandshake, Save } from "lucide-react";
import client from "@/lib/api";
import { toast } from "sonner";

export default function Profile() {
  const { user } = useAuth();
  const [me, setMe] = useState(user);
  const [buddyName, setBuddyName] = useState("");
  const [buddyEmail, setBuddyEmail] = useState("");
  const [buddyPhone, setBuddyPhone] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    client.get("/auth/me").then(r => {
      setMe(r.data);
      setBuddyName(r.data.buddy_name || "");
      setBuddyEmail(r.data.buddy_email || "");
      setBuddyPhone(r.data.buddy_phone || "");
      setPhone(r.data.phone || "");
    });
  }, []);

  const save = async () => {
    setBusy(true);
    try {
      const r = await client.put("/users/me", { buddy_name: buddyName, buddy_email: buddyEmail, buddy_phone: buddyPhone, phone });
      setMe(r.data);
      localStorage.setItem("crq_user", JSON.stringify(r.data));
      toast.success("Profile saved");
    } catch (e) { toast.error(e?.response?.data?.detail || "Save failed"); }
    finally { setBusy(false); }
  };

  if (!me) return null;
  const rows = [
    { icon: User, label: "Name", value: me.name },
    { icon: Mail, label: "Email", value: me.email },
    { icon: Shield, label: "Role", value: me.role?.replace(/_/g," ") },
    { icon: Building2, label: "Department", value: me.department?.replace(/_/g," ") || "—" },
    { icon: User, label: "Registration ID", value: me.registration_number || "—" },
  ];
  return (
    <Layout>
      <div className="max-w-xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <h1 className="font-display text-3xl font-extrabold">Profile</h1>
        <div className="rounded-2xl bg-white border border-slate-200 divide-y divide-slate-100">
          {rows.map((r) => (
            <div key={r.label} className="flex items-center gap-3 p-4">
              <r.icon className="w-5 h-5 text-slate-400" />
              <div className="flex-1">
                <div className="text-xs uppercase font-bold tracking-widest text-slate-500">{r.label}</div>
                <div className="font-semibold capitalize">{r.value}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 p-5 space-y-3">
          <div className="flex items-center gap-2"><HeartHandshake className="w-5 h-5 text-cyan-600"/><h2 className="font-display font-bold text-lg">Peer Buddy</h2></div>
          <p className="text-sm text-slate-600">Nominate a friend or family member who will be emailed automatically whenever you trigger an SOS.</p>
          <div className="space-y-2"><Label>Buddy&apos;s name</Label><Input data-testid="buddy-name" value={buddyName} onChange={(e)=>setBuddyName(e.target.value)} placeholder="e.g., Riya (roommate)"/></div>
          <div className="space-y-2"><Label>Buddy&apos;s email</Label><Input data-testid="buddy-email" type="email" value={buddyEmail} onChange={(e)=>setBuddyEmail(e.target.value)} placeholder="buddy@example.com"/></div>
          <div className="space-y-2"><Label>Buddy&apos;s phone (SMS fallback)</Label><Input data-testid="buddy-phone" type="tel" value={buddyPhone} onChange={(e)=>setBuddyPhone(e.target.value)} placeholder="+91 98765 43210"/><p className="text-[11px] text-slate-500">If email delivery fails, we&apos;ll SMS this number via Twilio.</p></div>
          <div className="space-y-2"><Label>Your phone (optional)</Label><Input data-testid="my-phone" value={phone} onChange={(e)=>setPhone(e.target.value)} placeholder="+91…"/></div>
          <Button data-testid="save-profile" onClick={save} disabled={busy} className="bg-slate-950 hover:bg-slate-800"><Save className="w-4 h-4 mr-1"/>{busy ? "Saving…" : "Save"}</Button>
        </div>
      </div>
    </Layout>
  );
}
