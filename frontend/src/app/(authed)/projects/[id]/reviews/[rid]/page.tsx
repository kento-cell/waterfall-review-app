"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FindingDetailDialog } from "@/components/finding-detail";
import { formatDateTime } from "@/lib/utils";
import type { Finding, PdfStatus, PdfStatusResponse, Review } from "@/types/api";

const severityLabel: Record<Finding["severity"], { label: string; color: string }> = {
  high: { label: "🔴 高", color: "text-red-700" },
  mid: { label: "🟡 中", color: "text-amber-700" },
  low: { label: "🟢 低", color: "text-green-700" },
};

const PDF_POLL_INTERVAL_MS = 1000;

function pdfButtonLabel(status: PdfStatus, generating: boolean): string {
  if (generating || status === "running") return "生成中...";
  if (status === "completed") return "⬇ DL";
  return "生成して DL";
}

export default function ReviewResultPage() {
  const params = useParams<{ id: string; rid: string }>();
  const projectId = params.id;
  const reviewId = params.rid;

  // ポーリング付きでレビュー status を取得 (running なら自動更新)
  const reviewQuery = useQuery({
    queryKey: ["review", reviewId],
    queryFn: async () => {
      const { data } = await apiClient.get<Review>(`/api/reviews/${reviewId}`);
      return data;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 3000;
    },
  });

  const review = reviewQuery.data;
  const isCompleted = review?.status === "completed";
  const [pdfStatus, setPdfStatus] = React.useState<PdfStatus>("pending");
  const [pdfGenerating, setPdfGenerating] = React.useState(false);
  const [pdfError, setPdfError] = React.useState<string | null>(null);
  const [selectedFinding, setSelectedFinding] = React.useState<Finding | null>(null);

  React.useEffect(() => {
    if (review?.pdf_status) {
      setPdfStatus(review.pdf_status);
    }
  }, [review?.pdf_status]);

  const findingsQuery = useQuery({
    queryKey: ["findings", reviewId],
    queryFn: async () => {
      const { data } = await apiClient.get<Finding[]>(`/api/reviews/${reviewId}/findings`);
      return data;
    },
    enabled: isCompleted,
  });

  const findings = findingsQuery.data ?? [];
  const counts = {
    high: findings.filter((f) => f.severity === "high").length,
    mid: findings.filter((f) => f.severity === "mid").length,
    low: findings.filter((f) => f.severity === "low").length,
  };

  const downloadPdf = React.useCallback(async () => {
    const { data } = await apiClient.get<Blob>(`/api/reviews/${reviewId}/pdf`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `review-${reviewId}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }, [reviewId]);

  const waitForPdfCompletion = React.useCallback(async () => {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const { data } = await apiClient.get<PdfStatusResponse>(`/api/reviews/${reviewId}/pdf_status`);
      setPdfStatus(data.status);
      if (data.status === "completed") return;
      if (data.status === "failed") {
        throw new Error(data.error_message ?? "PDF 生成に失敗しました");
      }
      await new Promise((resolve) => window.setTimeout(resolve, PDF_POLL_INTERVAL_MS));
    }
    throw new Error("PDF 生成がタイムアウトしました");
  }, [reviewId]);

  const handlePdfDownload = async () => {
    if (!isCompleted || pdfGenerating) return;
    setPdfGenerating(true);
    setPdfError(null);
    try {
      if (pdfStatus !== "completed") {
        const { data } = await apiClient.post<PdfStatusResponse>(`/api/reviews/${reviewId}/generate_pdf`);
        setPdfStatus(data.status);
        if (data.status !== "completed") {
          await waitForPdfCompletion();
        }
      }
      await downloadPdf();
      setPdfStatus("completed");
    } catch (error) {
      const message = error instanceof Error ? error.message : "PDF ダウンロードに失敗しました";
      setPdfError(message);
    } finally {
      setPdfGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-sm text-muted-foreground hover:underline">
          ← プロジェクト詳細
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">レビュー結果</h1>
          <p className="mt-1 text-sm text-muted-foreground">ID: {reviewId}</p>
        </div>
        <Button
          variant="outline"
          disabled={!isCompleted || pdfGenerating || pdfStatus === "running"}
          onClick={handlePdfDownload}
        >
          {pdfButtonLabel(pdfStatus, pdfGenerating)}
        </Button>
      </div>
      {pdfError && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{pdfError}</div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">ステータス</CardTitle>
        </CardHeader>
        <CardContent>
          {!review && <p className="text-sm text-muted-foreground">読み込み中...</p>}
          {review && (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm md:grid-cols-4">
              <div>
                <dt className="text-muted-foreground">状態</dt>
                <dd className="font-semibold">
                  {review.status === "pending" && "⏳ 待機中"}
                  {review.status === "running" && "🔄 実行中"}
                  {review.status === "completed" && "✅ 完了"}
                  {review.status === "failed" && "❌ 失敗"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">種別</dt>
                <dd className="font-semibold">{review.review_type}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">開始</dt>
                <dd>{formatDateTime(review.started_at)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">完了</dt>
                <dd>{formatDateTime(review.completed_at)}</dd>
              </div>
            </dl>
          )}
          {review?.status === "failed" && review.error_message && (
            <div className="mt-3 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
              {review.error_message}
            </div>
          )}
        </CardContent>
      </Card>

      {isCompleted && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              指摘一覧 ({findings.length} 件 — 高 {counts.high} / 中 {counts.mid} / 低 {counts.low})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {findings.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                指摘なし。観点ファイルが空、または Stub LLM での簡易動作のため。Phase 4 で本格対応。
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead className="w-20">重要度</TableHead>
                    <TableHead className="w-40">位置</TableHead>
                    <TableHead className="w-40">観点</TableHead>
                    <TableHead>指摘内容</TableHead>
                    <TableHead>修正案</TableHead>
                    <TableHead className="w-24">対応</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {findings.map((f, i) => (
                    <TableRow
                      key={f.id}
                      className="cursor-pointer"
                      tabIndex={0}
                      onClick={() => setSelectedFinding(f)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") setSelectedFinding(f);
                      }}
                    >
                      <TableCell>{i + 1}</TableCell>
                      <TableCell className={severityLabel[f.severity].color}>
                        {severityLabel[f.severity].label}
                      </TableCell>
                      <TableCell className="text-xs">{f.location ?? "-"}</TableCell>
                      <TableCell className="text-xs">{f.aspect_name ?? f.aspect_id ?? "-"}</TableCell>
                      <TableCell className="text-sm">{f.content}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{f.suggestion ?? "-"}</TableCell>
                      <TableCell className="text-xs">{f.response_status}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      <FindingDetailDialog
        finding={selectedFinding}
        open={selectedFinding !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedFinding(null);
        }}
        onUpdated={() => findingsQuery.refetch()}
      />
    </div>
  );
}
