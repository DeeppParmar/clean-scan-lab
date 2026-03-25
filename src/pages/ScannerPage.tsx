import { UploadZone } from "@/components/Scanner/UploadZone";
import { ResultPanel } from "@/components/Scanner/ResultPanel";
import { useScanner } from "@/hooks/useScanner";

export default function ScannerPage() {
  const { result, previewUrl } = useScanner();

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto flex flex-col gap-8 h-full min-h-[calc(100vh-80px)] overflow-x-hidden">
      {/* Top: Scan Zone */}
      <section className="w-full shrink-0">
        <UploadZone />
      </section>

      {/* Bottom: Dedicated Results Dashboard */}
      {result && (
        <section className="w-full flex flex-col animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out pb-12">
          <h2 className="text-xl md:text-2xl font-heading font-bold text-text-primary mb-5 flex items-center gap-3 tracking-wide">
            <span className="w-1.5 h-6 bg-accent-green rounded-full shadow-[0_0_10px_hsl(var(--accent-green))]"></span>
            ANALYSIS OUTPUT
          </h2>
          <ResultPanel result={result} previewUrl={previewUrl} />
        </section>
      )}
    </div>
  );
}
