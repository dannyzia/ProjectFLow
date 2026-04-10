import { AlertCircle } from 'lucide-react';

interface ErrorAlertProps {
  message: string;
}

export function ErrorAlert({ message }: ErrorAlertProps) {
  return (
    <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-lg p-4 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-[#ef4444] flex-shrink-0 mt-0.5" />
      <div>
        <p className="text-sm text-[#ef4444] font-medium">Something went wrong</p>
        <p className="text-sm text-[#cbd5e1] mt-1">{message}. Please try again.</p>
      </div>
    </div>
  );
}
