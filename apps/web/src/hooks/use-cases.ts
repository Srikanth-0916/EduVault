"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CaseListResponse, DuplicateCase } from "@/lib/types";

export function useCases(filters: { status?: string; severity?: string; page?: number } = {}) {
  const { token } = useAuth();
  const params = new URLSearchParams({ pageSize: "50" });
  if (filters.status) params.set("status", filters.status);
  if (filters.severity) params.set("severity", filters.severity);
  if (filters.page) params.set("page", String(filters.page));
  return useQuery({
    queryKey: ["cases", filters.status ?? "all", filters.severity ?? "all", filters.page ?? 1],
    queryFn: () => api.get<CaseListResponse>(`/duplicate-cases?${params.toString()}`, token),
    enabled: Boolean(token),
  });
}

export function useCase(id: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["case", id],
    queryFn: () => api.get<DuplicateCase>(`/duplicate-cases/${id}`, token),
    enabled: Boolean(token && id),
  });
}
