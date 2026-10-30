"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ApprovalSnapshot, InstitutionDetail, InstitutionListResponse } from "@/lib/types";

export function useInstitutions(search: string) {
  const { token } = useAuth();
  const params = new URLSearchParams({ page: "1", pageSize: "100" });
  if (search.trim()) params.set("search", search.trim());
  return useQuery({ queryKey: ["aicte-institutions", search], queryFn: () => api.get<InstitutionListResponse>(`/institutions?${params.toString()}`, token), enabled: Boolean(token) });
}

export function useInstitutionDetail(id: string, academicYear: string) {
  const { token } = useAuth();
  return useQuery({ queryKey: ["aicte-institution", id, academicYear], queryFn: () => api.get<InstitutionDetail>(`/institutions/${id}?academicYear=${encodeURIComponent(academicYear)}`, token), enabled: Boolean(token && id) });
}

export function useIntakeHistory(programmeIds: string[]) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["intake-history", programmeIds],
    queryFn: async () => {
      const entries = await Promise.all(programmeIds.map(async (id) => [id, await api.get<ApprovalSnapshot[]>(`/programmes/${id}/intake-snapshots`, token)] as const));
      return Object.fromEntries(entries) as Record<string, ApprovalSnapshot[]>;
    },
    enabled: Boolean(token && programmeIds.length),
  });
}
