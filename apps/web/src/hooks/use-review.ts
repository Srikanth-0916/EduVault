"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ReviewQueueResponse, ReviewSummary } from "@/lib/types";

export function useReviewQueue(status?: string) {
  const { token } = useAuth();
  const params = new URLSearchParams({ pageSize: "50" });
  if (status) params.set("status", status);
  return useQuery({
    queryKey: ["review-queue", status ?? "UNDER_AICTE_REVIEW"],
    queryFn: () => api.get<ReviewQueueResponse>(`/review/queue?${params.toString()}`, token),
    enabled: Boolean(token),
  });
}

export function useReviewSummary() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["review-summary"],
    queryFn: () => api.get<ReviewSummary>("/review/summary", token),
    enabled: Boolean(token),
  });
}
