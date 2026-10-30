"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { StudentMeData } from "@/lib/types";

export function useStudentMe() {
  const { token } = useAuth();
  return useQuery({ queryKey: ["student-me"], queryFn: () => api.get<StudentMeData>("/students/me", token), enabled: Boolean(token) });
}
