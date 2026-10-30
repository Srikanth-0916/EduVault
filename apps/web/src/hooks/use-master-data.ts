"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Capacity, InstitutionDetail, Programme } from "@/lib/types";

export function useMyInstitution(academicYear: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["my-institution", academicYear],
    queryFn: () =>
      api.get<InstitutionDetail>(
        `/institutions/me?academicYear=${encodeURIComponent(academicYear)}`,
        token,
      ),
    enabled: Boolean(token),
  });
}

export function useMyIntake(academicYear: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["my-intake", academicYear],
    queryFn: () =>
      api.get<Capacity[]>(
        `/institutions/me/intake?academicYear=${encodeURIComponent(academicYear)}`,
        token,
      ),
    enabled: Boolean(token),
  });
}

export function useMyProgrammes(academicYear: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["my-programmes", academicYear],
    queryFn: () =>
      api.get<Programme[]>(
        `/institutions/me/programmes?academicYear=${encodeURIComponent(academicYear)}`,
        token,
      ),
    enabled: Boolean(token),
  });
}
