import { UploadZone } from "@/components/Scanner/UploadZone";
import { ResultPanel } from "@/components/Scanner/ResultPanel";
import { useScanner } from "@/hooks/useScanner";

export default function ScannerPage() {
  const { result, previewUrl } = useScanner();

  return (
    <div className="p-4 md:p-6 h-full">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-6 h-full min-h-[calc(100vh-80px)]">
        {/* Left: Scan Zone */}
        <section className="flex flex-col min-h-0">
          <UploadZone />
        </section>

        {/* Right: Results */}
        <section className="flex flex-col min-h-0">
          <ResultPanel result={result} previewUrl={previewUrl} />
        </section>
      </div>
    </div>
  );
}
