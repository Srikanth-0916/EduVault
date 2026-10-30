import Link from "next/link";
import {
  BookOpen,
  Building2,
  ChartNoAxesCombined,
  ClipboardCheck,
  ClipboardList,
  FileSpreadsheet,
  Landmark,
  LayoutDashboard,
  ScanLine,
  ScrollText,
  Share2,
  ShieldCheck,
  UserCog,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";

import { Logo } from "@/components/logo";
import { cn } from "@/lib/utils";
import type { NavGroup, NavIcon } from "@/lib/types";
import { navItemForPath } from "@/lib/nav";

const ICONS: Record<NavIcon, LucideIcon> = {
  overview: LayoutDashboard,
  students: Users,
  batches: FileSpreadsheet,
  programmes: BookOpen,
  cases: ClipboardCheck,
  team: UserCog,
  review: ShieldCheck,
  institutions: Building2,
  intake: ClipboardList,
  reports: ChartNoAxesCombined,
  audit: ScrollText,
  record: UserRound,
  sharing: Share2,
  verify: ScanLine,
  users: UserCog,
};

export function Sidebar({
  groups,
  pathname,
  homeHref,
  onNavigate,
  className,
}: {
  groups: NavGroup[];
  pathname: string;
  homeHref: string;
  onNavigate?: () => void;
  className?: string;
}) {
  const activeItem = navItemForPath(groups, pathname);

  return (
    <aside
      className={cn(
        "flex w-[264px] shrink-0 flex-col bg-ink text-white lg:sticky lg:top-0 lg:h-[calc(100dvh-2rem)]",
        className,
      )}
    >
      <div className="flex h-16 items-center border-b border-white/8 px-5">
        <Link href={homeHref} onClick={onNavigate} className="rounded-[8px]" aria-label="APAAR-SDMV home">
          <Logo variant="light" />
        </Link>
      </div>

      <nav aria-label="Primary navigation" className="flex-1 overflow-y-auto px-3 py-4 scrollbar-thin">
        {groups.map((group) => (
          <div key={group.label} className="mb-5">
            <p className="px-2.5 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-white/40">
              {group.label}
            </p>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = ICONS[item.icon];
                const active = activeItem?.href === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "group relative flex items-center gap-2.5 rounded-[8px] px-2.5 py-2 text-[13px] font-medium transition-colors",
                        active
                          ? "bg-white/10 text-white before:absolute before:left-0 before:top-1/2 before:h-4 before:w-[2px] before:-translate-y-1/2 before:rounded-full before:bg-[#5eead4]"
                          : "text-white/66 hover:bg-white/6 hover:text-white",
                      )}
                    >
                      <Icon
                        className={cn(
                          "size-[17px] shrink-0",
                          active ? "text-[#5eead4]" : "text-white/45 group-hover:text-white/75",
                        )}
                        aria-hidden="true"
                      />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/8 p-3">
        <div className="rounded-[10px] border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center gap-2 text-[11px] font-semibold text-white/80">
            <Landmark className="size-3.5 text-[#5eead4]" aria-hidden="true" />
            Demo workspace
          </div>
          <p className="mt-1.5 text-[11px] leading-5 text-white/48">
            Synthetic data only. APAAR checks are mock/sandbox, never live government verification.
          </p>
        </div>
      </div>
    </aside>
  );
}
