"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { artifactsApi } from "@/lib/api/artifacts";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
  const modeMeta = MODES.find((m) => m.value === mode) ?? MODES[0];

  // Drop hidden-side selections on mode switch so the user can't
  // accidentally upload a stale file that's no longer required. Earlier
  // versions kept stale files invisible-but-set, which uploaded under
  // the wrong artifact category at submit time.
  //
  // Defense-in-depth: submitMutation also gates uploads with
  // `needUi/needSs` (see lines below). This effect just keeps the UI
  // state consistent with the visible slots — it's not the only guard.
  //
  // Why deps are only [mode]: the snapshot semantics here are "when
  // the user switches mode, clear once". Including uiFile/ssFile would
  // re-fire the effect every time the user picks a file (no-op when
  // need* is true, but noisy and confusing).
  React.useEffect(() => {
    if (!needUi && uiFile) setUiFile(null);
    if (!needSs && ssFile) setSsFile(null);
    setSubmitError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

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

  const requiredChecks = [
    { label: "観点ファイル", ready: !!aspectFile, detail: aspectFile?.name ?? "未選択" },
    ...(needUi ? [{ label: "UI 機能概要書", ready: !!uiFile, detail: uiFile?.name ?? "未選択" }] : []),
    ...(needSs ? [{ label: "SS 構造設計書", ready: !!ssFile, detail: ssFile?.name ?? "未選択" }] : []),
  ];
  const readyCount = requiredChecks.filter((item) => item.ready).length;
  const missingItems = requiredChecks.filter((item) => !item.ready).map((item) => item.label);
  const canSubmit = missingItems.length === 0 && !submitMutation.isPending;
  const submitButtonLabel = submitMutation.isPending
    ? "アップロードとレビュー起動中..."
    : canSubmit
      ? "▶ AI レビュー実行"
      : "必須ファイルを選択してください";

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

      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-white shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm text-slate-300">現在のレビュー種別</p>
            <p className="mt-1 text-xl font-semibold">{modeMeta.label}</p>
            <p className="mt-1 text-sm text-slate-300">{modeMeta.desc}</p>
          </div>
          <div className="min-w-[220px]" aria-live="polite">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <span>準備状況</span>
              <span>
                {readyCount}/{requiredChecks.length}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/15">
              <div
                className="h-full rounded-full bg-emerald-400 transition-all"
                style={{ width: `${(readyCount / requiredChecks.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">① 工程選択</CardTitle>
          <CardDescription>レビュー目的に合わせて、必要な投入資料が自動で切り替わります。</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3 md:flex-row">
            {MODES.map((m) => (
              <label
                key={m.value}
                className={`relative flex flex-1 cursor-pointer flex-col gap-2 rounded-xl border-2 p-4 transition-all ${
                  mode === m.value ? "border-slate-900 bg-slate-50 shadow-sm" : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value={m.value}
                  checked={mode === m.value}
                  onChange={() => {
                    setMode(m.value);
                    setSubmitError(null);
                  }}
                  className="sr-only"
                />
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${
                      mode === m.value ? "border-slate-900" : "border-gray-400"
                    }`}
                  >
                    {mode === m.value && <span className="h-2 w-2 rounded-full bg-slate-900" />}
                  </span>
                  <span className="font-semibold">{m.label}</span>
                </div>
                <span className="text-xs text-gray-500">{m.desc}</span>
                <span className="text-xs text-gray-400">
                  必須: {m.value === "ui" && "観点 / UI"}
                  {m.value === "ss" && "観点 / SS"}
                  {m.value === "cross" && "観点 / UI / SS"}
                </span>
                {mode === m.value && (
                  <span className="absolute right-3 top-3 rounded-full bg-slate-900 px-2 py-0.5 text-xs text-white">
                    選択中
                  </span>
                )}
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">② 観点ファイル (PM 提供)</CardTitle>
          <CardDescription>AI が何を重視して見るかを決める入力です。まずここを選択してください。</CardDescription>
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
          <CardDescription>
            {mode === "ui" && "UI レビュー: 機能概要書 1 ファイルだけ投入"}
            {mode === "ss" && "SS レビュー: 構造設計書 1 ファイルだけ投入"}
            {mode === "cross" && "UI × SS 整合性レビュー: 機能概要書 + 構造設計書 の両方を投入"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`grid gap-4 ${
              mode === "cross" ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"
            }`}
          >
            {needUi && (
              <Dropzone
                label="UI 機能概要書"
                description="顧客向け、Excel 中心 (.xlsx / .docx / .pdf)"
                accept={DOC_ACCEPT}
                file={uiFile}
                onFileChange={setUiFile}
                variant="amber"
                required
                badge={{ text: "UI", color: "#ED6C02" }}
              />
            )}
            {needSs && (
              <Dropzone
                label="SS 構造設計書"
                description="PG/PT 向け、擬似コード+チェック仕様 (.xlsx / .docx / .pdf)"
                accept={DOC_ACCEPT}
                file={ssFile}
                onFileChange={setSsFile}
                variant="navy"
                required
                badge={{ text: "SS", color: "#1B3A6B" }}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {submitError && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{submitError}</div>
      )}

      <Card className="border-slate-200 bg-slate-50">
        <CardHeader>
          <CardTitle className="text-lg">実行前チェック</CardTitle>
          <CardDescription>不足している項目がなくなると実行できます。</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3">
            {requiredChecks.map((item) => (
              <div
                key={item.label}
                className={`rounded-lg border bg-white p-3 ${
                  item.ready ? "border-emerald-200" : "border-amber-200"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{item.label}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      item.ready ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {item.ready ? "OK" : "未選択"}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground">{item.detail}</p>
              </div>
            ))}
          </div>
          {missingItems.length > 0 && (
            <p className="mt-3 text-sm text-amber-700">不足: {missingItems.join("、")}</p>
          )}
          {submitMutation.isPending && (
            <p className="mt-3 text-sm text-slate-600">
              ファイルをアップロードしてレビューを開始しています。画面を閉じずにお待ちください。
            </p>
          )}
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Link href={`/projects/${projectId}`}>
          <Button type="button" variant="outline">
            キャンセル
          </Button>
        </Link>
        <Button type="submit" disabled={!canSubmit}>
          {submitButtonLabel}
        </Button>
      </form>
    </div>
  );
}
