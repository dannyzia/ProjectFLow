import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  mode: 'scaffold' | 'analyze';
}

export function LoadingState({ mode: _ }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center py-8">
      <Loader2 className="w-5 h-5 text-[#3b82f6] animate-spin" />
    </div>
  );
}
