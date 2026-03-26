import React, { createContext, useContext, useReducer, useCallback, useRef, useEffect } from "react";
import type { ScanResult, ScanStatus } from "@/types/detection";
import { analyzeScan, getWsUrl } from "@/services/api";

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
  | { type: "SET_WS_RESULT"; result: ScanResult }
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
    case "SET_WS_RESULT":
      return { ...state, status: "success", result: action.result, error: null };
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
  sendFrame: (blob: Blob) => void;
}

const ScanContext = createContext<ScanContextType | null>(null);

export function ScanProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(scanReducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (state.isWebcam) {
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            dispatch({ type: "ANALYZE_ERROR", error: data.error });
            return;
          }
          dispatch({ type: "SET_WS_RESULT", result: data as ScanResult });
        } catch (e) {
          console.error("WebSocket message error:", e);
        }
      };

      ws.onerror = () => {
        dispatch({ type: "ANALYZE_ERROR", error: "WebSocket connection error" });
      };

      ws.onclose = () => {
        wsRef.current = null;
      };

      return () => {
        ws.close();
        wsRef.current = null;
      };
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  }, [state.isWebcam]);

  const sendFrame = useCallback((blob: Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(blob);
    }
  }, []);

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
      const detail = err.response?.data?.detail;
      let errorMsg = "Failed to analyze image";
      if (typeof detail === "string") {
        errorMsg = detail;
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(', ');
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      dispatch({ type: "ANALYZE_ERROR", error: errorMsg });
    }
  }, [state.file]);

  return (
    <ScanContext.Provider value={{ ...state, dispatch, analyze, sendFrame }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useScanner() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error("useScanner must be used within ScanProvider");
  return ctx;
}
