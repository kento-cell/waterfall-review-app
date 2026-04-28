"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import { artifactsApi } from "@/lib/api/artifacts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatBytes, formatDateTime } from "@/lib/utils";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const qc = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
  });

  const artifactsQuery = useQuery({
    queryKey: ["artifacts", projectId],
    queryFn: () => artifactsApi.list(projectId),
    enabled: !!projectId,
  });

  const removeMutation = useMutation({
    mutationFn: artifactsApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["artifacts", projectId] }),
  });

  const project = projectQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href="/projects" className="text-sm text-muted-foreground hover:underline">
          ← プロジェクト一覧
        </Link>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{project?.name ?? "-"}</h1>
          {project?.description && <p className="mt-1 text-sm text-muted-foreground">{project.description}</p>}
        </div>
        <div className="flex gap-2">
          <Link href={`/projects/${projectId}/artifacts/upload`}>
            <Button variant="outline">+ 成果物アップロード</Button>
          </Link>
          <Link href={`/projects/${projectId}/review`}>
            <Button>▶ AI レビュー実行</Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">対象工程</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {(project?.phases ?? []).map((p) => (
              <span key={p} className="rounded-full border bg-muted px-3 py-1 text-xs">
                {p}
              </span>
            ))}
            {(project?.phases?.length ?? 0) === 0 && <span className="text-sm text-muted-foreground">未設定</span>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">成果物一覧</CardTitle>
          <CardDescription>各工程の成果物 (xlsx/docx/pdf/source)</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ファイル名</TableHead>
                <TableHead>工程</TableHead>
                <TableHead>版</TableHead>
                <TableHead>サイズ</TableHead>
                <TableHead>アップロード日</TableHead>
                <TableHead className="w-32">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {artifactsQuery.isLoading && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    読み込み中...
                  </TableCell>
                </TableRow>
              )}
              {!artifactsQuery.isLoading && (artifactsQuery.data ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    成果物がありません
                  </TableCell>
                </TableRow>
              )}
              {(artifactsQuery.data ?? []).map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium">{a.file_name}</TableCell>
                  <TableCell>{a.phase}</TableCell>
                  <TableCell>v{a.version}</TableCell>
                  <TableCell className="text-sm">{formatBytes(a.size_bytes)}</TableCell>
                  <TableCell className="text-sm">{formatDateTime(a.uploaded_at)}</TableCell>
                  <TableCell className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => artifactsApi.download(a.id, a.file_name)}
                    >
                      DL
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        if (window.confirm(`${a.file_name} を削除しますか?`)) {
                          removeMutation.mutate(a.id);
                        }
                      }}
                      disabled={removeMutation.isPending}
                    >
                      削除
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">レビュー履歴</CardTitle>
          <CardDescription>Phase 4 で実装予定 (現状はプレースホルダ)</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            レビューを実行するには成果物をアップロード後、レビュー実行画面 (Phase 4) で対象を選択します。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
