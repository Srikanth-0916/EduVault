"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { PublicVerificationData } from "@/lib/types";

export function usePublicVerification(token: string) {
  return useQuery({ queryKey: ["public-verification", token], queryFn: () => api.get<PublicVerificationData>(`/public/verify/${encodeURIComponent(token)}`), enabled: Boolean(token), retry: false });
}

export function useMyVerificationRequests() {
  const { token } = useAuth();
  return useQuery({ queryKey: ["verification-requests"], queryFn: () => api.get<{ items: import("@/lib/types").VerificationRequest[]; total: number }>("/verification-requests?scope=mine", token), enabled: Boolean(token) });
}
