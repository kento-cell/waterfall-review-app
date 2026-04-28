// API types matching backend Pydantic schemas (Phase 1+2).
// Source: backend/app/schemas/

export type Phase = "要件定義" | "基本設計" | "詳細設計" | "PG" | "UT" | "IT" | "ST";
export const ALL_PHASES: Phase[] = ["要件定義", "基本設計", "詳細設計", "PG", "UT", "IT", "ST"];

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "admin" | "general";
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  phases: Phase[] | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  phases?: Phase[];
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  phases?: Phase[] | null;
}

export interface Artifact {
  id: string;
  project_id: string;
  phase: string;
  file_name: string;
  file_path: string;
  file_type: string;
  version: number;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
}

export type ReviewStatus = "pending" | "running" | "completed" | "failed";
export type PdfStatus = "pending" | "running" | "completed" | "failed";

export interface Review {
  id: string;
  project_id: string;
  review_type: "single" | "cross";
  target_artifact_ids: string[];
  aspect_ids: string[];
  status: ReviewStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message?: string | null;
  created_at?: string;
  pdf_status?: PdfStatus | null;
  pdf_path?: string | null;
  pdf_generated_at?: string | null;
}

export interface Finding {
  id: string;
  review_id: string;
  artifact_id: string | null;
  location: string | null;
  severity: "high" | "mid" | "low";
  aspect_id: string | null;
  aspect_name?: string | null;
  content: string;
  suggestion: string | null;
  created_at: string;
  response_status: "not_started" | "in_progress" | "done" | "not_applicable";
}

export interface PdfStatusResponse {
  review_id: string;
  status: PdfStatus;
  pdf_path: string | null;
  pdf_generated_at: string | null;
  error_message: string | null;
}

export interface ApiError {
  detail: string | Array<{ msg: string; loc?: string[] }>;
}
