import { useCallback, useState, useRef } from "react";
import { Upload, Camera, X } from "lucide-react";
import { useScanner } from "@/hooks/useScanner";
import { cn } from "@/lib/utils";

export function UploadZone() {
  const { dispatch, previewUrl, status, isWebcam, analyze, error } = useScanner();
  const [isDragging, setIsDragging] = useState(false);
  const [fileInfo, setFileInfo] = useState<{ name: string; size: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const url = URL.createObjectURL(file);
      const sizeKb = (file.size / 1024).toFixed(1);
      setFileInfo({ name: file.name, size: `${sizeKb} KB` });
      dispatch({ type: "SET_FILE", file, previewUrl: url });
    },
    [dispatch]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) handleFile(file);
    },
    [handleFile]
  );

  const handleWebcam = () => {
    dispatch({ type: "SET_WEBCAM", active: true });
  };

  const reset = () => {
    dispatch({ type: "RESET" });
    setFileInfo(null);
  };

  if (isWebcam) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="relative flex-1 bg-bg-surface border border-border rounded-xl overflow-hidden min-h-[300px]">
          {/* Scan line */}
          <div className="absolute inset-0 z-20 pointer-events-none overflow-hidden">
            <div className="w-full h-0.5 bg-accent-green/50 shadow-[0_0_15px_hsl(var(--accent-green))] animate-scan-line" />
          </div>
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2">
              <Camera size={48} className="mx-auto text-accent-green/30" />
              <p className="text-xs font-mono text-text-muted">Camera feed active</p>
              <div className="inline-flex items-center gap-2 bg-bg-base/60 backdrop-blur-md border border-border px-3 py-1 rounded-full">
                <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
                <span className="text-[10px] font-mono text-text-muted uppercase tracking-tighter">Live Stream</span>
              </div>
            </div>
          </div>
          <button
            onClick={reset}
            className="absolute top-3 right-3 z-30 p-1.5 rounded-md bg-bg-base/60 backdrop-blur text-text-muted hover:text-text-primary transition-colors"
            aria-label="Close webcam"
          >
            <X size={16} />
          </button>
        </div>
        <AnalyzeButton status={status} onAnalyze={analyze} />
        <StatusBar status={status} error={error} latency={null} />
      </div>
    );
  }

  if (previewUrl) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="relative flex-1 bg-bg-surface border border-border rounded-xl overflow-hidden min-h-[300px]">
          <img src={previewUrl} alt="Uploaded scan" className="w-full h-full object-contain" />
          <button
            onClick={reset}
            className="absolute top-3 right-3 z-30 p-1.5 rounded-md bg-bg-base/60 backdrop-blur text-text-muted hover:text-text-primary transition-colors"
            aria-label="Remove image"
          >
            <X size={16} />
          </button>
          {fileInfo && (
            <div className="absolute bottom-3 left-3 bg-bg-base/70 backdrop-blur-md border border-border px-3 py-1.5 rounded-lg">
              <p className="text-[10px] font-mono text-text-muted">{fileInfo.name} · {fileInfo.size}</p>
            </div>
          )}
        </div>
        <AnalyzeButton status={status} onAnalyze={analyze} />
        <StatusBar status={status} error={error} latency={null} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div
        className={cn(
          "relative flex-1 bg-bg-surface border rounded-xl overflow-hidden flex flex-col items-center justify-center cursor-pointer transition-all duration-300 min-h-[300px]",
          isDragging
            ? "border-solid border-accent-green bg-accent-green/5"
            : "border-dashed border-accent-green/40 hover:border-accent-green hover:bg-accent-green/[0.03]"
        )}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload image for scanning"
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        <Upload size={40} className="text-accent-green/30 mb-4" />
        <p className="font-heading font-semibold text-sm text-text-primary">Drop image here or click to upload</p>
        <p className="text-[11px] font-mono text-text-muted mt-1.5">PNG, JPG, WEBP up to 10MB</p>
      </div>

      <button
        onClick={handleWebcam}
        className="flex items-center justify-center gap-2 px-4 py-3 bg-bg-surface border border-border rounded-lg hover:bg-muted/50 transition-all duration-200 text-text-primary font-heading font-medium text-sm"
        aria-label="Use webcam"
      >
        <Camera size={18} />
        Use Webcam
      </button>

      <StatusBar status={status} error={error} latency={null} />
    </div>
  );
}

function AnalyzeButton({ status, onAnalyze }: { status: string; onAnalyze: () => void }) {
  return (
    <button
      onClick={onAnalyze}
      disabled={status === "loading"}
      className={cn(
        "w-full py-4 rounded-lg font-heading font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200",
        status === "loading"
          ? "bg-accent-green/20 text-accent-green cursor-wait"
          : "bg-accent-green text-primary-foreground hover:brightness-110 active:scale-[0.98]"
      )}
      style={status !== "loading" ? { animation: "pulse-badge 2s ease-in-out infinite" } : undefined}
      aria-label="Analyze material"
    >
      <ScanIcon size={18} />
      {status === "loading" ? "ANALYZING..." : "ANALYZE MATERIAL"}
    </button>
  );
}

function ScanIcon({ size }: { size: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" /><path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" /><line x1="7" y1="12" x2="17" y2="12" /></svg>;
}

function StatusBar({ status, error, latency }: { status: string; error: string | null; latency: number | null }) {
  if (status === "error" && error) {
    return <div className="text-xs font-mono text-accent-red px-2">{error}</div>;
  }
  if (status === "loading") {
    return (
      <div className="flex items-center gap-2 px-2">
        <div className="dot-wave"><span /><span /><span /></div>
        <span className="text-xs font-mono text-text-muted">Analyzing...</span>
      </div>
    );
  }
  if (status === "success" && latency) {
    return <div className="text-xs font-mono text-text-muted px-2">Worker processing · ~{latency}ms</div>;
  }
  return <div className="text-xs font-mono text-text-muted/50 px-2">Ready to scan</div>;
}
