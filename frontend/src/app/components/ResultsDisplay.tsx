import { CheckCircle2 } from 'lucide-react';

interface ResultsDisplayProps {
  filesWritten: string[];
  outputPath: string;
  onGenerateAnother: () => void;
  onOpenFolder: () => void;
}

export function ResultsDisplay({ onGenerateAnother }: ResultsDisplayProps) {
  return (
    <div className="bg-[#1e293b] rounded-[12px] p-8 border border-gray-700 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-[#22c55e]/10 rounded-full mb-4">
        <CheckCircle2 className="w-8 h-8 text-[#22c55e]" />
      </div>
      <h2 className="text-2xl font-semibold text-white mb-2">All done!</h2>
      <p className="text-[#cbd5e1] mb-8">Your config files have been generated.</p>
      <button
        onClick={onGenerateAnother}
        className="bg-[#334155] hover:bg-[#475569] text-white px-8 py-3 rounded-lg font-medium transition-colors"
      >
        Start Over
      </button>
    </div>
  );
}
