"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { LearnerDetail } from "@/lib/api/types";

type LearnerSelectionValue = {
  learner: LearnerDetail | null;
  selectLearner: (learner: LearnerDetail | null) => void;
};

const LearnerSelectionContext = createContext<LearnerSelectionValue | null>(null);

export function LearnerSelectionProvider({ children }: { children: ReactNode }) {
  const [learner, selectLearner] = useState<LearnerDetail | null>(null);
  const value = useMemo(() => ({ learner, selectLearner }), [learner]);
  return <LearnerSelectionContext.Provider value={value}>{children}</LearnerSelectionContext.Provider>;
}

export function useLearnerSelection(): LearnerSelectionValue {
  const value = useContext(LearnerSelectionContext);
  if (!value) throw new Error("useLearnerSelection must be used within LearnerSelectionProvider.");
  return value;
}
