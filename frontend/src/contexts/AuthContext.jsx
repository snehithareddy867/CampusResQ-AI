import React, { createContext, useContext, useEffect, useState } from "react";
import client from "@/lib/api";
import { registerServiceWorker, enablePush } from "@/lib/push";
import { connectWS, disconnectWS } from "@/lib/ws";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { registerServiceWorker(); }, []);

  useEffect(() => {
    const token = localStorage.getItem("crq_token");
    const cached = localStorage.getItem("crq_user");
    if (token && cached) {
      try { setUser(JSON.parse(cached)); } catch {}
    }
    if (token) {
      connectWS();
      client.get("/auth/me")
        .then((r) => { setUser(r.data); localStorage.setItem("crq_user", JSON.stringify(r.data)); })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const afterAuth = async (data) => {
    localStorage.setItem("crq_token", data.token);
    localStorage.setItem("crq_user", JSON.stringify(data.user));
    setUser(data.user);
    connectWS();
    enablePush().catch(() => {});
    return data.user;
  };

  const login = async (email, password) => {
    const r = await client.post("/auth/login", { email, password });
    return afterAuth(r.data);
  };

  const register = async (payload) => {
    const r = await client.post("/auth/register", payload);
    return afterAuth(r.data);
  };

  const logout = () => {
    localStorage.removeItem("crq_token");
    localStorage.removeItem("crq_user");
    disconnectWS();
    setUser(null);
  };

  return <AuthCtx.Provider value={{ user, loading, login, register, logout }}>{children}</AuthCtx.Provider>;
}
