import { describe, expect, it } from "vitest";

import { areaLabel, navForRoles, navItemForPath, roleHome } from "@/lib/nav";
import type { NavGroup, Role } from "@/lib/types";

function labels(groups: NavGroup[]): string[] {
  return groups.flatMap((group) => group.items.map((item) => item.label));
}

describe("role-aware navigation", () => {
  it("gives institution administrators the complete workspace, including Team", () => {
    const groups = navForRoles(["INSTITUTION_ADMIN"]);
    expect(labels(groups)).toEqual([
      "Overview",
      "Students",
      "Batches",
      "Programmes & Intake",
      "Cases",
      "Team",
    ]);
    expect(navItemForPath(groups, "/institution/team")?.label).toBe("Team");
  });

  it("does not expose Team to operators or nodal officers", () => {
    for (const role of ["INSTITUTION_OPERATOR", "INSTITUTION_NODAL_OFFICER"] as const) {
      const labelsForRole = labels(navForRoles([role]));
      expect(labelsForRole).toContain("Batches");
      expect(labelsForRole).not.toContain("Team");
    }
  });

  it("gives AICTE supervisors review and oversight without system administration", () => {
    const groups = navForRoles(["AICTE_SUPERVISOR"]);
    expect(labels(groups)).toEqual([
      "National Overview",
      "Review Queue",
      "Institutions",
      "Cases",
      "Reports",
    ]);
    expect(labels(groups)).not.toContain("Users");
    expect(labels(groups)).not.toContain("Audit Trail");
  });

  it("limits analysts to aggregate reporting surfaces", () => {
    expect(labels(navForRoles(["AICTE_ANALYST"]))).toEqual([
      "National Overview",
      "Reports",
    ]);
  });

  it("limits auditors to read-only oversight and audit", () => {
    expect(labels(navForRoles(["AUDITOR"]))).toEqual([
      "National Overview",
      "Institutions",
      "Cases",
      "Reports",
      "Audit Trail",
    ]);
  });

  it("adds user administration only for system administrators", () => {
    const groups = navForRoles(["SYSTEM_ADMIN"]);
    expect(labels(groups)).toContain("Users");
    expect(labels(groups)).toContain("Audit Trail");
    expect(navItemForPath(groups, "/admin/users")?.label).toBe("Users");
  });

  it("keeps the student portal to record and sharing", () => {
    expect(labels(navForRoles(["STUDENT"]))).toEqual(["My Record", "Sharing"]);
  });

  it("keeps the external verifier to the verification entry point", () => {
    expect(labels(navForRoles(["EXTERNAL_VERIFIER"]))).toEqual(["Verify a Reference"]);
  });

  it("resolves a role-appropriate home route", () => {
    expect(roleHome(["INSTITUTION_ADMIN"])).toBe("/institution");
    expect(roleHome(["AICTE_REVIEWER"])).toBe("/aicte");
    expect(roleHome(["STUDENT"])).toBe("/student");
    expect(roleHome(["EXTERNAL_VERIFIER"])).toBe("/verifier");
    expect(roleHome([])).toBe("/login");
  });

  it("describes the active workspace for the top bar", () => {
    expect(areaLabel(["INSTITUTION_OPERATOR"])).toBe("Institution workspace");
    expect(areaLabel(["AUDITOR"])).toBe("AICTE national console");
    expect(areaLabel(["STUDENT"])).toBe("Student portal");
  });

  it("matches nested routes and falls back to the nearest parent", () => {
    const groups = navForRoles(["INSTITUTION_ADMIN"]);
    expect(navItemForPath(groups, "/institution/students/sid_demo_student_1")?.label).toBe(
      "Students",
    );
    // A sibling whose name merely shares a prefix must not match Students;
    // it is still beneath the institution overview route.
    expect(navItemForPath(groups, "/institution/studentship")?.label).toBe("Overview");
    expect(navItemForPath(groups, "/outside-the-console")).toBeNull();
  });

  it("returns no navigation for an unknown role", () => {
    expect(navForRoles(["UNKNOWN_ROLE" as Role])).toEqual([]);
  });
});
