import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "project-1" }),
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api/projects", () => ({
  projectsApi: {
    get: vi.fn(async () => ({ id: "project-1", name: "テストプロジェクト" })),
  },
}));

vi.mock("@/lib/api/artifacts", () => ({
  artifactsApi: { upload: vi.fn() },
}));

vi.mock("@/lib/api/client", () => ({
  apiClient: { post: vi.fn() },
}));

import ReviewExecutePage from "@/app/(authed)/projects/[id]/review/page";

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ReviewExecutePage />
    </QueryClientProvider>,
  );
}

// "UI 機能概要書" / "SS 構造設計書" appear once in the Dropzone label and
// once in the readiness-check card — so when the kind is needed, the
// label count is 2; when hidden, the count is 0.
function visibleCount(label: string): number {
  return screen.queryAllByText(label).length;
}

describe("ReviewExecutePage — mode-conditional file slots", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("defaults to cross mode and shows both UI and SS dropzones", () => {
    renderPage();
    expect(visibleCount("UI 機能概要書")).toBe(2);
    expect(visibleCount("SS 構造設計書")).toBe(2);
  });

  it("hides the SS dropzone when switching to UI-only mode", async () => {
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByText("UI レビュー"));
    expect(visibleCount("UI 機能概要書")).toBe(2);
    expect(visibleCount("SS 構造設計書")).toBe(0);
  });

  it("hides the UI dropzone when switching to SS-only mode", async () => {
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByText("SS レビュー"));
    expect(visibleCount("SS 構造設計書")).toBe(2);
    expect(visibleCount("UI 機能概要書")).toBe(0);
  });

  it("readiness panel mirrors required items across all 3 modes", async () => {
    // The readiness panel must reflect exactly which artifacts are
    // required for the chosen mode. Cross = 3, single (UI/SS) = 2.
    renderPage();
    const user = userEvent.setup();

    // Default: cross mode → 0/3
    expect(screen.getByText("0/3")).toBeInTheDocument();

    // UI mode → 0/2 + SS hidden
    await user.click(screen.getByText("UI レビュー"));
    expect(screen.getByText("0/2")).toBeInTheDocument();
    expect(visibleCount("SS 構造設計書")).toBe(0);

    // SS mode → 0/2 + UI hidden
    await user.click(screen.getByText("SS レビュー"));
    expect(screen.getByText("0/2")).toBeInTheDocument();
    expect(visibleCount("UI 機能概要書")).toBe(0);

    // Back to cross → 0/3 + both visible
    await user.click(screen.getByText("UI × SS 整合性レビュー"));
    expect(screen.getByText("0/3")).toBeInTheDocument();
    expect(visibleCount("UI 機能概要書")).toBe(2);
    expect(visibleCount("SS 構造設計書")).toBe(2);
  });
});
