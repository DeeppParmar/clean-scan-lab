import React, { createContext, useContext, useReducer, useCallback } from "react";
import type { ScanResult, ScanStatus } from "@/types/detection";
import { analyzeScan } from "@/services/api";

interface ScanState {
  status: ScanStatus;
  file: File | null;
  previewUrl: string | null;
  result: ScanResult | null;
  error: string | null;
  isWebcam: boolean;
}

type ScanAction =
  | { type: "SET_FILE"; file: File; previewUrl: string }
  | { type: "SET_WEBCAM"; active: boolean }
  | { type: "START_ANALYZE" }
  | { type: "ANALYZE_SUCCESS"; result: ScanResult }
  | { type: "ANALYZE_ERROR"; error: string }
  | { type: "RESET" };

const initialState: ScanState = {
  status: "idle",
  file: null,
  previewUrl: null,
  result: null,
  error: null,
  isWebcam: false,
};

function scanReducer(state: ScanState, action: ScanAction): ScanState {
  switch (action.type) {
    case "SET_FILE":
      return { ...state, file: action.file, previewUrl: action.previewUrl, result: null, error: null, status: "idle", isWebcam: false };
    case "SET_WEBCAM":
      return { ...state, isWebcam: action.active, file: null, previewUrl: null, result: null, error: null, status: "idle" };
    case "START_ANALYZE":
      return { ...state, status: "loading", error: null };
    case "ANALYZE_SUCCESS":
      return { ...state, status: "success", result: action.result };
    case "ANALYZE_ERROR":
      return { ...state, status: "error", error: action.error };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

interface ScanContextType extends ScanState {
  dispatch: React.Dispatch<ScanAction>;
  analyze: () => void;
}

const ScanContext = createContext<ScanContextType | null>(null);

export function ScanProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(scanReducer, initialState);

  const analyze = useCallback(async () => {
    if (!state.file) {
      dispatch({ type: "ANALYZE_ERROR", error: "No image file provided." });
      return;
    }
    
    dispatch({ type: "START_ANALYZE" });
    try {
      const result = await analyzeScan(state.file);
      dispatch({ type: "ANALYZE_SUCCESS", result });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "Failed to analyze image";
      dispatch({ type: "ANALYZE_ERROR", error: errorMsg });
    }
  }, [state.file]);

  return (
    <ScanContext.Provider value={{ ...state, dispatch, analyze }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useScanner() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error("useScanner must be used within ScanProvider");
  return ctx;
}
