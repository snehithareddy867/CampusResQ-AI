import React from "react";
import { LANGS, useT } from "@/lib/i18n";
import { Globe } from "lucide-react";

export default function LanguageSwitcher({ dark = false }) {
  const { lang, setLang } = useT();
  return (
    <label data-testid="lang-switcher" className={`inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-2.5 py-1 border ${dark ? "border-slate-700 bg-slate-900 text-slate-300" : "border-slate-200 bg-white text-slate-700"}`}>
      <Globe className="w-3.5 h-3.5"/>
      <select value={lang} onChange={(e)=>setLang(e.target.value)} className="bg-transparent outline-none">
        {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
      </select>
    </label>
  );
}
