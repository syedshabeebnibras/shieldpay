"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, TOKEN_KEY } from "@/lib/api";
import type { User, UserRole } from "@/types";

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

// Backend returns snake_case — define raw response shape
interface ApiAuthResponse {
  user: {
    id: string;
    email: string;
    full_name: string;
    role: UserRole;
    is_verified: boolean;
    stripe_account_id: string | null;
    stripe_customer_id: string | null;
    created_at: string;
  };
  access_token: string;
  token_type: string;
}

interface ApiUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_verified: boolean;
  stripe_account_id: string | null;
  stripe_customer_id: string | null;
  created_at: string;
}

function mapUser(raw: ApiUser): User {
  return {
    id: raw.id,
    email: raw.email,
    fullName: raw.full_name,
    role: raw.role,
    isVerified: raw.is_verified,
    stripeAccountId: raw.stripe_account_id,
    stripeCustomerId: raw.stripe_customer_id,
    createdAt: raw.created_at,
  };
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
      const { data } = await api.get<ApiUser>("/api/auth/me");
      setUser(mapUser(data));
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
      const { data } = await api.post<ApiAuthResponse>("/api/auth/register", {
        email: body.email,
        password: body.password,
        full_name: body.fullName,
        role: body.role,
      });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setUser(mapUser(data.user));
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
      const { data } = await api.post<ApiAuthResponse>("/api/auth/login", {
        email: body.email,
        password: body.password,
      });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setUser(mapUser(data.user));
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
