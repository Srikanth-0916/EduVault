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
  | "intake"
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

export interface Page<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}

export interface Campus {
  id: string;
  institutionId: string;
  campusCode: string;
  name: string;
  location: string | null;
  status: string;
}

export interface Programme {
  id: string;
  institutionId: string;
  campusId: string;
  programmeCode: string;
  programmeName: string;
  awardLevel: string;
  durationYears: number;
  status: string;
  campusName: string | null;
  institutionName: string | null;
  approvedRegular: number;
  approvedSupernumerary: number;
  reportedRegular: number;
  reportedSupernumerary: number;
  capacityStatus: string | null;
  approvalReference: string | null;
}

export interface InstitutionDetail extends UserContextInstitution {
  campuses: Campus[];
  programmes: Programme[];
}

export interface UserContextInstitution {
  id: string;
  aicteInstitutionCode: string;
  name: string;
  institutionType: string;
  status: string;
  state: string | null;
  city: string | null;
  websiteUrl: string | null;
  contactEmail: string | null;
  campusCount: number;
  programmeCount: number;
}

export interface InstitutionListResponse {
  items: UserContextInstitution[];
  page: number;
  pageSize: number;
  total: number;
}

export interface ApprovalSnapshot {
  id: string;
  programmeId: string;
  academicYear: string;
  approvalReference: string;
  validFrom: string;
  validTo: string | null;
  issuedBy: string | null;
  notes: string | null;
  version: number;
  status: string;
  allocations: {
    id: string;
    approvalSnapshotId: string;
    seatClassification: string;
    approvedCount: number;
    authorizationReference: string | null;
  }[];
  createdAt: string | null;
}

export interface ReportEnvelope {
  generatedAt: string;
  filters: Record<string, unknown>;
  dataFreshness: string;
  suppressedGroups: number;
  items: Record<string, unknown>[];
}

export interface Capacity {
  programmeId: string;
  academicYear: string;
  allocations: Record<string, number>;
  reported: number;
  projected: number;
  status: string;
  evidence: Record<string, unknown>;
  approvalSnapshotId: string | null;
  approvalReference: string | null;
}

export interface Kpi {
  key: string;
  label: string;
  value: number;
  hint: string | null;
  tone: "default" | "warning" | "success" | "danger" | string;
}

export interface DashboardCapacityRow {
  programmeId: string;
  programmeCode: string;
  programmeName: string;
  campusName: string | null;
  approvedRegular: number;
  approvedSupernumerary: number;
  reportedRegular: number;
  reportedSupernumerary: number;
  reportedTotal: number;
  status: string;
  evidence: Record<string, unknown>;
}

export interface DistributionRow {
  key: string;
  label: string;
  count: number;
}

export interface DashboardBatch {
  id: string;
  academicYear: string;
  status: string;
  sourceType: string;
  rowCount: number;
  version: number;
  createdAt: string | null;
  submittedAt: string | null;
}

export interface DashboardCase {
  id: string;
  matchType: string;
  severity: string;
  status: string;
  openedAt: string;
}

export interface InstitutionDashboardData {
  institutionId: string;
  institutionName: string;
  academicYear: string;
  generatedAt: string;
  dataFreshness: string;
  kpis: Kpi[];
  capacity: DashboardCapacityRow[];
  identityDistribution: DistributionRow[];
  enrollmentStatusDistribution: DistributionRow[];
  recentBatches: DashboardBatch[];
  openCases: DashboardCase[];
}

export interface NationalDashboardData {
  academicYear: string;
  generatedAt: string;
  dataFreshness: string;
  kpis: Kpi[];
  institutionTypeDistribution: DistributionRow[];
  batchStatusDistribution: DistributionRow[];
  possibleExcessProgrammes: DashboardCapacityRow[];
  reportingInstitutions: {
    institutionId: string;
    institutionName: string;
    institutionType: string;
    enrollmentCount: number;
    batchCount: number;
    reportingStatus: string;
  }[];
}

export interface ReviewQueueItem {
  batchId: string;
  institutionId: string;
  institutionName: string;
  academicYear: string;
  status: string;
  rowCount: number;
  version: number;
  severity: string | null;
  blockingFindings: number;
  warningFindings: number;
  createdAt: string | null;
  submittedAt: string | null;
  ageDays: number;
  assignedReviewerId: string | null;
  decision: string | null;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  page: number;
  pageSize: number;
  total: number;
}

export interface ReviewSummary {
  underReview: number;
  returned: number;
  accepted: number;
  rejected: number;
  openCases: number;
  oldestPending: string | null;
  averageTurnaroundDays: number | null;
}

export interface Notification {
  id: string;
  eventType: string;
  title: string;
  body: string;
  channel: string;
  deliveryStatus: string;
  resourceType: string | null;
  resourceRef: string | null;
  readAt: string | null;
  createdAt: string | null;
}

export interface NotificationListResponse {
  items: Notification[];
  page: number;
  pageSize: number;
  total: number;
  unread: number;
}

export interface AuditEvent {
  id: string;
  actorId: string | null;
  actorEmail: string | null;
  actorRole: string | null;
  action: string;
  outcome: string;
  resourceType: string;
  resourceRef: string | null;
  institutionId: string | null;
  reason: string | null;
  metadata: Record<string, unknown> | null;
  timestamp: string;
}

export interface AuditListResponse {
  items: AuditEvent[];
  page: number;
  pageSize: number;
  total: number;
}

export interface Finding {
  id: string;
  ruleId: string;
  code: string;
  severity: string;
  blocking: boolean;
  message: string;
  field: string | null;
  status: string;
  evidence: Record<string, unknown> | null;
  rowId: string | null;
}

export interface EnrollmentSummary {
  id: string;
  institutionId: string;
  institutionName: string | null;
  campusId: string | null;
  campusName: string | null;
  programmeId: string;
  programmeName: string | null;
  studentLocalId: string;
  studentFullName: string;
  maskedApaar: string;
  identityStatus: string | null;
  academicYear: string;
  admissionDate: string;
  exitDate: string | null;
  enrollmentStatus: string;
  seatClassification: string;
  admissionCategory: string | null;
  nriStatus: string;
  ociStatus: string;
  foreignNationalStatus: string;
  version: number;
  isCurrent: boolean;
  recordAcceptedAt: string | null;
  updatedAt: string | null;
}

export interface EnrollmentVersion {
  id: string;
  version: number;
  snapshot: Record<string, unknown>;
  changeReason: string | null;
  changedBy: string | null;
  actorRole: string | null;
  createdAt: string;
}

export interface IdentityVerification {
  id: string;
  provider: string;
  providerReference: string | null;
  result: string;
  adapterVersion: string;
  isMock: boolean;
  checkedAt: string;
  purpose: string | null;
  consentContext: string | null;
  resultingStatus: string | null;
  detail: Record<string, unknown> | null;
}

export interface EnrollmentDetail extends EnrollmentSummary {
  supernumeraryApprovalReference: string | null;
  versions: EnrollmentVersion[];
  verifications: IdentityVerification[];
  findings: Finding[];
}

export interface BatchSummary {
  id: string;
  institutionId: string;
  campusId: string | null;
  programmeId: string | null;
  academicYear: string;
  sourceType: string;
  status: string;
  version: number;
  supersedesBatchId: string | null;
  fileName: string | null;
  fileChecksum: string | null;
  fileSizeBytes: number | null;
  rowCount: number | null;
  summary: Record<string, unknown>;
  createdAt: string | null;
  attestedAt: string | null;
  submittedAt: string | null;
  decision: string | null;
  decisionReason: string | null;
  decisionReasonCode: string | null;
  decidedAt: string | null;
}

export interface BatchRow {
  id: string;
  sourceRowNumber: number;
  studentName: string | null;
  studentLocalId: string | null;
  maskedApaar: string;
  rowStatus: string;
  enrollmentId: string | null;
  findings: Finding[];
}

export interface BatchDetail extends BatchSummary {
  rows: BatchRow[];
  findings: Finding[];
  validationRunId: string | null;
  validationSummary: Record<string, unknown> | null;
}

export interface BatchListResponse {
  items: BatchSummary[];
  total: number;
}

export interface DuplicateCase {
  id: string;
  matchGroupId: string;
  matchType: string;
  severity: string;
  status: string;
  primaryEnrollmentId: string | null;
  relatedEnrollmentId: string | null;
  institutionId: string | null;
  discoveredBatchId: string | null;
  openedAt: string;
  assignedReviewerId: string | null;
  resolutionCode: string | null;
  resolutionReason: string | null;
  resolvedBy: string | null;
  resolvedAt: string | null;
  evidence: Record<string, unknown> | null;
}

export interface CaseListResponse {
  items: DuplicateCase[];
  total: number;
}

export interface BatchReceipt {
  batchId: string;
  checksum: string;
  rowCount: number;
  submittedBy: string | null;
  submittedAt: string | null;
  payload: Record<string, unknown>;
  signature: Record<string, string>;
}

export interface VerificationRequest {
  id: string;
  recipientName: string;
  recipientOrg: string;
  recipientEmail: string;
  purpose: string;
  requestedClaims: string[];
  legalBasis: string;
  status: string;
  singleUse: boolean;
  expiresInHours: number;
  issuedAt: string | null;
  expiresAt: string | null;
  viewedAt: string | null;
  revokedAt: string | null;
  revokedReason: string | null;
  createdAt: string;
}

export interface VerificationReceipt {
  id: string;
  payload: Record<string, unknown>;
  signature: string;
  algorithm: string;
  keyId: string;
  issuedAt: string;
  expiresAt: string;
}

export interface AuthorizeResponse {
  request: VerificationRequest;
  token: string;
  verifyUrl: string;
  expiresAt: string;
  receipt: VerificationReceipt;
}

export interface StudentMeData {
  maskedApaar: string;
  identityStatus: string;
  identityLast4: string | null;
  enrollments: {
    id: string;
    institutionId: string;
    programmeId: string;
    academicYear: string;
    enrollmentStatus: string;
    seatClassification: string;
    recordAccepted: boolean;
  }[];
  verificationRequests: VerificationRequest[];
}

export interface PublicClaim {
  key: string;
  label: string;
  value: string;
  source: string;
  status: string;
  asOf: string | null;
}

export interface PublicVerificationData {
  valid: boolean;
  claims: PublicClaim[];
  receipt: VerificationReceipt | null;
  expiresAt: string | null;
  demoNotice: string;
}
