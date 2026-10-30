import type { DemoAccount } from "@/lib/types";

export const DEMO_PASSWORD = "Demo@1234";

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: "INSTITUTION_ADMIN",
    label: "Institution admin",
    email: "admin@demo-ait.edu",
    scope: "AIT",
  },
  {
    role: "INSTITUTION_OPERATOR",
    label: "Institution operator",
    email: "operator@demo-ait.edu",
    scope: "AIT",
  },
  {
    role: "INSTITUTION_NODAL_OFFICER",
    label: "Nodal officer",
    email: "nodal@demo-ait.edu",
    scope: "AIT",
  },
  {
    role: "AICTE_REVIEWER",
    label: "AICTE reviewer",
    email: "reviewer@aicte.demo",
    scope: "National",
  },
  {
    role: "AICTE_SUPERVISOR",
    label: "AICTE supervisor",
    email: "supervisor@aicte.demo",
    scope: "National",
  },
  {
    role: "AICTE_ANALYST",
    label: "AICTE analyst",
    email: "analyst@aicte.demo",
    scope: "National",
  },
  {
    role: "SYSTEM_ADMIN",
    label: "System admin",
    email: "sysadmin@aicte.demo",
    scope: "Technical",
  },
  {
    role: "AUDITOR",
    label: "Auditor",
    email: "auditor@aicte.demo",
    scope: "Read-only",
  },
  {
    role: "STUDENT",
    label: "Student",
    email: "student@demo-ait.edu",
    scope: "AIT",
  },
  {
    role: "EXTERNAL_VERIFIER",
    label: "External verifier",
    email: "verifier@acme-demo.example",
    scope: "Acme Demo",
  },
];

export const ROLE_LABELS: Record<string, string> = {
  INSTITUTION_ADMIN: "Institution administrator",
  INSTITUTION_OPERATOR: "Institution operator",
  INSTITUTION_NODAL_OFFICER: "Nodal officer",
  AICTE_REVIEWER: "AICTE reviewer",
  AICTE_SUPERVISOR: "AICTE supervisor",
  AICTE_ANALYST: "AICTE analyst",
  SYSTEM_ADMIN: "System administrator",
  AUDITOR: "Auditor",
  STUDENT: "Student",
  EXTERNAL_VERIFIER: "External verifier",
};
