"use client";

import * as React from "react";
import { cn, formatBytes } from "@/lib/utils";

export interface DropzoneProps {
  label: string;
  description?: string;
  accept?: string;
  maxSizeMb?: number;
  file: File | null;
  onFileChange: (file: File | null) => void;
  badge?: { text: string; color: string };
  variant?: "default" | "amber" | "blue" | "navy";
  required?: boolean;
}

const variantClasses: Record<NonNullable<DropzoneProps["variant"]>, string> = {
  default: "border-gray-300 bg-gray-50",
  amber: "border-amber-500 bg-amber-50",
  blue: "border-blue-400 bg-blue-50",
  navy: "border-blue-900 bg-blue-50",
};

const activeClasses: Record<NonNullable<DropzoneProps["variant"]>, string> = {
  default: "border-gray-500 bg-gray-100",
  amber: "border-amber-700 bg-amber-100",
  blue: "border-blue-600 bg-blue-100",
  navy: "border-blue-950 bg-blue-100",
};

export function Dropzone({
  label,
  description,
  accept,
  maxSizeMb = 50,
  file,
  onFileChange,
  badge,
  variant = "default",
  required = false,
}: DropzoneProps) {
  const [isDragging, setIsDragging] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  const validate = (f: File): string | null => {
    if (f.size > maxSizeMb * 1024 * 1024) {
      return `${maxSizeMb}MB を超えています (現: ${formatBytes(f.size)})`;
    }
    if (accept) {
      const exts = accept.split(",").map((e) => e.trim().toLowerCase());
      const fileExt = "." + (f.name.split(".").pop()?.toLowerCase() ?? "");
      if (!exts.includes(fileExt)) {
        return `許可されていない拡張子: ${fileExt} (許可: ${exts.join(", ")})`;
      }
    }
    return null;
  };

  const handleFile = (f: File | null) => {
    setError(null);
    if (!f) {
      onFileChange(null);
      return;
    }
    const err = validate(f);
    if (err) {
      setError(err);
      onFileChange(null);
      return;
    }
    onFileChange(f);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0] ?? null;
    handleFile(f);
  };

  const onClick = () => {
    inputRef.current?.click();
  };

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    handleFile(f);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">{label}</span>
        {required && <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">必須</span>}
        {badge && (
          <span
            className="rounded px-2 py-0.5 text-xs font-bold text-white"
            style={{ backgroundColor: badge.color }}
          >
            {badge.text}
          </span>
        )}
      </div>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={onClick}
        className={cn(
          "flex min-h-[140px] cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-4 transition-colors",
          isDragging ? activeClasses[variant] : variantClasses[variant],
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={onSelectFile}
          className="hidden"
        />
        {!file && (
          <>
            <span className="text-3xl">📁</span>
            <span className="text-sm font-medium">ここにファイルをドラッグ</span>
            <span className="text-xs text-gray-500">またはクリックで選択</span>
            {description && <span className="text-xs text-gray-400">{description}</span>}
          </>
        )}
        {file && (
          <>
            <span className="text-3xl">📄</span>
            <span className="text-sm font-semibold">{file.name}</span>
            <span className="text-xs text-gray-500">{formatBytes(file.size)}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleFile(null);
              }}
              className="text-xs text-red-600 hover:underline"
            >
              削除して選び直す
            </button>
          </>
        )}
      </div>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
