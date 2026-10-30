import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { IntakeForm } from "@/components/aicte/intake-form";

const programme = {
  id: "prog_ait_cse",
  institutionId: "inst_ait",
  campusId: "camp_ait_main",
  programmeCode: "CSE",
  programmeName: "Computer Science and Engineering",
  awardLevel: "UNDERGRADUATE",
  durationYears: 4,
  status: "ACTIVE",
  campusName: "AIT Main",
  institutionName: "Synthetic AIT",
  approvedRegular: 120,
  approvedSupernumerary: 12,
  reportedRegular: 24,
  reportedSupernumerary: 2,
  capacityStatus: "WITHIN_APPROVED_INTAKE",
  approvalReference: "AICTE/DEMO/2026",
};

describe("IntakeForm", () => {
  it("shows supernumerary separately from regular intake", () => {
    render(<IntakeForm programme={programme} academicYear="2026-27" onSubmit={vi.fn()} />);

    expect(screen.getByLabelText(/regular approved seats/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/authorized supernumerary seats/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/authorization reference/i)).toBeInTheDocument();
  });
});
