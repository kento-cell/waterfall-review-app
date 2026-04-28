"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { projectsApi } from "@/lib/api/projects";
import { ALL_PHASES } from "@/types/api";
import type { Phase } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { formatDateTime } from "@/lib/utils";

const createSchema = z.object({
  name: z.string().min(1, "プロジェクト名は必須").max(200),
  description: z.string().optional(),
  phases: z.array(z.string()).optional(),
});

type CreateValues = z.infer<typeof createSchema>;

export default function ProjectsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
    },
  });

  const { register, handleSubmit, reset, watch, setValue, formState: { errors, isSubmitting } } = useForm<CreateValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { phases: ALL_PHASES as unknown as string[] },
  });

  const togglePhase = (phase: Phase) => {
    const current = (watch("phases") ?? []) as Phase[];
    if (current.includes(phase)) {
      setValue(
        "phases",
        current.filter((p) => p !== phase),
      );
    } else {
      setValue("phases", [...current, phase]);
    }
  };

  const onSubmit = (values: CreateValues) => {
    createMutation.mutate(
      { name: values.name, description: values.description || undefined, phases: (values.phases as Phase[]) ?? undefined },
      {
        onSuccess: () => reset({ name: "", description: "", phases: ALL_PHASES as unknown as string[] }),
      },
    );
  };

  const filtered = (data ?? []).filter((p) => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">プロジェクト一覧</h1>
        <Button onClick={() => setOpen(true)}>+ 新規プロジェクト</Button>
      </div>

      <div className="flex items-center gap-2">
        <Input
          placeholder="プロジェクト名で検索..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>プロジェクト名</TableHead>
              <TableHead>工程</TableHead>
              <TableHead>最終更新</TableHead>
              <TableHead className="w-24">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  読み込み中...
                </TableCell>
              </TableRow>
            )}
            {!isLoading && filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  プロジェクトがありません
                </TableCell>
              </TableRow>
            )}
            {filtered.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{(p.phases ?? []).join(" / ")}</TableCell>
                <TableCell className="text-sm">{formatDateTime(p.updated_at)}</TableCell>
                <TableCell>
                  <Link href={`/projects/${p.id}`}>
                    <Button variant="outline" size="sm">
                      詳細
                    </Button>
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新規プロジェクト作成</DialogTitle>
            <DialogDescription>案件単位でプロジェクトを作成します</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="name">プロジェクト名</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <span className="text-xs text-destructive">{errors.name.message}</span>}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="description">説明 (任意)</Label>
              <Input id="description" {...register("description")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label>対象工程</Label>
              <div className="flex flex-wrap gap-2">
                {ALL_PHASES.map((phase) => {
                  const checked = ((watch("phases") ?? []) as Phase[]).includes(phase);
                  return (
                    <button
                      type="button"
                      key={phase}
                      onClick={() => togglePhase(phase)}
                      className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                        checked ? "border-primary bg-primary text-primary-foreground" : "border-input bg-white"
                      }`}
                    >
                      {phase}
                    </button>
                  );
                })}
              </div>
            </div>
            {createMutation.isError && (
              <span className="text-sm text-destructive">作成に失敗しました</span>
            )}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                キャンセル
              </Button>
              <Button type="submit" disabled={isSubmitting || createMutation.isPending}>
                作成
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
