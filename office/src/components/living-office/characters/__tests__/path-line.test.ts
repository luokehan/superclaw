import { describe, expect, it } from "vitest";
import { computeLineGeometry } from "../PathLine";

describe("computeLineGeometry", () => {
  it("calculates distance for horizontal line", () => {
    const result = computeLineGeometry(
      { left: 0, top: 0 },
      { left: 100, top: 0 },
    );
    expect(result.distance).toBeCloseTo(100);
    expect(result.angle).toBeCloseTo(0);
  });

  it("calculates distance for vertical line", () => {
    const result = computeLineGeometry(
      { left: 0, top: 0 },
      { left: 0, top: 100 },
    );
    expect(result.distance).toBeCloseTo(100);
    expect(result.angle).toBeCloseTo(90);
  });

  it("calculates distance for diagonal line", () => {
    const result = computeLineGeometry(
      { left: 0, top: 0 },
      { left: 100, top: 100 },
    );
    expect(result.distance).toBeCloseTo(141.42, 1);
    expect(result.angle).toBeCloseTo(45);
  });

  it("handles negative direction", () => {
    const result = computeLineGeometry(
      { left: 100, top: 100 },
      { left: 0, top: 0 },
    );
    expect(result.distance).toBeCloseTo(141.42, 1);
    expect(result.angle).toBeCloseTo(-135);
  });

  it("handles same point (zero distance)", () => {
    const result = computeLineGeometry(
      { left: 50, top: 50 },
      { left: 50, top: 50 },
    );
    expect(result.distance).toBe(0);
  });

  it("calculates realistic office coordinates", () => {
    const result = computeLineGeometry(
      { left: 234, top: 422 },
      { left: 1100, top: 435 },
    );
    expect(result.distance).toBeGreaterThan(800);
    expect(Math.abs(result.angle)).toBeLessThan(10);
  });
});
