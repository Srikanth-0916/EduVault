"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { NationalDashboardData } from "@/lib/types";

export function useNationalDashboard(academicYear: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["national-dashboard", academicYear],
    queryFn: () => api.get<NationalDashboardData>(`/dashboard/national?academicYear=${encodeURIComponent(academicYear)}`, token),
    enabled: Boolean(token),
  });
}
