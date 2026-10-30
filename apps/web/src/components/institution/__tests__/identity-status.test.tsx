import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IdentityStatus } from "@/components/institution/identity-status";

describe("IdentityStatus", () => {
  it("does not label a format-valid identity as verified", () => {
    render(<IdentityStatus status="FORMAT_VALID" />);

    expect(screen.getByText(/format valid/i)).toBeInTheDocument();
    expect(screen.queryByText(/^verified$/i)).not.toBeInTheDocument();
    expect(screen.getByText(/no external confirmation/i)).toBeInTheDocument();
  });

  it("labels external confirmation as mock rather than government verification", () => {
    render(<IdentityStatus status="EXTERNALLY_CONFIRMED" />);

    expect(screen.getByText(/externally confirmed/i)).toBeInTheDocument();
    expect(screen.getByText(/mock external check/i)).toBeInTheDocument();
    expect(screen.getByText(/not a live government response/i)).toBeInTheDocument();
  });
});
