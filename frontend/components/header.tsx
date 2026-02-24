import { ChevronLeft, Plus, FilePlus } from 'lucide-react';

interface HeaderProps {
  title: string;
  onBack?: () => void;
  onReset?: () => void;
  showLogo?: boolean;
  rightElements?: React.ReactNode;
  className?: string;
}

export function Header({ title, onBack, onReset, showLogo, rightElements, className = '' }: HeaderProps) {
  return (
    <header className={`flex items-center h-14 px-4 border-b border-border bg-white safe-top relative ${className}`}>
      {onBack && (
        <button
          onClick={onBack}
          className="mr-3 p-1 -ml-1 active:opacity-70 transition-opacity"
          aria-label="Go back"
        >
          <ChevronLeft className="w-6 h-6 text-navy-900" />
        </button>
      )}
      {showLogo && (
        <div className="mr-3 w-8 h-8 bg-navy-900 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">G</span>
        </div>
      )}
      <h1 className="text-lg font-semibold text-navy-900 flex-1 truncate">{title}</h1>
      
      <div className="flex items-center gap-2">
        {onReset && (
          <button
            onClick={onReset}
            className="flex items-center gap-1 p-2 bg-navy-900 text-white hover:bg-navy-800 rounded-full transition-colors active:scale-95"
            aria-label="New Session"
            title="Start New Session"
          >
            <Plus className="w-4 h-5" />
            <span className="text-xs">New</span>
          </button>
        )}
        {rightElements}
      </div>
    </header>
  );
}
