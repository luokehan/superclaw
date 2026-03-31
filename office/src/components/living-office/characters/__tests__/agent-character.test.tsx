import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AgentCharacter2D5 } from "../AgentCharacter2D5";

afterEach(cleanup);

describe("AgentCharacter2D5", () => {
  it("renders with agent data attributes", () => {
    const { container } = render(
      <AgentCharacter2D5
        agentId="test-agent"
        deskId="desk-gm"
        name="Test Agent"
        perceivedState="IDLE"
      />,
    );

    const el = container.querySelector("[data-agent-id='test-agent']");
    expect(el).toBeTruthy();
    expect(el?.getAttribute("data-agent-state")).toBe("IDLE");
  });

  it("renders the agent name", () => {
    render(
      <AgentCharacter2D5
        agentId="test-agent"
        deskId="desk-gm"
        name="General Manager"
        perceivedState="IDLE"
      />,
    );

    expect(screen.getByText("General Manager")).toBeTruthy();
  });

  it("applies idle CSS class by default", () => {
    const { container } = render(
      <AgentCharacter2D5
        agentId="test-agent"
        deskId="desk-gm"
        name="Test"
        perceivedState="IDLE"
      />,
    );

    const el = container.querySelector(".lo-character");
    expect(el?.classList.contains("lo-char-state-idle")).toBe(true);
  });

  it("uses absolute positioning", () => {
    const { container } = render(
      <AgentCharacter2D5
        agentId="test-agent"
        deskId="desk-gm"
        name="Test"
        perceivedState="WORKING"
      />,
    );

    const el = container.querySelector(".lo-character") as HTMLElement;
    expect(el?.style.position).toBe("absolute");
  });
});
