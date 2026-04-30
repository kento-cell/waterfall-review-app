import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock next/navigation
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

// Mock auth API
const loginMock = vi.fn();
const meMock = vi.fn();
vi.mock("@/lib/api/auth", () => ({
  authApi: {
    login: (...args: unknown[]) => loginMock(...args),
    me: (...args: unknown[]) => meMock(...args),
    logout: vi.fn(),
  },
}));

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    pushMock.mockReset();
    loginMock.mockReset();
    meMock.mockReset();
  });

  it("submits credentials and navigates on success", async () => {
    loginMock.mockResolvedValue({ access_token: "tok", token_type: "bearer" });
    meMock.mockResolvedValue({
      id: "u1",
      email: "u@example.com",
      display_name: "User",
      role: "general",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("メールアドレス"), "u@example.com");
    await userEvent.type(screen.getByLabelText("パスワード"), "pw12345678");
    await userEvent.click(screen.getByRole("button", { name: "ログイン" }));

    await vi.waitFor(() => expect(loginMock).toHaveBeenCalledWith({ email: "u@example.com", password: "pw12345678" }));
    await vi.waitFor(() => expect(pushMock).toHaveBeenCalledWith("/projects"));
  });

  it("shows validation error on empty submit", async () => {
    render(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: "ログイン" }));
    expect(await screen.findByText(/メールアドレスの形式が不正です/)).toBeInTheDocument();
  });

  it("fills demo credentials", async () => {
    render(<LoginPage />);

    await userEvent.click(screen.getByRole("button", { name: "入力する" }));

    expect(screen.getByLabelText("メールアドレス")).toHaveValue("demo@example.com");
    expect(screen.getByLabelText("パスワード")).toHaveValue("password123");
  });
});
