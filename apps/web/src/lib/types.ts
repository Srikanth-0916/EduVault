export type Role =
  | "INSTITUTION_ADMIN"
  | "INSTITUTION_OPERATOR"
  | "INSTITUTION_NODAL_OFFICER"
  | "AICTE_REVIEWER"
  | "AICTE_SUPERVISOR"
  | "AICTE_ANALYST"
  | "SYSTEM_ADMIN"
  | "AUDITOR"
  | "STUDENT"
  | "EXTERNAL_VERIFIER";

export interface UserContext {
  id: string;
  email: string;
  fullName: string;
  roles: Role[];
  primaryRole: Role;
  institutionId: string | null;
  institutionName: string | null;
  studentIdentityId: string | null;
  mfaEnabled: boolean;
}

export interface LoginResponse {
  accessToken: string;
  expiresIn: number;
  user: UserContext;
}

export interface UserSummary {
  id: string;
  email: string;
  fullName: string;
  roles: Role[];
  status: string;
  institutionId: string | null;
  lastLoginAt: string | null;
}

export interface UserListResponse {
  items: UserSummary[];
  total: number;
}

export interface InvitationResponse {
  user: UserSummary;
  tempPassword: string;
  note: string;
}

export interface DemoAccount {
  role: Role;
  label: string;
  email: string;
  scope: string;
}

export type NavIcon =
  | "overview"
  | "students"
  | "batches"
  | "programmes"
  | "cases"
  | "team"
  | "review"
  | "institutions"
  | "reports"
  | "audit"
  | "record"
  | "sharing"
  | "verify"
  | "users";

export interface NavItem {
  label: string;
  href: string;
  icon: NavIcon;
  description?: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}
