"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import type { LoginResponse, Role, UserContext } from "@/lib/types";

const TOKEN_KEY = "apaar_sdmv_token";

interface AuthContextValue {
  user: UserContext | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<UserContext>;
  logout: () => void;
  refreshUser: () => Promise<UserContext | null>;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage can be unavailable in hardened/private browser modes. The
    // in-memory session still works for the current page.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserContext | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const stored = readStoredToken();
    if (!stored) {
      // Restoring from localStorage is an external-system read. The effect must
      // settle the initial loading state, which is exactly the synchronous
      // handoff this rule otherwise warns about.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoading(false);
      return () => {
        active = false;
      };
    }

    setToken(stored);
    api
      .get<UserContext>("/auth/me", stored)
      .then((current) => {
        if (active) setUser(current);
      })
      .catch(() => {
        if (!active) return;
        storeToken(null);
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.post<LoginResponse>("/auth/login", {
      email,
      password,
    });
    storeToken(response.accessToken);
    setToken(response.accessToken);
    setUser(response.user);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    storeToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return null;
    const current = await api.get<UserContext>("/auth/me", token);
    setUser(current);
    return current;
  }, [token]);

  const hasRole = useCallback(
    (...roles: Role[]) => Boolean(user && roles.some((role) => user.roles.includes(role))),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
      refreshUser,
      hasRole,
    }),
    [user, token, isLoading, login, logout, refreshUser, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
