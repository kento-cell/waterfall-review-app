"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { artifactsApi } from "@/lib/api/artifacts";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";

type ReviewMode = "ui" | "ss" | "cross";

const MODES: { value: ReviewMode; label: string; desc: string }[] = [
  { value: "ui", label: "UI レビュー", desc: "機能概要書を顧客視点でレビュー" },
  { value: "ss", label: "SS レビュー", desc: "構造設計書を PG/PT 視点でレビュー" },
  { value: "cross", label: "UI × SS 整合性レビュー", desc: "UI と SS の対応関係を AI が突合" },
];

const ASPECT_ACCEPT = ".xlsx,.txt";
const DOC_ACCEPT = ".xlsx,.docx,.pdf";

export default function ReviewExecutePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const qc = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
  });

  const [mode, setMode] = React.useState<ReviewMode>("cross");
  const [aspectFile, setAspectFile] = React.useState<File | null>(null);
  const [uiFile, setUiFile] = React.useState<File | null>(null);
  const [ssFile, setSsFile] = React.useState<File | null>(null);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  const needUi = mode === "ui" || mode === "cross";
  const needSs = mode === "ss" || mode === "cross";

  const submitMutation = useMutation({
    mutationFn: async () => {
      // 1) Upload aspect file as artifact (phase: 観点)
      if (!aspectFile) throw new Error("観点ファイルが未指定");
      const aspectArtifact = await artifactsApi.upload(projectId, "観点", aspectFile);

      // 2) Upload UI / SS as artifacts
      const targetIds: string[] = [];
      if (needUi) {
        if (!uiFile) throw new Error("UI ファイルが未指定");
        const uiArt = await artifactsApi.upload(projectId, "UI", uiFile);
        targetIds.push(uiArt.id);
      }
      if (needSs) {
        if (!ssFile) throw new Error("SS ファイルが未指定");
        const ssArt = await artifactsApi.upload(projectId, "SS", ssFile);
        targetIds.push(ssArt.id);
      }

      // 3) Trigger review (Phase 4 で aspect parsing が backend に入るまでは
      //    Stub 観点で動作。aspect file の内容は artifact として保存済)
      const { data } = await apiClient.post(`/api/projects/${projectId}/reviews`, {
        artifact_id: targetIds[0],
        aspect_ids: [],
        review_type: mode === "cross" ? "cross" : "single",
        target_artifact_ids: targetIds,
        aspect_artifact_id: aspectArtifact.id,
      });
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      router.push(`/projects/${projectId}/reviews/${data.review_id ?? data.id}`);
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ??
        (err as Error).message ??
        "レビュー実行に失敗しました";
      setSubmitError(typeof msg === "string" ? msg : "レビュー実行に失敗しました");
    },
  });

  const canSubmit =
    !!aspectFile &&
    (!needUi || !!uiFile) &&
    (!needSs || !!ssFile) &&
    !submitMutation.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    submitMutation.mutate();
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-sm text-muted-foreground hover:underline">
          ← {projectQuery.data?.name ?? "プロジェクト詳細"}
        </Link>
      </div>

      <h1 className="text-2xl font-semibold">AI レビュー実行</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">① 工程選択</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3 md:flex-row">
            {MODES.map((m) => (
              <label
                key={m.value}
                className={`flex flex-1 cursor-pointer flex-col gap-1 rounded-lg border-2 p-4 transition-colors ${
                  mode === m.value ? "border-blue-700 bg-blue-50" : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value={m.value}
                  checked={mode === m.value}
                  onChange={() => setMode(m.value)}
                  className="sr-only"
                />
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${
                      mode === m.value ? "border-blue-700" : "border-gray-400"
                    }`}
                  >
                    {mode === m.value && <span className="h-2 w-2 rounded-full bg-blue-700" />}
                  </span>
                  <span className="font-semibold">{m.label}</span>
                </div>
                <span className="text-xs text-gray-500">{m.desc}</span>
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">② 観点ファイル (PM 提供)</CardTitle>
        </CardHeader>
        <CardContent>
          <Dropzone
            label="観点ファイル"
            description="Excel (.xlsx) または テキスト (.txt) — 観点名 / 対象 / 重要度 / 工程 / 指示文 を含む"
            accept={ASPECT_ACCEPT}
            file={aspectFile}
            onFileChange={setAspectFile}
            variant="amber"
            required
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">③ レビュー対象資料</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Dropzone
              label="UI 機能概要書"
              description="顧客向け、Excel 中心 (.xlsx / .docx / .pdf)"
              accept={DOC_ACCEPT}
              file={uiFile}
              onFileChange={setUiFile}
              variant={needUi ? "amber" : "default"}
              required={needUi}
              badge={{ text: "UI", color: "#ED6C02" }}
            />
            <Dropzone
              label="SS 構造設計書"
              description="PG/PT 向け、擬似コード+チェック仕様 (.xlsx / .docx / .pdf)"
              accept={DOC_ACCEPT}
              file={ssFile}
              onFileChange={setSsFile}
              variant={needSs ? "navy" : "default"}
              required={needSs}
              badge={{ text: "SS", color: "#1B3A6B" }}
            />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {mode === "ui" && "UI レビュー: SS は不要 (グレー表示)"}
            {mode === "ss" && "SS レビュー: UI は不要 (グレー表示、整合性参考のため任意で添付可)"}
            {mode === "cross" && "UI × SS 整合性レビュー: 両方 必須"}
          </p>
        </CardContent>
      </Card>

      {submitError && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{submitError}</div>
      )}

      <form onSubmit={handleSubmit} className="flex justify-end gap-2">
        <Link href={`/projects/${projectId}`}>
          <Button type="button" variant="outline">
            キャンセル
          </Button>
        </Link>
        <Button type="submit" disabled={!canSubmit}>
          {submitMutation.isPending ? "実行中..." : "▶ AI レビュー実行"}
        </Button>
      </form>
    </div>
  );
}
