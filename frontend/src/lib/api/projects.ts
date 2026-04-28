import { apiClient } from "./client";
import type { Project, ProjectCreate, ProjectUpdate } from "@/types/api";

export const projectsApi = {
  async list(): Promise<Project[]> {
    const { data } = await apiClient.get<Project[]>("/api/projects");
    return data;
  },

  async get(id: string): Promise<Project> {
    const { data } = await apiClient.get<Project>(`/api/projects/${id}`);
    return data;
  },

  async create(payload: ProjectCreate): Promise<Project> {
    const { data } = await apiClient.post<Project>("/api/projects", payload);
    return data;
  },

  async update(id: string, payload: ProjectUpdate): Promise<Project> {
    const { data } = await apiClient.put<Project>(`/api/projects/${id}`, payload);
    return data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(`/api/projects/${id}`);
  },
};
