import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BatchDecisionPanel } from "@/components/aicte/batch-decision-panel";

const underReviewBatch = {
  id: "batch_demo",
  status: "UNDER_AICTE_REVIEW",
  decision: null,
  decisionReason: null,
} as never;

describe("BatchDecisionPanel", () => {
  it("requires a reason before returning a batch", () => {
    render(
      <BatchDecisionPanel
        batch={underReviewBatch}
        role="AICTE_REVIEWER"
        onDecision={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /return for correction/i }));
    expect(screen.getByRole("button", { name: /confirm return/i })).toBeDisabled();
  });
});
