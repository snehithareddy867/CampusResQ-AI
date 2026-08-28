import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const client = axios.create({ baseURL: API });

client.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("crq_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      // token expired
      localStorage.removeItem("crq_token");
    }
    return Promise.reject(err);
  }
);

export default client;

// Offline sync queue in localStorage
const QUEUE_KEY = "crq_sync_queue";

export function enqueueOfflineOp(op) {
  const q = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
  q.push({ ...op, queued_at: new Date().toISOString() });
  localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  return q.length;
}

export function getQueue() {
  return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
}

export function clearQueue() {
  localStorage.setItem(QUEUE_KEY, "[]");
}

export async function flushQueue() {
  const q = getQueue();
  if (!q.length) return { synced: 0 };
  try {
    const res = await client.post("/sync/queue", { operations: q });
    clearQueue();
    return { synced: q.length, results: res.data.results };
  } catch (e) {
    return { synced: 0, error: e.message };
  }
}
