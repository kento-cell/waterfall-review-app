import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/store/auth";

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it("starts empty", () => {
    const s = useAuthStore.getState();
    expect(s.token).toBeNull();
    expect(s.user).toBeNull();
  });

  it("sets and clears token", () => {
    useAuthStore.getState().setToken("abc");
    expect(useAuthStore.getState().token).toBe("abc");
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("sets user", () => {
    useAuthStore.getState().setUser({
      id: "u1",
      email: "a@b.c",
      display_name: "Alice",
      role: "general",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
    expect(useAuthStore.getState().user?.email).toBe("a@b.c");
  });
});
