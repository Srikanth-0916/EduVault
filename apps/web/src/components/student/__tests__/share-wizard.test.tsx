import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ShareWizard } from "@/components/student/share-wizard";

describe("ShareWizard", () => {
  it("requires explicit claim selection before authorizing", () => {
    render(<ShareWizard open onOpenChange={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByRole("button", { name: /review authorization/i })).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/programme/i));
    expect(screen.getByRole("button", { name: /review authorization/i })).toBeEnabled();
  });
});
