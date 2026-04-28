import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types/api";

interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: "ai-review-auth",
      storage: createJSONStorage(() => (typeof window !== "undefined" ? localStorage : (undefined as unknown as Storage))),
      partialize: (state) => ({ token: state.token, user: state.user }),
    },
  ),
);
