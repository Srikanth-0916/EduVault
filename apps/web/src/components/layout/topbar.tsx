"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Bell, CalendarDays, ChevronDown, LogOut, Menu, Settings2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { RoleBadge } from "@/components/role-badge";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { areaLabel, navItemForPath } from "@/lib/nav";
import type { NavGroup, NotificationListResponse } from "@/lib/types";
import { initials } from "@/lib/utils";

export function Topbar({
  groups,
  pathname,
  onOpenMenu,
}: {
  groups: NavGroup[];
  pathname: string;
  onOpenMenu: () => void;
}) {
  const { user, logout, token } = useAuth();
  const router = useRouter();
  const [academicYear, setAcademicYear] = useState("2026-27");
  const current = navItemForPath(groups, pathname);
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<NotificationListResponse>("/notifications?page=1&pageSize=1", token),
    enabled: Boolean(token),
    staleTime: 30_000,
  });

  if (!user) return null;

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b border-border bg-surface/95 px-4 backdrop-blur sm:px-6">
      <button
        type="button"
        onClick={onOpenMenu}
        className="inline-flex size-10 items-center justify-center rounded-[8px] text-ink-soft hover:bg-surface-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="size-5" aria-hidden="true" />
      </button>

      <div className="min-w-0 flex-1">
        <p className="truncate text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-soft/55">
          {areaLabel(user.roles)}
        </p>
        <p className="truncate text-sm font-semibold text-ink">
          {current?.label ?? "Workspace"}
        </p>
      </div>

      <div className="hidden items-center gap-2 md:flex">
        <label htmlFor="academic-year" className="sr-only">
          Academic year
        </label>
        <div className="relative">
          <CalendarDays
            className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-ink-soft/55"
            aria-hidden="true"
          />
          <select
            id="academic-year"
            value={academicYear}
            onChange={(event) => setAcademicYear(event.target.value)}
            className="h-9 appearance-none rounded-[8px] border border-border bg-surface pl-8 pr-8 text-xs font-semibold text-ink-soft hover:border-ink/20 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="2026-27">2026-27</option>
            <option value="2025-26">2025-26</option>
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-2.5 top-1/2 size-3.5 -translate-y-1/2 text-ink-soft/55"
            aria-hidden="true"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => router.push("/notifications")}
        className="relative inline-flex size-10 items-center justify-center rounded-[8px] text-ink-soft hover:bg-surface-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        aria-label={`Notifications${notifications.data?.unread ? `, ${notifications.data.unread} unread` : ""}`}
        title="Notifications"
      >
        <Bell className="size-[18px]" aria-hidden="true" />
        {notifications.data?.unread ? (
          <span className="absolute -right-1 -top-1 flex min-w-4 items-center justify-center rounded-full bg-danger px-1 py-0.5 text-[9px] font-bold leading-none text-white ring-2 ring-surface">
            {notifications.data.unread > 9 ? "9+" : notifications.data.unread}
          </span>
        ) : null}
      </button>

      <span className="mx-1 hidden h-6 w-px bg-border sm:block" aria-hidden="true" />

      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button
            type="button"
            className="flex items-center gap-2 rounded-[8px] p-1 pr-1.5 text-left hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            aria-label="Open account menu"
          >
            <span className="flex size-8 items-center justify-center rounded-full bg-primary-soft text-[11px] font-bold text-primary-dark">
              {initials(user.fullName)}
            </span>
            <span className="hidden max-w-36 sm:block">
              <span className="block truncate text-xs font-semibold text-ink">{user.fullName}</span>
              <span className="block truncate text-[10px] text-ink-soft/65">{user.email}</span>
            </span>
            <ChevronDown className="size-3.5 text-ink-soft/55" aria-hidden="true" />
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={8}
            className="z-50 w-72 rounded-[12px] border border-border bg-surface p-1.5 shadow-pop animate-fade-in"
          >
            <div className="rounded-[8px] bg-surface-muted/60 px-3 py-2.5">
              <p className="text-sm font-semibold text-ink">{user.fullName}</p>
              <p className="mt-0.5 truncate text-xs text-ink-soft">{user.email}</p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <RoleBadge role={user.primaryRole} />
                {user.institutionName ? (
                  <span className="text-[10px] text-ink-soft/70">{user.institutionName}</span>
                ) : null}
              </div>
            </div>
            <DropdownMenu.Separator className="my-1.5 h-px bg-border" />
            <DropdownMenu.Label className="px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-soft/55">
              Session
            </DropdownMenu.Label>
            <DropdownMenu.Item
              disabled
              className="flex items-center gap-2 rounded-[6px] px-2.5 py-2 text-xs text-ink-soft/55 outline-none data-[disabled]:cursor-default"
            >
              <Settings2 className="size-3.5" aria-hidden="true" />
              Profile settings arriving later
            </DropdownMenu.Item>
            <DropdownMenu.Item
              onSelect={handleLogout}
              className="flex cursor-pointer items-center gap-2 rounded-[6px] px-2.5 py-2 text-xs font-medium text-danger outline-none hover:bg-danger-soft focus:bg-danger-soft"
            >
              <LogOut className="size-3.5" aria-hidden="true" />
              Sign out
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </header>
  );
}
