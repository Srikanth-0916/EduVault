import type { NavGroup, NavItem, Role } from "@/lib/types";

const INSTITUTION_STAFF: Role[] = [
  "INSTITUTION_ADMIN",
  "INSTITUTION_OPERATOR",
  "INSTITUTION_NODAL_OFFICER",
];

const AICTE_ROLES: Role[] = [
  "AICTE_REVIEWER",
  "AICTE_SUPERVISOR",
  "AICTE_ANALYST",
  "SYSTEM_ADMIN",
  "AUDITOR",
];

function hasAny(roles: Role[], candidates: Role[]): boolean {
  return roles.some((role) => candidates.includes(role));
}

function institutionNav(roles: Role[]): NavGroup[] {
  const groups: NavGroup[] = [
    {
      label: "Workspace",
      items: [
        {
          label: "Overview",
          href: "/institution",
          icon: "overview",
          description: "Intake, enrolment and review status",
        },
        {
          label: "Students",
          href: "/institution/students",
          icon: "students",
          description: "Student records and corrections",
        },
        {
          label: "Batches",
          href: "/institution/batches",
          icon: "batches",
          description: "CSV intake, validation, attestation",
        },
        {
          label: "Programmes & Intake",
          href: "/institution/programmes",
          icon: "programmes",
          description: "Approved capacity and allocations",
        },
      ],
    },
    {
      label: "Review",
      items: [
        {
          label: "Cases",
          href: "/institution/cases",
          icon: "cases",
          description: "Duplicate and overlap findings",
        },
      ],
    },
  ];

  if (roles.includes("INSTITUTION_ADMIN")) {
    groups.push({
      label: "Administration",
      items: [
        {
          label: "Team",
          href: "/institution/team",
          icon: "team",
          description: "Institution users and invitations",
        },
      ],
    });
  }
  return groups;
}

function aicteNav(roles: Role[]): NavGroup[] {
  const nationalItems: NavItem[] = [
    {
      label: "National Overview",
      href: "/aicte",
      icon: "overview" as const,
      description: "Coverage, capacity and quality",
    },
  ];

  if (hasAny(roles, ["AICTE_REVIEWER", "AICTE_SUPERVISOR"])) {
    nationalItems.push({
      label: "Review Queue",
      href: "/aicte/review",
      icon: "review" as const,
      description: "Submitted batches awaiting decision",
    });
  }

  if (hasAny(roles, ["AICTE_REVIEWER", "AICTE_SUPERVISOR", "AUDITOR", "SYSTEM_ADMIN"])) {
    nationalItems.push({
      label: "Institutions",
      href: "/aicte/institutions",
      icon: "institutions" as const,
      description: "Master data, campuses and programmes",
    });
    nationalItems.push({
      label: "Intake",
      href: "/aicte/intake",
      icon: "intake",
      description: "Versioned regular and supernumerary allocations",
    });
  }

  const oversightItems: NavItem[] = [];
  if (hasAny(roles, ["AICTE_REVIEWER", "AICTE_SUPERVISOR", "AUDITOR"])) {
    oversightItems.push({
      label: "Cases",
      href: "/aicte/cases",
      icon: "cases" as const,
      description: "Duplicate and transfer review",
    });
  }
  if (hasAny(roles, ["AICTE_SUPERVISOR", "AICTE_ANALYST", "AUDITOR"])) {
    oversightItems.push({
      label: "Reports",
      href: "/aicte/reports",
      icon: "reports" as const,
      description: "Aggregate and reconciliation exports",
    });
  }

  const groups: NavGroup[] = [{ label: "National", items: nationalItems }];
  if (oversightItems.length) {
    groups.push({ label: "Oversight", items: oversightItems });
  }

  if (hasAny(roles, ["AUDITOR", "SYSTEM_ADMIN"])) {
    groups.push({
      label: "Accountability",
      items: [
        {
          label: "Audit Trail",
          href: "/aicte/audit",
          icon: "audit",
          description: "Append-only action history",
        },
      ],
    });
  }

  if (roles.includes("SYSTEM_ADMIN")) {
    groups.push({
      label: "Administration",
      items: [
        {
          label: "Users",
          href: "/admin/users",
          icon: "users",
          description: "Platform accounts and access",
        },
      ],
    });
  }

  return groups;
}

function studentNav(): NavGroup[] {
  return [
    {
      label: "My record",
      items: [
        {
          label: "My Record",
          href: "/student",
          icon: "record",
          description: "Identity, enrolment and status",
        },
        {
          label: "Sharing",
          href: "/student/sharing",
          icon: "sharing",
          description: "Consent-based verification links",
        },
      ],
    },
  ];
}

function verifierNav(): NavGroup[] {
  return [
    {
      label: "Verification",
      items: [
        {
          label: "Verify a Reference",
          href: "/verifier",
          icon: "verify",
          description: "Resolve a consented verification link",
        },
      ],
    },
  ];
}

export function navForRoles(roles: Role[]): NavGroup[] {
  if (hasAny(roles, INSTITUTION_STAFF)) return institutionNav(roles);
  if (roles.includes("STUDENT")) return studentNav();
  if (roles.includes("EXTERNAL_VERIFIER")) return verifierNav();
  if (hasAny(roles, AICTE_ROLES)) return aicteNav(roles);
  return [];
}

export function roleHome(roles: Role[]): string {
  if (hasAny(roles, INSTITUTION_STAFF)) return "/institution";
  if (roles.includes("STUDENT")) return "/student";
  if (roles.includes("EXTERNAL_VERIFIER")) return "/verifier";
  if (hasAny(roles, AICTE_ROLES)) return "/aicte";
  return "/login";
}

export function areaLabel(roles: Role[]): string {
  if (hasAny(roles, INSTITUTION_STAFF)) return "Institution workspace";
  if (roles.includes("STUDENT")) return "Student portal";
  if (roles.includes("EXTERNAL_VERIFIER")) return "Verifier access";
  if (hasAny(roles, AICTE_ROLES)) return "AICTE national console";
  return "Restricted workspace";
}

export function navItemForPath(groups: NavGroup[], pathname: string) {
  const items = groups.flatMap((group) => group.items);
  return (
    items
      .filter((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))
      .sort((a, b) => b.href.length - a.href.length)[0] ?? null
  );
}
