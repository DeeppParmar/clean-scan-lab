import { UploadZone } from "@/components/Scanner/UploadZone";
import { ResultPanel } from "@/components/Scanner/ResultPanel";
import { useScanner } from "@/hooks/useScanner";

export default function ScannerPage() {
  const { result, previewUrl, isWebcam } = useScanner();

  return (
    <div className={`p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto flex gap-6 lg:gap-8 h-full min-h-[calc(100vh-80px)] overflow-x-hidden ${isWebcam && result ? 'flex-col lg:flex-row' : 'flex-col'}`}>
      {/* Top/Left: Scan Zone */}
      <section className={`w-full shrink-0 ${isWebcam && result ? 'lg:w-[45%] xl:w-1/2 lg:sticky lg:top-24 lg:h-[calc(100vh-120px)] z-30' : ''}`}>
        <UploadZone />
      </section>

      {/* Bottom/Right: Dedicated Results Dashboard */}
      {result && (
        <section className={`w-full flex flex-col animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out pb-12 ${isWebcam ? 'lg:w-[55%] xl:w-1/2' : ''}`}>
          {!isWebcam && (
            <h2 className="text-xl md:text-2xl font-heading font-bold text-text-primary mb-5 flex items-center gap-3 tracking-wide">
              <span className="w-1.5 h-6 bg-accent-green rounded-full shadow-[0_0_10px_hsl(var(--accent-green))]"></span>
              ANALYSIS OUTPUT
            </h2>
          )}
          <ResultPanel result={result} previewUrl={previewUrl} />
        </section>
      )}
    </div>
  );
}
