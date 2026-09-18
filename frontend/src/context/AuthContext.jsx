import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api, { getErrorMessage } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      try {
        const { data } = await api.get("/auth/me/");
        if (!cancelled) setUser(data);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (username, password) => {
    try {
      const { data } = await api.post("/auth/login/", { username, password });
      setUser(data.user);
      return { success: true, role: data.user.role };
    } catch (error) {
      return { success: false, message: getErrorMessage(error) };
    }
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout/");
    } finally {
      setUser(null);
    }
  };

  const value = useMemo(
    () => ({
      user,
      role: user?.role ?? null,
      isAuthenticated: !!user,
      loading,
      login,
      logout,
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
