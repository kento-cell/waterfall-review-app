"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { artifactsApi } from "@/lib/api/artifacts";
import { ALL_PHASES } from "@/types/api";
import type { Phase } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatBytes } from "@/lib/utils";

const ALLOWED_EXT = [".xlsx", ".docx", ".pdf", ".vb", ".cs", ".java", ".py", ".js", ".ts"];
const MAX_SIZE = 50 * 1024 * 1024;

export default function UploadPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const qc = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
  });

  const [phase, setPhase] = React.useState<Phase>("基本設計");
  const [file, setFile] = React.useState<File | null>(null);
  const [progress, setProgress] = React.useState<number>(0);
  const [error, setError] = React.useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: () => artifactsApi.upload(projectId, phase, file!, setProgress),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["artifacts", projectId] });
      router.push(`/projects/${projectId}`);
    },
    onError: () => setError("アップロードに失敗しました"),
  });

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const f = e.target.files?.[0] ?? null;
    if (!f) {
      setFile(null);
      return;
    }
    const ext = "." + (f.name.split(".").pop()?.toLowerCase() ?? "");
    if (!ALLOWED_EXT.includes(ext)) {
      setError(`許可されていない拡張子です。許可: ${ALLOWED_EXT.join(", ")}`);
      setFile(null);
      return;
    }
    if (f.size > MAX_SIZE) {
      setError(`50MB を超えています (現: ${formatBytes(f.size)})`);
      setFile(null);
      return;
    }
    setFile(f);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setProgress(0);
    if (!file) {
      setError("ファイルを選択してください");
      return;
    }
    uploadMutation.mutate();
  };

  const project = projectQuery.data;
  const availablePhases = (project?.phases as Phase[] | null | undefined) ?? ALL_PHASES;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-sm text-muted-foreground hover:underline">
          ← {project?.name ?? "プロジェクト詳細"}
        </Link>
      </div>

      <h1 className="text-2xl font-semibold">成果物アップロード</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">アップロード</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="phase">工程</Label>
              <select
                id="phase"
                value={phase}
                onChange={(e) => setPhase(e.target.value as Phase)}
                className="flex h-10 w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {availablePhases.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="file">ファイル ({ALLOWED_EXT.join(", ")} / 最大 50MB)</Label>
              <Input id="file" type="file" accept={ALLOWED_EXT.join(",")} onChange={onFileChange} />
              {file && (
                <span className="text-sm text-muted-foreground">
                  選択: {file.name} ({formatBytes(file.size)})
                </span>
              )}
            </div>

            {progress > 0 && progress < 100 && (
              <div className="flex items-center gap-3">
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
                </div>
                <span className="text-xs">{progress}%</span>
              </div>
            )}

            {error && <span className="text-sm text-destructive">{error}</span>}

            <div className="flex gap-2">
              <Button type="submit" disabled={!file || uploadMutation.isPending}>
                {uploadMutation.isPending ? "アップロード中..." : "アップロード"}
              </Button>
              <Link href={`/projects/${projectId}`}>
                <Button type="button" variant="outline">
                  キャンセル
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
