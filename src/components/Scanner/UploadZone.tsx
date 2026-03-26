import { useCallback, useState, useRef, useEffect } from "react";
import { Upload, Camera, X } from "lucide-react";
import { useScanner } from "@/hooks/useScanner";
import { cn } from "@/lib/utils";
import { DetectionOverlay } from "./DetectionOverlay";

export function UploadZone() {
  const { dispatch, previewUrl, result, status, isWebcam, analyze, error, sendFrame } = useScanner();
  const [isDragging, setIsDragging] = useState(false);
  const [fileInfo, setFileInfo] = useState<{ name: string; size: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isWebcam) {
      navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(stream => {
          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.onloadedmetadata = () => {
              videoRef.current?.play().catch(console.error);
            };
          }
          intervalRef.current = setInterval(() => {
             if (videoRef.current && canvasRef.current) {
               const video = videoRef.current;
               const canvas = canvasRef.current;
               if (video.videoWidth > 0 && video.videoHeight > 0) {
                 canvas.width = video.videoWidth;
                 canvas.height = video.videoHeight;
                 const ctx = canvas.getContext("2d");
                 if (ctx) {
                   ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                   canvas.toBlob((blob) => {
                     if (blob) sendFrame(blob);
                   }, "image/jpeg", 0.7);
                 }
               }
             }
          }, 200);
        })
        .catch(err => {
          console.error("Error accessing webcam:", err);
          dispatch({ type: "ANALYZE_ERROR", error: "Failed to access webcam." });
        });
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [isWebcam, dispatch, sendFrame]);

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
      <div className="flex flex-col gap-4 h-full relative">
        <div className="relative flex-1 bg-bg-surface border border-border rounded-xl overflow-hidden min-h-[45vh] lg:min-h-[500px] shadow-lg">
          {/* Scan line */}
          <div className="absolute inset-0 z-20 pointer-events-none overflow-hidden">
            <div className="w-full h-0.5 bg-accent-green/50 shadow-[0_0_15px_hsl(var(--accent-green))] animate-scan-line" />
          </div>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover absolute inset-0 z-10"
          />
          <canvas ref={canvasRef} className="hidden" />
          
          {/* Real-time WebCam Detections Overlay */}
          <div className="absolute inset-0 z-20 pointer-events-none">
            {result && result.detections && (
              <DetectionOverlay detections={result.detections} />
            )}
          </div>

          <div className="flex items-center justify-center h-full relative z-20 pointer-events-none">
            <div className="text-center space-y-2 mix-blend-difference text-white/80">
              <Camera size={48} className="mx-auto" />
              <p className="text-xs font-mono">Camera feed active</p>
              <div className="inline-flex items-center gap-2 bg-black/60 backdrop-blur-md border border-white/20 px-3 py-1 rounded-full">
                <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
                <span className="text-[10px] font-mono uppercase tracking-tighter">Live Stream</span>
              </div>
            </div>
          </div>
          <button
            onClick={reset}
            className="absolute top-3 right-3 z-30 p-1.5 rounded-md bg-bg-base/60 backdrop-blur text-text-muted hover:text-text-primary transition-colors hover:bg-black/40"
            aria-label="Close webcam"
          >
            <X size={16} />
          </button>
        </div>
        <StatusBar status={status} error={error} latency={null} streaming={true} />
      </div>
    );
  }

  if (previewUrl) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="relative w-full h-full min-h-[300px] flex items-center justify-center p-4 bg-bg-surface border border-border rounded-xl overflow-hidden">
          <img
            src={previewUrl}
            alt="Preview"
            className="max-w-full max-h-[350px] lg:max-h-[400px] object-contain rounded-lg shadow-[0_0_20px_rgba(0,0,0,0.5)]"
          />
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
        <StatusBar status={status} error={error} latency={null} streaming={false} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div
        className={cn(
          "relative flex-1 bg-bg-surface/50 border rounded-xl overflow-hidden flex flex-col items-center justify-center cursor-pointer transition-all duration-300 min-h-[300px] backdrop-blur-sm shadow-inner group",
          isDragging
            ? "border-solid border-accent-green bg-accent-green/10 shadow-[0_0_30px_hsl(var(--accent-green)/0.15)]"
            : "border-dashed border-accent-green/30 hover:border-accent-green/80 hover:bg-accent-green/[0.04]"
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

      <StatusBar status={status} error={error} latency={null} streaming={false} />
    </div>
  );
}

function AnalyzeButton({ status, onAnalyze }: { status: string; onAnalyze: () => void }) {
  return (
    <button
      onClick={onAnalyze}
      disabled={status === "loading"}
      className={cn(
        "w-full py-4 rounded-xl font-heading font-bold text-[13px] tracking-[0.15em] flex items-center justify-center gap-3 transition-all duration-500 overflow-hidden relative group",
        status === "loading"
          ? "bg-accent-green/10 text-accent-green cursor-wait border border-accent-green/20"
          : "bg-gradient-to-r from-accent-green to-accent-blue text-primary-foreground hover:shadow-[0_0_20px_hsl(var(--accent-green)/0.4)] border border-transparent hover:brightness-110 active:scale-[0.98]"
      )}
      style={status !== "loading" ? { animation: "pulse-badge 2s ease-in-out infinite" } : undefined}
      aria-label="Analyze material"
    >
      {/* Glossy overlay effect */}
      <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      <ScanIcon size={18} />
      {status === "loading" ? "ANALYZING..." : "ANALYZE MATERIAL"}
    </button>
  );
}

function ScanIcon({ size }: { size: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" /><path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" /><line x1="7" y1="12" x2="17" y2="12" /></svg>;
}

function StatusBar({ status, error, latency, streaming }: { status: string; error: string | null; latency: number | null, streaming: boolean }) {
  if (status === "error" && error) {
    return <div className="text-xs font-mono text-accent-red px-2">{error}</div>;
  }
  if (streaming) {
    return (
      <div className="flex items-center gap-2 px-2">
        <div className="dot-wave"><span /><span /><span /></div>
        <span className="text-xs font-mono text-accent-green">Streaming...</span>
        {status === "success" && <span className="text-xs font-mono text-text-muted ml-auto font-bold tracking-widest text-[#a855f7]">LIVE DETECTIONS</span>}
      </div>
    );
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
