"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/nav";

export default function PortalIndexPage() {
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    if (user) router.replace(roleHome(user.roles));
  }, [user, router]);

  return (
    <div
      className="flex min-h-[40vh] items-center justify-center text-sm text-ink-soft"
      role="status"
    >
      <Loader2 className="mr-2 size-4 animate-spin text-primary" aria-hidden="true" />
      Opening your workspace…
    </div>
  );
}
