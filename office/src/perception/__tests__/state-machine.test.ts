import { describe, expect, it, vi } from "vitest";
import {
  isLegalTransition,
  resetToIdle,
  transition,
  TRANSITIONS,
} from "../state-machine";
import type { PerceivedAgentState, PerceivedKind } from "../types";

describe("state-machine", () => {
  describe("legal transitions", () => {
    const legalCases: Array<[PerceivedAgentState, PerceivedKind, PerceivedAgentState]> = [
      ["IDLE", "ARRIVE", "INCOMING"],
      ["INCOMING", "ACK", "ACK"],
      ["ACK", "DISPATCH", "WORKING"],
      ["ACK", "FOCUS", "WORKING"],
      ["WORKING", "CALL_TOOL", "TOOL_CALL"],
      ["WORKING", "WAIT", "WAITING"],
      ["WORKING", "COLLAB", "COLLABORATING"],
      ["WORKING", "RETURN", "RETURNING"],
      ["WORKING", "BLOCK", "BLOCKED"],
      ["TOOL_CALL", "FOCUS", "WORKING"],
      ["TOOL_CALL", "WAIT", "WAITING"],
      ["TOOL_CALL", "BLOCK", "BLOCKED"],
      ["WAITING", "FOCUS", "WORKING"],
      ["WAITING", "BLOCK", "BLOCKED"],
      ["COLLABORATING", "RETURN", "RETURNING"],
      ["COLLABORATING", "BLOCK", "BLOCKED"],
      ["RETURNING", "RETURN", "DONE"],
      ["BLOCKED", "RECOVER", "RECOVERED"],
      ["RECOVERED", "FOCUS", "WORKING"],
    ];

    it.each(legalCases)(
      "%s + %s → %s",
      (currentState, eventKind, expectedState) => {
        const result = transition(currentState, eventKind);
        expect(result.nextState).toBe(expectedState);
        expect(result.visual.cssClass).toBeTruthy();
      },
    );
  });

  describe("illegal transitions (degradation)", () => {
    it("should warn but accept illegal transition IDLE → RETURNING", () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      const result = transition("IDLE", "RETURN");
      expect(result.nextState).toBe("RETURNING");
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("Illegal transition"),
      );
      warnSpy.mockRestore();
    });

    it("should warn but accept illegal transition DONE → BLOCKED", () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      const result = transition("DONE", "BLOCK");
      expect(result.nextState).toBe("BLOCKED");
      expect(warnSpy).toHaveBeenCalled();
      warnSpy.mockRestore();
    });
  });

  describe("IDLE escape path", () => {
    const allStates: PerceivedAgentState[] = [
      "IDLE", "INCOMING", "ACK", "WORKING", "TOOL_CALL",
      "WAITING", "COLLABORATING", "RETURNING", "DONE",
      "BLOCKED", "RECOVERED",
    ];

    it.each(allStates)(
      "any state (%s) can jump back to IDLE via POLL_HEARTBEAT",
      (state) => {
        const result = transition(state, "POLL_HEARTBEAT");
        expect(result.nextState).toBe("IDLE");
      },
    );

    it.each(allStates)(
      "any state (%s) can jump back to IDLE via BROADCAST_CRON",
      (state) => {
        const result = transition(state, "BROADCAST_CRON");
        expect(result.nextState).toBe("IDLE");
      },
    );
  });

  describe("resetToIdle", () => {
    it("should return IDLE state with no movement", () => {
      const result = resetToIdle();
      expect(result.nextState).toBe("IDLE");
      expect(result.visual.shouldMove).toBe(false);
      expect(result.visual.cssClass).toBe("idle");
    });
  });

  describe("isLegalTransition", () => {
    it("should return true for legal transitions", () => {
      expect(isLegalTransition("IDLE", "INCOMING")).toBe(true);
      expect(isLegalTransition("WORKING", "TOOL_CALL")).toBe(true);
      expect(isLegalTransition("BLOCKED", "RECOVERED")).toBe(true);
    });

    it("should return false for illegal transitions", () => {
      expect(isLegalTransition("IDLE", "DONE")).toBe(false);
      expect(isLegalTransition("DONE", "WORKING")).toBe(false);
    });

    it("should always return true for any → IDLE", () => {
      expect(isLegalTransition("BLOCKED", "IDLE")).toBe(true);
      expect(isLegalTransition("WORKING", "IDLE")).toBe(true);
      expect(isLegalTransition("COLLABORATING", "IDLE")).toBe(true);
    });
  });

  describe("movement triggers", () => {
    it("COLLABORATING should trigger movement for COLLAB event", () => {
      const result = transition("WORKING", "COLLAB");
      expect(result.nextState).toBe("COLLABORATING");
      expect(result.visual.shouldMove).toBe(true);
    });

    it("RETURNING should trigger movement for RETURN event", () => {
      const result = transition("COLLABORATING", "RETURN");
      expect(result.nextState).toBe("RETURNING");
      expect(result.visual.shouldMove).toBe(true);
    });

    it("WORKING should NOT trigger movement for FOCUS event", () => {
      const result = transition("ACK", "FOCUS");
      expect(result.nextState).toBe("WORKING");
      expect(result.visual.shouldMove).toBe(false);
    });

    it("INCOMING should NOT trigger movement for ARRIVE event", () => {
      const result = transition("IDLE", "ARRIVE");
      expect(result.nextState).toBe("INCOMING");
      expect(result.visual.shouldMove).toBe(false);
    });
  });

  describe("same-state transition", () => {
    it("should keep current state when event maps to same state", () => {
      const result = transition("WORKING", "FOCUS");
      expect(result.nextState).toBe("WORKING");
    });
  });

  describe("TRANSITIONS completeness", () => {
    it("should have entries for all 11 states", () => {
      const allStates: PerceivedAgentState[] = [
        "IDLE", "INCOMING", "ACK", "WORKING", "TOOL_CALL",
        "WAITING", "COLLABORATING", "RETURNING", "DONE",
        "BLOCKED", "RECOVERED",
      ];
      for (const state of allStates) {
        expect(TRANSITIONS[state]).toBeDefined();
        expect(TRANSITIONS[state]).toBeInstanceOf(Set);
      }
    });
  });
});
