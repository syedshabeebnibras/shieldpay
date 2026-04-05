"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, TOKEN_KEY } from "@/lib/api";
import type { AuthResponse, User, UserRole } from "@/types";

interface RegisterData {
  email: string;
  password: string;
  fullName: string;
  role: UserRole;
}

interface LoginData {
  email: string;
  password: string;
}

export function useAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = user !== null;

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const { data } = await api.get<User>("/api/auth/me");
      setUser(data);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const register = async (body: RegisterData) => {
    setError(null);
    try {
      const { data } = await api.post<AuthResponse>("/api/auth/register", {
        email: body.email,
        password: body.password,
        full_name: body.fullName,
        role: body.role,
      });
      localStorage.setItem(TOKEN_KEY, data.accessToken);
      setUser(data.user);
      return data;
    } catch (err: unknown) {
      const message = extractError(err);
      setError(message);
      throw new Error(message);
    }
  };

  const login = async (body: LoginData) => {
    setError(null);
    try {
      const { data } = await api.post<AuthResponse>("/api/auth/login", {
        email: body.email,
        password: body.password,
      });
      localStorage.setItem(TOKEN_KEY, data.accessToken);
      setUser(data.user);
      return data;
    } catch (err: unknown) {
      const message = extractError(err);
      setError(message);
      throw new Error(message);
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    router.push("/login");
  }, [router]);

  return {
    user,
    isLoading,
    isAuthenticated,
    error,
    register,
    login,
    logout,
    fetchUser,
  };
}

function extractError(err: unknown): string {
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as Record<string, unknown>).response === "object"
  ) {
    const resp = (err as { response: { data?: { detail?: string } } }).response;
    if (resp.data?.detail) return resp.data.detail;
  }
  return "An unexpected error occurred";
}
