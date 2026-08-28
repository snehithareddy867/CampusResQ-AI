// Lightweight WebSocket client with auto-reconnect + pub/sub.
let ws = null;
let reconnectTimer = null;
let closedByUser = false;
const listeners = new Set();

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";
const WS_URL_BASE = BACKEND.replace(/^http/, "ws");

export function subscribeWS(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function scheduleReconnect() {
  if (reconnectTimer || closedByUser) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWS();
  }, 3000);
}

export function connectWS() {
  closedByUser = false;
  const token = localStorage.getItem("crq_token");
  if (!token) return;
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
  try {
    ws = new WebSocket(`${WS_URL_BASE}/api/ws?token=${encodeURIComponent(token)}`);
    ws.onopen = () => { /* connected */ };
    ws.onmessage = (e) => {
      let data;
      try { data = JSON.parse(e.data); } catch { return; }
      listeners.forEach(fn => { try { fn(data); } catch {} });
    };
    ws.onerror = () => {};
    ws.onclose = () => { ws = null; scheduleReconnect(); };
  } catch {
    scheduleReconnect();
  }
}

export function disconnectWS() {
  closedByUser = true;
  if (ws) { try { ws.close(); } catch {} ws = null; }
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
}
