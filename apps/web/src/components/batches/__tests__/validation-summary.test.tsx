import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ValidationSummary } from "@/components/batches/validation-summary";

describe("ValidationSummary", () => {
  it("makes blocking findings and non-blocking warnings distinct", () => {
    render(
      <ValidationSummary
        summary={{
          totalRows: 10,
          validRows: 7,
          warningRows: 2,
          errorRows: 1,
          blockingFindings: 1,
          findings: 3,
          byRule: { "BR-002": 1, "BR-008": 2 },
        }}
      />,
    );

    expect(screen.getByText("1 blocking finding")).toBeInTheDocument();
    expect(screen.getByText("Warnings still submit")).toBeInTheDocument();
    expect(screen.getByText("BR-002: 1")).toBeInTheDocument();
  });

  it("states when a batch has no blocking findings", () => {
    render(
      <ValidationSummary
        summary={{ totalRows: 4, validRows: 4, warningRows: 0, errorRows: 0, blockingFindings: 0, findings: 0 }}
      />,
    );

    expect(screen.getByText("No blocking findings")).toBeInTheDocument();
    expect(screen.queryByText("Warnings still submit")).not.toBeInTheDocument();
  });
});
