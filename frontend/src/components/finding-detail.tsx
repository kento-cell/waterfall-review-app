"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import type { Finding } from "@/types/api";

type ResponseStatus = Finding["response_status"];

const severityLabel: Record<Finding["severity"], string> = {
  high: "高",
  mid: "中",
  low: "低",
};

const responseStatusLabels: Record<ResponseStatus, string> = {
  not_started: "未着手",
  in_progress: "対応中",
  done: "完了",
  not_applicable: "対応不要",
};

interface FindingDetailDialogProps {
  finding: Finding | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated?: () => void;
}

export function FindingDetailDialog({
  finding,
  open,
  onOpenChange,
  onUpdated,
}: FindingDetailDialogProps) {
  const [status, setStatus] = React.useState<ResponseStatus>("not_started");
  const [comment, setComment] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (finding) {
      setStatus(finding.response_status);
      setComment("");
      setError(null);
    }
  }, [finding]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!finding) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.put(`/api/findings/${finding.id}/response`, {
        status,
        comment: comment.trim() || null,
      });
      onUpdated?.();
      onOpenChange(false);
    } catch {
      setError("対応状況の更新に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>指摘詳細</DialogTitle>
        </DialogHeader>
        {finding && (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <dl className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">重要度</dt>
                <dd className="font-semibold">{severityLabel[finding.severity]}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">観点</dt>
                <dd className="font-semibold">{finding.aspect_name ?? finding.aspect_id ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">位置</dt>
                <dd>{finding.location ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">対応状況</dt>
                <dd>{responseStatusLabels[finding.response_status]}</dd>
              </div>
              <div className="md:col-span-2">
                <dt className="text-muted-foreground">指摘内容</dt>
                <dd className="whitespace-pre-wrap">{finding.content}</dd>
              </div>
              <div className="md:col-span-2">
                <dt className="text-muted-foreground">修正案</dt>
                <dd className="whitespace-pre-wrap">{finding.suggestion ?? "-"}</dd>
              </div>
            </dl>

            <div className="grid gap-2">
              <Label htmlFor="finding-response-status">対応状況更新</Label>
              <select
                id="finding-response-status"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={status}
                onChange={(event) => setStatus(event.target.value as ResponseStatus)}
              >
                {Object.entries(responseStatusLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="finding-response-comment">対応コメント</Label>
              <textarea
                id="finding-response-comment"
                className="min-h-24 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
              />
            </div>

            {error && <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                閉じる
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? "更新中..." : "更新"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
