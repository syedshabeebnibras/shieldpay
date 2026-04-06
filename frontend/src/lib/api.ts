import axios, { InternalAxiosRequestConfig } from "axios";

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

// No 401 interceptor — let calling code handle auth failures
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);
