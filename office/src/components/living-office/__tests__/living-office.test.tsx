import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { GlassPanel } from "../panels/GlassPanel";
import { StatusRing } from "../workspace/StatusRing";
import { DeskBubble } from "../workspace/DeskBubble";
import { Desk } from "../workspace/Desk";
import type { DeskConfig } from "../types";

describe("GlassPanel", () => {
  it("renders children inside glass panel", () => {
    render(
      <GlassPanel>
        <span>Panel content</span>
      </GlassPanel>,
    );
    expect(screen.getByText("Panel content")).toBeTruthy();
  });

  it("applies custom className", () => {
    const { container } = render(
      <GlassPanel className="custom-class">Content</GlassPanel>,
    );
    expect(container.firstElementChild?.classList.contains("custom-class")).toBe(
      true,
    );
  });

  it("applies glass morphism styles", () => {
    const { container } = render(<GlassPanel>Content</GlassPanel>);
    const el = container.firstElementChild as HTMLElement;
    expect(el.style.borderRadius).toBe("22px");
    expect(el.style.overflow).toBe("hidden");
  });
});

describe("StatusRing", () => {
  it("renders with idle status color", () => {
    const { container } = render(<StatusRing status="idle" />);
    const ring = container.firstElementChild as HTMLElement;
    expect(ring.style.background).toBe("var(--lo-good)");
  });

  it("renders with busy status color", () => {
    const { container } = render(<StatusRing status="busy" />);
    const ring = container.firstElementChild as HTMLElement;
    expect(ring.style.background).toBe("var(--lo-warn)");
  });

  it("renders with blocked status color", () => {
    const { container } = render(<StatusRing status="blocked" />);
    const ring = container.firstElementChild as HTMLElement;
    expect(ring.style.background).toBe("var(--lo-bad)");
  });

  it("renders with heartbeat status color", () => {
    const { container } = render(<StatusRing status="heartbeat" />);
    const ring = container.firstElementChild as HTMLElement;
    expect(ring.style.background).toBe("var(--lo-cyan)");
  });
});

describe("DeskBubble", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows bubble text when provided", () => {
    render(<DeskBubble text="收到新事务" />);
    expect(screen.getByText("收到新事务")).toBeTruthy();
  });

  it("hides when text is empty", () => {
    const { container } = render(<DeskBubble text="" />);
    expect(container.firstElementChild?.childElementCount ?? 0).toBe(0);
  });

  it("auto-hides after duration", () => {
    render(<DeskBubble text="测试气泡" duration={2600} />);
    expect(screen.getByText("测试气泡")).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(2700);
    });

    expect(screen.queryByText("测试气泡")).toBeNull();
  });
});

describe("Desk", () => {
  const mockConfig: DeskConfig = {
    id: "desk-test",
    agentName: "Test Agent",
    role: "tester",
    position: { left: 100, top: 200 },
  };

  it("renders agent name and role", () => {
    render(<Desk config={mockConfig} />);
    expect(screen.getByText("Test Agent")).toBeTruthy();
    expect(screen.getByText("tester")).toBeTruthy();
  });

  it("renders with data-desk-id attribute", () => {
    const { container } = render(<Desk config={mockConfig} />);
    const desk = container.firstElementChild as HTMLElement;
    expect(desk.dataset.deskId).toBe("desk-test");
  });

  it("renders heartbeat pulse ring when status is heartbeat", () => {
    const { container } = render(
      <Desk config={mockConfig} status="heartbeat" />,
    );
    const desk = container.firstElementChild as HTMLElement;
    const pulseRing = desk.firstElementChild as HTMLElement;
    expect(pulseRing.style.animation).toContain("lo-pulse");
  });

  it("does not render pulse ring for non-heartbeat status", () => {
    const { container } = render(<Desk config={mockConfig} status="idle" />);
    const desk = container.firstElementChild as HTMLElement;
    const firstChild = desk.firstElementChild as HTMLElement;
    expect(firstChild.style.animation).not.toContain("lo-pulse");
  });
});
