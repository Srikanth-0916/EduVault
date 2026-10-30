"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BatchDetail, BatchListResponse } from "@/lib/types";

export function useBatches(academicYear: string, status?: string) {
  const { token } = useAuth();
  const params = new URLSearchParams({ academicYear, pageSize: "50" });
  if (status) params.set("status", status);
  return useQuery({
    queryKey: ["batches", academicYear, status ?? "all"],
    queryFn: () =>
      api.get<BatchListResponse>(`/submission-batches?${params.toString()}`, token),
    enabled: Boolean(token),
  });
}

export function useBatch(id: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["batch", id],
    queryFn: () => api.get<BatchDetail>(`/submission-batches/${id}`, token),
    enabled: Boolean(token && id),
  });
}
