"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

export const ACADEMIC_YEARS = ["2025-26", "2026-27", "2027-28"] as const;
export const CURRENT_ACADEMIC_YEAR = "2026-27";

export function useAcademicYear(): [string, (year: string) => void] {
  const pathname = usePathname();
  const router = useRouter();
  const params = useSearchParams();
  const year = params.get("academicYear") ?? CURRENT_ACADEMIC_YEAR;
  const setYear = useCallback(
    (next: string) => {
      const query = new URLSearchParams(params.toString());
      query.set("academicYear", next);
      router.replace(`${pathname}?${query.toString()}`);
    },
    [pathname, params, router],
  );
  return [year, setYear];
}
