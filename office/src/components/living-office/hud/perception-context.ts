import { createContext, useContext, type RefObject } from "react";
import type { PerceptionEngine } from "@/perception/perception-engine";

export const PerceptionEngineContext = createContext<RefObject<PerceptionEngine | null> | null>(
  null,
);

export function usePerceptionEngine(): PerceptionEngine | null {
  const ref = useContext(PerceptionEngineContext);
  return ref?.current ?? null;
}
