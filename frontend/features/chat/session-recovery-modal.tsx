import { MessageSquare, RotateCcw } from 'lucide-react';

interface SessionRecoveryModalProps {
  onResume: () => void;
  onNewSession: () => void;
}

export function SessionRecoveryModal({ onResume, onNewSession }: SessionRecoveryModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-6 text-center">
          <div className="w-12 h-12 bg-navy-50 text-navy-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-6 h-6" />
          </div>
          
          <h2 className="text-xl font-bold text-navy-900 mb-2">
            Welcome Back
          </h2>
          
          <p className="text-text-secondary text-sm leading-relaxed mb-6">
            We found a previous consultation in progress. Would you like to continue from where you left off?
          </p>

          <div className="space-y-3">
            <button
              onClick={onResume}
              className="w-full py-3 px-4 bg-navy-900 text-white rounded-xl font-medium shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 hover:bg-navy-800"
            >
              Resume Conversation
            </button>
            
            <button
              onClick={onNewSession}
              className="w-full py-3 px-4 bg-white text-text-secondary border border-border rounded-xl font-medium active:scale-95 transition-all flex items-center justify-center gap-2 hover:bg-gray-50"
            >
              <RotateCcw className="w-4 h-4" />
              Start New Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
