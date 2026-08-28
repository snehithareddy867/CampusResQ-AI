// Lightweight i18n for student PWA. Persist choice in localStorage.
import { useEffect, useState } from "react";

export const LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "kn", label: "ಕನ್ನಡ" },
];

const T = {
  en: {
    hello: "Hello", protected: "You're protected on campus.",
    sos_title: "Life-threatening?", sos_hint: "Press & hold.",
    sos_desc: "Your location, identity and status are broadcast to nearby responders in real time.",
    report_link: "Report a non-SOS emergency",
    quick_report: "Report", quick_assistant: "AI Assistant", quick_notifs: "Notifications",
    active: "Active", history: "History",
    all_clear: "You're all clear. No active emergencies.",
    tell_us: "Tell us what's happening",
    describe_ph: "e.g., There is smoke coming from the electrical room in Block C.",
    location: "Location", evidence_opt: "Evidence (optional)",
    send_report: "Send Report",
    im_safe: "I'm Safe", response_complete: "Response Complete",
  },
  hi: {
    hello: "नमस्ते", protected: "आप कैंपस में सुरक्षित हैं।",
    sos_title: "जीवन-खतरनाक?", sos_hint: "दबाकर रखें।",
    sos_desc: "आपका स्थान, पहचान और स्थिति निकटवर्ती जवाबदेहों को रीयल-टाइम में भेजी जाती है।",
    report_link: "गैर-SOS आपात रिपोर्ट करें",
    quick_report: "रिपोर्ट", quick_assistant: "AI सहायक", quick_notifs: "सूचनाएँ",
    active: "सक्रिय", history: "इतिहास",
    all_clear: "सब कुछ ठीक है। कोई सक्रिय आपात नहीं।",
    tell_us: "बताएँ क्या हो रहा है",
    describe_ph: "जैसे: ब्लॉक C के इलेक्ट्रिकल रूम से धुआँ निकल रहा है।",
    location: "स्थान", evidence_opt: "प्रमाण (वैकल्पिक)",
    send_report: "रिपोर्ट भेजें",
    im_safe: "मैं सुरक्षित हूँ", response_complete: "प्रतिक्रिया पूर्ण",
  },
  ta: {
    hello: "வணக்கம்", protected: "நீங்கள் வளாகத்தில் பாதுகாப்பாக இருக்கிறீர்கள்.",
    sos_title: "உயிருக்கு ஆபத்தா?", sos_hint: "அழுத்திப் பிடிக்கவும்.",
    sos_desc: "உங்கள் இருப்பிடம், அடையாளம் மற்றும் நிலை அருகிலுள்ள மீட்பாளர்களுக்கு நேரடியாக அனுப்பப்படும்.",
    report_link: "SOS அல்லாத அவசரத்தை புகார் செய்யவும்",
    quick_report: "புகார்", quick_assistant: "AI உதவியாளர்", quick_notifs: "அறிவிப்புகள்",
    active: "செயலில்", history: "வரலாறு",
    all_clear: "எல்லாம் சரியாக உள்ளது. செயலில் அவசரங்கள் இல்லை.",
    tell_us: "என்ன நடக்கிறது என்று சொல்லுங்கள்",
    describe_ph: "எ.கா., பிளாக் C-இல் மின்சார அறையில் புகை.",
    location: "இருப்பிடம்", evidence_opt: "ஆதாரம் (விருப்பம்)",
    send_report: "புகார் அனுப்பு",
    im_safe: "நான் பாதுகாப்பாக உள்ளேன்", response_complete: "பதில் முடிந்தது",
  },
  te: {
    hello: "నమస్తే", protected: "మీరు క్యాంపస్‌లో సురక్షితంగా ఉన్నారు.",
    sos_title: "ప్రాణాంతకమా?", sos_hint: "నొక్కి పట్టుకోండి.",
    sos_desc: "మీ స్థానం, గుర్తింపు మరియు స్థితి సమీపంలోని రెస్క్యూర్‌లకు రియల్-టైమ్‌లో పంపబడతాయి.",
    report_link: "SOS కాని అత్యవసర పరిస్థితిని నివేదించండి",
    quick_report: "నివేదిక", quick_assistant: "AI సహాయకుడు", quick_notifs: "నోటిఫికేషన్లు",
    active: "ప్రస్తుత", history: "చరిత్ర",
    all_clear: "అంతా బాగుంది. ప్రస్తుత అత్యవసరాలు లేవు.",
    tell_us: "ఏం జరుగుతోందో చెప్పండి",
    describe_ph: "ఉదా., బ్లాక్ C ఎలక్ట్రికల్ రూమ్ నుండి పొగ.",
    location: "స్థానం", evidence_opt: "సాక్ష్యం (ఐచ్ఛికం)",
    send_report: "నివేదికను పంపండి",
    im_safe: "నేను సురక్షితం", response_complete: "ప్రతిస్పందన పూర్తి",
  },
  kn: {
    hello: "ನಮಸ್ಕಾರ", protected: "ನೀವು ಕ್ಯಾಂಪಸ್‌ನಲ್ಲಿ ಸುರಕ್ಷಿತರಾಗಿದ್ದೀರಿ.",
    sos_title: "ಜೀವಕ್ಕೆ ಅಪಾಯವೇ?", sos_hint: "ಒತ್ತಿ ಹಿಡಿಯಿರಿ.",
    sos_desc: "ನಿಮ್ಮ ಸ್ಥಳ, ಗುರುತು ಮತ್ತು ಸ್ಥಿತಿ ಸಮೀಪದ ಪ್ರತಿಕ್ರಿಯಾಕರ್ತರಿಗೆ ರಿಯಲ್-ಟೈಂನಲ್ಲಿ ರವಾನಿಸಲಾಗುತ್ತದೆ.",
    report_link: "SOS ಅಲ್ಲದ ತುರ್ತು ವರದಿ ಮಾಡಿ",
    quick_report: "ವರದಿ", quick_assistant: "AI ಸಹಾಯಕ", quick_notifs: "ಸೂಚನೆಗಳು",
    active: "ಸಕ್ರಿಯ", history: "ಇತಿಹಾಸ",
    all_clear: "ಎಲ್ಲಾ ಸರಿಯಿದೆ. ಯಾವುದೇ ಸಕ್ರಿಯ ತುರ್ತು ಇಲ್ಲ.",
    tell_us: "ಏನಾಗುತ್ತಿದೆ ಎಂದು ತಿಳಿಸಿ",
    describe_ph: "ಉದಾ., ಬ್ಲಾಕ್ C ಎಲೆಕ್ಟ್ರಿಕಲ್ ರೂಮ್‌ನಿಂದ ಹೊಗೆ.",
    location: "ಸ್ಥಳ", evidence_opt: "ಸಾಕ್ಷ್ಯ (ಐಚ್ಛಿಕ)",
    send_report: "ವರದಿ ಕಳುಹಿಸಿ",
    im_safe: "ನಾನು ಸುರಕ್ಷಿತ", response_complete: "ಪ್ರತಿಕ್ರಿಯೆ ಪೂರ್ಣ",
  },
};

const listeners = new Set();
export function getLang() { return localStorage.getItem("crq_lang") || "en"; }
export function setLang(code) {
  localStorage.setItem("crq_lang", code);
  listeners.forEach(fn => fn(code));
}

export function useT() {
  const [lang, setLangState] = useState(getLang());
  useEffect(() => {
    const fn = (c) => setLangState(c);
    listeners.add(fn);
    return () => listeners.delete(fn);
  }, []);
  const t = (key) => (T[lang] && T[lang][key]) || T.en[key] || key;
  return { t, lang, setLang };
}
