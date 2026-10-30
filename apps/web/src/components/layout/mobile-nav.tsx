"use client";

import { X } from "lucide-react";
import { useEffect } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import type { NavGroup } from "@/lib/types";

export function MobileNav({
  open,
  onClose,
  groups,
  pathname,
  homeHref,
}: {
  open: boolean;
  onClose: () => void;
  groups: NavGroup[];
  pathname: string;
  homeHref: string;
}) {
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
      <button
        type="button"
        className="absolute inset-0 bg-ink/55 backdrop-blur-[2px]"
        aria-label="Close navigation"
        onClick={onClose}
      />
      <div className="relative h-full w-[288px] max-w-[86vw] animate-fade-in">
        <Sidebar
          groups={groups}
          pathname={pathname}
          homeHref={homeHref}
          onNavigate={onClose}
          className="h-full w-full"
        />
        <button
          type="button"
          onClick={onClose}
          autoFocus
          className="absolute right-2 top-3 inline-flex size-9 items-center justify-center rounded-[8px] text-white/65 hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5eead4]"
          aria-label="Close navigation"
        >
          <X className="size-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
