import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AxiosRequestConfig } from "axios";
import * as React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "project-1", rid: "review-1" }),
}));

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => apiMocks.get(...args),
    post: (...args: unknown[]) => apiMocks.post(...args),
    put: (...args: unknown[]) => apiMocks.put(...args),
  },
}));

import ReviewResultPage from "@/app/(authed)/projects/[id]/reviews/[rid]/page";

const finding = {
  id: "finding-1",
  review_id: "review-1",
  artifact_id: "artifact-1",
  location: "UI:Sheet1!A3",
  severity: "high" as const,
  aspect_id: "aspect-1",
  aspect_name: "必須項目欠落",
  content: "指摘内容です",
  suggestion: "修正案です",
  created_at: "2026-04-28T00:00:00Z",
  response_status: "not_started" as const,
};

function review(pdfStatus: string | null = null) {
  return {
    id: "review-1",
    project_id: "project-1",
    review_type: "single",
    target_artifact_ids: ["artifact-1"],
    aspect_ids: [],
    status: "completed",
    started_at: "2026-04-28T00:00:00Z",
    completed_at: "2026-04-28T00:01:00Z",
    created_at: "2026-04-28T00:00:00Z",
    created_by: "user-1",
    error_message: null,
    pdf_status: pdfStatus,
    pdf_path: null,
    pdf_generated_at: null,
  };
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <ReviewResultPage />
    </QueryClientProvider>,
  );
}

function mockGet(pdfStatus: string | null = null) {
  apiMocks.get.mockImplementation((url: string, config?: AxiosRequestConfig) => {
    if (url.endsWith("/findings")) return Promise.resolve({ data: [finding] });
    if (url.endsWith("/pdf_status")) {
      return Promise.resolve({
        data: {
          review_id: "review-1",
          status: "completed",
          pdf_path: "storage/pdfs/review-1.pdf",
          pdf_generated_at: "2026-04-28T00:02:00Z",
          error_message: null,
        },
      });
    }
    if (url.endsWith("/pdf")) {
      expect(config?.responseType).toBe("blob");
      return Promise.resolve({ data: new Blob(["pdf"], { type: "application/pdf" }) });
    }
    return Promise.resolve({ data: review(pdfStatus) });
  });
}

describe("ReviewResultPage", () => {
  beforeEach(() => {
    apiMocks.get.mockReset();
    apiMocks.post.mockReset();
    apiMocks.put.mockReset();
    apiMocks.post.mockResolvedValue({
      data: {
        review_id: "review-1",
        status: "running",
        pdf_path: null,
        pdf_generated_at: null,
        error_message: null,
      },
    });
    apiMocks.put.mockResolvedValue({ data: {} });
    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: vi.fn(() => "blob:review-pdf"),
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: vi.fn(),
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  });

  it("shows the generate-and-download button for completed reviews without a PDF", async () => {
    mockGet(null);

    renderPage();

    const button = await screen.findByRole("button", { name: "生成して DL" });
    await waitFor(() => expect(button).toBeEnabled());
    expect(await screen.findByText("指摘内容です")).toBeInTheDocument();
  });

  it("requests generation, polls status, and downloads the completed PDF", async () => {
    mockGet(null);

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "生成して DL" }));

    await waitFor(() => expect(apiMocks.post).toHaveBeenCalledWith("/api/reviews/review-1/generate_pdf"));
    await waitFor(() => expect(apiMocks.get).toHaveBeenCalledWith("/api/reviews/review-1/pdf_status"));
    await waitFor(() =>
      expect(apiMocks.get).toHaveBeenCalledWith("/api/reviews/review-1/pdf", { responseType: "blob" }),
    );
  });

  it("downloads directly when the PDF is already completed", async () => {
    mockGet("completed");

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "⬇ DL" }));

    expect(apiMocks.post).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(apiMocks.get).toHaveBeenCalledWith("/api/reviews/review-1/pdf", { responseType: "blob" }),
    );
  });

  it("shows the running label when PDF generation is already running", async () => {
    mockGet("running");

    renderPage();

    expect(await screen.findByRole("button", { name: "生成中..." })).toBeDisabled();
  });

  it("opens finding detail and updates the response status", async () => {
    mockGet(null);

    renderPage();
    await userEvent.click(await screen.findByText("指摘内容です"));
    await userEvent.selectOptions(await screen.findByLabelText("対応状況更新"), "done");
    await userEvent.type(screen.getByLabelText("対応コメント"), "修正しました");
    await userEvent.click(screen.getByRole("button", { name: "更新" }));

    await waitFor(() =>
      expect(apiMocks.put).toHaveBeenCalledWith("/api/findings/finding-1/response", {
        status: "done",
        comment: "修正しました",
      }),
    );
  });

  it("shows an error when PDF generation fails", async () => {
    mockGet(null);
    apiMocks.get.mockImplementation((url: string, config?: AxiosRequestConfig) => {
      if (url.endsWith("/findings")) return Promise.resolve({ data: [finding] });
      if (url.endsWith("/pdf_status")) {
        return Promise.resolve({
          data: {
            review_id: "review-1",
            status: "failed",
            pdf_path: null,
            pdf_generated_at: null,
            error_message: "PDF conversion failed",
          },
        });
      }
      if (url.endsWith("/pdf")) {
        expect(config?.responseType).toBe("blob");
        return Promise.resolve({ data: new Blob(["pdf"], { type: "application/pdf" }) });
      }
      return Promise.resolve({ data: review(null) });
    });

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "生成して DL" }));

    expect(await screen.findByText("PDF conversion failed")).toBeInTheDocument();
  });
});
