import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://shieldpay-api-production.up.railway.app";

export const TOKEN_KEY = "shieldpay_token";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (
      error.response?.status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login") &&
      !window.location.pathname.startsWith("/register")
    ) {
      localStorage.removeItem(TOKEN_KEY);
      document.cookie = "token=; path=/; max-age=0";
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
