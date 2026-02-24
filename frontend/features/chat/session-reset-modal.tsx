import { AlertCircle } from 'lucide-react';

interface SessionResetModalProps {
  onConfirm: () => void;
  onCancel: () => void;
}

export function SessionResetModal({ onConfirm, onCancel }: SessionResetModalProps) {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-200 border border-white/20">
        <div className="p-6 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <h2 className="text-lg font-semibold text-navy-900 mb-2">Start New Session?</h2>
          <p className="text-text-secondary text-sm leading-relaxed mb-6">
            This will clear your current conversation and the collected evidence. This action cannot be undone.
          </p>
          
          <div className="flex flex-col gap-3">
            <button
              onClick={onConfirm}
              className="w-full py-3 bg-red-600 text-white rounded-xl font-medium active:scale-[0.98] transition-all shadow-sm hover:bg-red-700"
            >
              Start New Session
            </button>
            <button
              onClick={onCancel}
              className="w-full py-3 bg-gray-100 text-navy-900 rounded-xl font-medium active:scale-[0.98] transition-all hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
