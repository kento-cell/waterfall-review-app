import axios, { AxiosError, type AxiosInstance } from "axios";
import { useAuthStore } from "@/store/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_URL,
    headers: { "Content-Type": "application/json" },
    timeout: 60_000,
  });

  instance.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        useAuthStore.getState().logout();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    },
  );

  return instance;
}

export const apiClient = createApiClient();
export { API_URL };
