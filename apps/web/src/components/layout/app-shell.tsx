"use client";

import { Loader2 } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { Logo } from "@/components/logo";
import { MobileNav } from "@/components/layout/mobile-nav";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/lib/auth";
import { navForRoles, roleHome } from "@/lib/nav";

function SessionLoading() {
  return (
    <div className="flex min-h-[calc(100dvh-2rem)] items-center justify-center bg-canvas px-6">
      <div className="flex flex-col items-center gap-4 text-center" role="status" aria-live="polite">
        <Logo />
        <div className="flex items-center gap-2 text-xs font-medium text-ink-soft">
          <Loader2 className="size-3.5 animate-spin text-primary" aria-hidden="true" />
          Restoring demo session…
        </div>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  // Store the pathname alongside the open flag so a navigation closes the
  // drawer without a pathname effect setting state after render.
  const [mobileState, setMobileState] = useState({ open: false, pathname });
  const mobileOpen = mobileState.open && mobileState.pathname === pathname;
  const closeMobile = useCallback(
    () => setMobileState({ open: false, pathname }),
    [pathname],
  );
  const openMobile = useCallback(
    () => setMobileState({ open: true, pathname }),
    [pathname],
  );

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading) return <SessionLoading />;
  if (!user) return null;

  const groups = navForRoles(user.roles);
  const homeHref = roleHome(user.roles);

  return (
    <TooltipProvider delayDuration={200}>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <div className="flex min-h-[calc(100dvh-2rem)] bg-canvas">
        <Sidebar
          groups={groups}
          pathname={pathname}
          homeHref={homeHref}
          className="hidden lg:flex"
        />
        <MobileNav
          open={mobileOpen}
          onClose={closeMobile}
          groups={groups}
          pathname={pathname}
          homeHref={homeHref}
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar groups={groups} pathname={pathname} onOpenMenu={openMobile} />
          <main id="main-content" className="app-canvas flex-1">
            <div className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
              <div className="animate-fade-in">{children}</div>
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}
