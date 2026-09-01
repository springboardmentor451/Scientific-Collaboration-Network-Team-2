/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from "react";
import { getCurrentUser, loginUser, logoutUser } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const storedUser = () => JSON.parse(localStorage.getItem("scnaUser") || sessionStorage.getItem("scnaUser") || "null");
  const hasToken = () => Boolean(localStorage.getItem("accessToken") || sessionStorage.getItem("accessToken"));
  const [user, setUser] = useState(storedUser);
  const [isLoading, setIsLoading] = useState(hasToken);

  useEffect(() => {
    if (!hasToken()) return;
    getCurrentUser().then((current) => { setUser(current); const storage = localStorage.getItem("accessToken") ? localStorage : sessionStorage; storage.setItem("scnaUser", JSON.stringify(current)); }).catch(() => setUser(null)).finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    const clearExpiredSession = () => { setUser(null); setIsLoading(false); };
    window.addEventListener("scna:unauthorized", clearExpiredSession);
    return () => window.removeEventListener("scna:unauthorized", clearExpiredSession);
  }, []);

  const login = async (email, password, remember = false) => {
    const result = await loginUser(email, password);
    const storage = remember ? localStorage : sessionStorage;
    localStorage.removeItem("accessToken"); localStorage.removeItem("scnaUser"); sessionStorage.removeItem("accessToken"); sessionStorage.removeItem("scnaUser");
    storage.setItem("accessToken", result.access_token);
    storage.setItem("scnaUser", JSON.stringify(result.user));
    if (remember) localStorage.setItem("scna_remembered_email", email.trim().toLowerCase()); else localStorage.removeItem("scna_remembered_email");
    setUser(result.user);
    return result.user;
  };

  const logout = () => {
    // The local cleanup must never be blocked by a network failure.
    logoutUser().catch(() => undefined);
    localStorage.removeItem("accessToken"); localStorage.removeItem("scnaUser"); sessionStorage.removeItem("accessToken"); sessionStorage.removeItem("scnaUser"); setUser(null);
  };
  const updateUser = (updated) => { setUser(updated); const storage = localStorage.getItem("accessToken") ? localStorage : sessionStorage; storage.setItem("scnaUser", JSON.stringify(updated)); };

  return <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
