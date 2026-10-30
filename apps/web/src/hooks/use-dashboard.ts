"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { InstitutionDashboardData } from "@/lib/types";

export function useInstitutionDashboard(academicYear: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["institution-dashboard", academicYear],
    queryFn: () =>
      api.get<InstitutionDashboardData>(
        `/dashboard/institution?academicYear=${encodeURIComponent(academicYear)}`,
        token,
      ),
    enabled: Boolean(token),
  });
}
