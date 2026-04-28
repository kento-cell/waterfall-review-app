import { apiClient, API_URL } from "./client";
import type { Artifact } from "@/types/api";
import { useAuthStore } from "@/store/auth";

export const artifactsApi = {
  async list(projectId: string): Promise<Artifact[]> {
    const { data } = await apiClient.get<Artifact[]>(`/api/projects/${projectId}/artifacts`);
    return data;
  },

  async get(id: string): Promise<Artifact> {
    const { data } = await apiClient.get<Artifact>(`/api/artifacts/${id}`);
    return data;
  },

  async upload(
    projectId: string,
    phase: string,
    file: File,
    onProgress?: (progress: number) => void,
  ): Promise<Artifact> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("phase", phase);

    const { data } = await apiClient.post<Artifact>(
      `/api/projects/${projectId}/artifacts`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total && onProgress) {
            onProgress(Math.round((e.loaded * 100) / e.total));
          }
        },
      },
    );
    return data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(`/api/artifacts/${id}`);
  },

  downloadUrl(id: string): string {
    return `${API_URL}/api/artifacts/${id}/download`;
  },

  async download(id: string, fileName: string): Promise<void> {
    const token = useAuthStore.getState().token;
    const res = await fetch(`${API_URL}/api/artifacts/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};
