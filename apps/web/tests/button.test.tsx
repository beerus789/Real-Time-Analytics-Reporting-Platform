import { render, screen } from "@testing-library/react";

import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders a usable command button", () => {
    render(<Button>Generate</Button>);
    expect(screen.getByRole("button", { name: "Generate" })).toBeEnabled();
  });

  it("supports disabled error-state prevention", () => {
    render(<Button disabled>Generate</Button>);
    expect(screen.getByRole("button", { name: "Generate" })).toBeDisabled();
  });
});

