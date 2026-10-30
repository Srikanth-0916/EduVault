"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EnrollmentDetail, EnrollmentSummary, Page } from "@/lib/types";

export interface StudentFilters {
  academicYear: string;
  search?: string;
  programmeId?: string;
  enrollmentStatus?: string;
  identityStatus?: string;
  page?: number;
  pageSize?: number;
}

export function useStudents(filters: StudentFilters) {
  const { token } = useAuth();
  const params = new URLSearchParams();
  params.set("academicYear", filters.academicYear);
  if (filters.search) params.set("search", filters.search);
  if (filters.programmeId) params.set("programmeId", filters.programmeId);
  if (filters.enrollmentStatus) params.set("enrollmentStatus", filters.enrollmentStatus);
  if (filters.identityStatus) params.set("identityStatus", filters.identityStatus);
  params.set("page", String(filters.page ?? 1));
  params.set("pageSize", String(filters.pageSize ?? 20));
  return useQuery({
    queryKey: ["students", Object.fromEntries(params.entries())],
    queryFn: () => api.get<Page<EnrollmentSummary>>(`/enrollments?${params.toString()}`, token),
    enabled: Boolean(token),
  });
}

export function useStudent(id: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["student", id],
    queryFn: () => api.get<EnrollmentDetail>(`/enrollments/${id}`, token),
    enabled: Boolean(token && id),
  });
}
