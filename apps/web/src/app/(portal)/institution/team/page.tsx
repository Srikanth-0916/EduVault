"use client";

import {
  Check,
  Copy,
  MailPlus,
  ShieldAlert,
  UserCog,
  Users,
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { RoleBadge } from "@/components/role-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  StatCard,
} from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { InvitationResponse, Role, UserListResponse } from "@/lib/types";
import { formatDateTime, initials } from "@/lib/utils";

const INVITABLE_ROLES: { value: Role; label: string }[] = [
  { value: "INSTITUTION_OPERATOR", label: "Institution operator" },
  { value: "INSTITUTION_NODAL_OFFICER", label: "Nodal officer" },
  { value: "INSTITUTION_ADMIN", label: "Institution administrator" },
];

export default function InstitutionTeamPage() {
  const { user, token } = useAuth();
  const queryClient = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState<Role>("INSTITUTION_OPERATOR");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviting, setInviting] = useState(false);
  const [invitation, setInvitation] = useState<InvitationResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const isAdmin = Boolean(user?.roles.includes("INSTITUTION_ADMIN"));
  const teamQueryKey = ["institution-users", user?.institutionId] as const;
  const teamQuery = useQuery({
    queryKey: teamQueryKey,
    queryFn: () => api.get<UserListResponse>("/institutions/me/users", token),
    enabled: isAdmin && Boolean(token),
  });
  const users = teamQuery.data?.items ?? [];
  const loading = teamQuery.isLoading;
  const error =
    teamQuery.error instanceof ApiError
      ? teamQuery.error.message
      : teamQuery.error
        ? "Could not load the institution team."
        : null;

  function resetInvitation() {
    setInviteEmail("");
    setInviteName("");
    setInviteRole("INSTITUTION_OPERATOR");
    setInviteError(null);
    setInvitation(null);
    setCopied(false);
  }

  function handleInviteOpenChange(open: boolean) {
    setInviteOpen(open);
    if (!open) resetInvitation();
  }

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setInviteError(null);
    setInviting(true);
    try {
      const response = await api.post<InvitationResponse>(
        "/institutions/me/users/invitations",
        {
          fullName: inviteName.trim(),
          email: inviteEmail.trim(),
          role: inviteRole,
        },
        token,
      );
      setInvitation(response);
      queryClient.setQueryData<UserListResponse>(teamQueryKey, (current) =>
        current
          ? { items: [response.user, ...current.items], total: current.total + 1 }
          : { items: [response.user], total: 1 },
      );
    } catch (cause) {
      setInviteError(
        cause instanceof ApiError ? cause.message : "The invitation could not be created.",
      );
    } finally {
      setInviting(false);
    }
  }

  async function copyPassword() {
    if (!invitation) return;
    try {
      await navigator.clipboard.writeText(invitation.tempPassword);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Administration"
          title="Team access"
          description="Manage institution users, roles and invitations."
        />
        <Card>
          <CardContent className="flex items-start gap-4 p-6">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-[10px] bg-danger-soft text-danger">
              <ShieldAlert className="size-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="font-display text-lg font-semibold text-ink">
                Administrator access required
              </h2>
              <p className="mt-1 max-w-xl text-sm leading-6 text-ink-soft">
                Your membership does not include team administration. Ask an
                institution administrator if you need access to invitations.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const roleCounts = users.reduce<Record<string, number>>((counts, member) => {
    for (const role of member.roles) counts[role] = (counts[role] ?? 0) + 1;
    return counts;
  }, {});

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Administration"
        title="Team"
        description="Institution-scoped accounts and memberships. Invitations return a one-time demo password and are written to the audit trail."
        actions={
          <Button
            icon={<MailPlus className="size-4" aria-hidden="true" />}
            onClick={() => setInviteOpen(true)}
          >
            Invite user
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Institution users"
          value={loading ? "—" : users.length}
          hint="Active memberships at this institution"
          icon={<Users className="size-4" aria-hidden="true" />}
        />
        <StatCard
          label="Administrators"
          value={loading ? "—" : (roleCounts.INSTITUTION_ADMIN ?? 0)}
          hint="Can manage team membership"
          icon={<UserCog className="size-4" aria-hidden="true" />}
        />
        <StatCard
          label="Nodal officers"
          value={loading ? "—" : (roleCounts.INSTITUTION_NODAL_OFFICER ?? 0)}
          hint="Attest institution submissions"
          icon={<ShieldAlert className="size-4" aria-hidden="true" />}
        />
      </div>

      <Card className="overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle>Memberships</CardTitle>
          <CardDescription>
            Every list request is scoped to your institution by the API; the
            browser never supplies the tenant identifier.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <div className="m-5 rounded-[10px] border border-danger/20 bg-danger-soft/60 p-4 text-sm text-danger">
              <p>{error}</p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-3"
                onClick={() => void teamQuery.refetch()}
              >
                Retry
              </Button>
            </div>
          ) : loading ? (
            <div className="space-y-2 p-5" role="status" aria-label="Loading team">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="h-12" />
              ))}
            </div>
          ) : users.length === 0 ? (
            <EmptyState
              className="m-5 border-0 bg-transparent"
              title="No institution members yet"
              description="Invite an operator or nodal officer to start collaborating on submissions."
              icon={<Users className="size-5" aria-hidden="true" />}
              action={
                <Button size="sm" onClick={() => setInviteOpen(true)}>
                  Invite the first user
                </Button>
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last sign-in</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-soft text-[11px] font-bold text-primary-dark">
                          {initials(member.fullName)}
                        </span>
                        <span className="min-w-0">
                          <span className="block truncate text-[13px] font-semibold text-ink">
                            {member.fullName}
                            {member.id === user?.id ? (
                              <span className="ml-1.5 text-[10px] font-medium text-ink-soft/60">
                                (you)
                              </span>
                            ) : null}
                          </span>
                          <span className="block truncate text-xs text-ink-soft/70">
                            {member.email}
                          </span>
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {member.roles.map((role) => (
                          <RoleBadge key={role} role={role as Role} />
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge family="user" status={member.status} />
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-ink-soft">
                      {formatDateTime(member.lastLoginAt)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={inviteOpen}
        onOpenChange={handleInviteOpenChange}
        title={invitation ? "Invitation created" : "Invite a colleague"}
        description={
          invitation
            ? "Copy the one-time password before closing. It is never shown again."
            : "Create an institution membership. There is no email delivery in this prototype."
        }
        footer={
          invitation ? (
            <Button onClick={() => handleInviteOpenChange(false)}>Done</Button>
          ) : (
            <>
              <Button variant="secondary" onClick={() => handleInviteOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" form="invite-form" loading={inviting}>
                Create invitation
              </Button>
            </>
          )
        }
      >
        {invitation ? (
          <div className="space-y-4">
            <div className="rounded-[10px] border border-success/25 bg-success-soft/55 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-success">
                One-time demo password
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 rounded-[6px] border border-border bg-surface px-3 py-2 font-mono text-sm text-ink">
                  {invitation.tempPassword}
                </code>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => void copyPassword()}
                  icon={
                    copied ? (
                      <Check className="size-3.5" aria-hidden="true" />
                    ) : (
                      <Copy className="size-3.5" aria-hidden="true" />
                    )
                  }
                >
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
              <p className="mt-2 text-xs leading-5 text-ink-soft" aria-live="polite">
                {invitation.note}
              </p>
            </div>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-soft/60">
                  Name
                </dt>
                <dd className="mt-0.5 text-ink">{invitation.user.fullName}</dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-soft/60">
                  Email
                </dt>
                <dd className="mt-0.5 break-all text-ink">{invitation.user.email}</dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-soft/60">
                  Role
                </dt>
                <dd className="mt-1">
                  <RoleBadge role={invitation.user.roles[0] as Role} />
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-soft/60">
                  Status
                </dt>
                <dd className="mt-1">
                  <StatusBadge family="user" status={invitation.user.status} />
                </dd>
              </div>
            </dl>
          </div>
        ) : (
          <form id="invite-form" onSubmit={handleInvite} className="space-y-4">
            {inviteError ? (
              <div
                role="alert"
                className="rounded-[8px] border border-danger/20 bg-danger-soft/60 px-3 py-2.5 text-sm text-danger"
              >
                {inviteError}
              </div>
            ) : null}
            <Input
              label="Full name"
              value={inviteName}
              onChange={(event) => setInviteName(event.target.value)}
              placeholder="Ananya Rao"
              minLength={2}
              required
              autoComplete="name"
            />
            <Input
              label="Work email"
              type="email"
              value={inviteEmail}
              onChange={(event) => setInviteEmail(event.target.value)}
              placeholder="ananya@demo-ait.edu"
              required
              autoComplete="email"
            />
            <Select
              label="Membership role"
              value={inviteRole}
              onChange={(event) => setInviteRole(event.target.value as Role)}
              hint="Institution administrators can invite other administrators, operators or nodal officers."
            >
              {INVITABLE_ROLES.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </Select>
            <p className="rounded-[8px] border border-border bg-surface-muted/50 px-3 py-2.5 text-xs leading-5 text-ink-soft">
              The demo invitation sets an active membership immediately and
              returns a temporary password in this dialog. Production must use
              verified delivery and force a password change at first sign-in.
            </p>
          </form>
        )}
      </Dialog>
    </div>
  );
}
