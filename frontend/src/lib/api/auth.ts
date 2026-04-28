import { apiClient } from "./client";
import type { LoginRequest, LoginResponse, User } from "@/types/api";

export const authApi = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>("/api/auth/login", payload);
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/api/auth/logout");
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>("/api/auth/me");
    return data;
  },
};
