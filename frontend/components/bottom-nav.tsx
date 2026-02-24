'use client';

import { MessageSquare, FileText, TrendingUp, User } from 'lucide-react';
import { useGenialStore } from '@/lib/store';
import { TabId } from '@/types';

interface NavItem {
  id: TabId;
  label: string;
  icon: typeof MessageSquare;
  hasBadge?: boolean;
}

export function BottomNav() {
  const { activeTab, setActiveTab, unreadReport, unreadDiagnosis } = useGenialStore();

  const navItems: NavItem[] = [
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
    },
    {
      id: 'results',
      label: 'Diseases',
      icon: TrendingUp,
      hasBadge: unreadDiagnosis,
    },
    {
      id: 'report',
      label: 'Evidence',
      icon: FileText,
      hasBadge: unreadReport,
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-xl border-t border-border/50 safe-bottom z-50 shadow-lg">
      <div className="max-w-md mx-auto flex items-center justify-around h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`
                flex flex-col items-center justify-center gap-1 px-6 py-2 
                transition-all duration-300 ease-out relative
                ${isActive ? 'text-navy-900' : 'text-text-tertiary'}
                active:scale-95
              `}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="relative">
                <div className={`
                  relative transition-all duration-300
                  ${isActive ? 'scale-110' : 'scale-100'}
                `}>
                  <Icon
                    className="w-6 h-6 transition-all duration-300"
                    strokeWidth={isActive ? 2.5 : 2}
                  />
                  {item.hasBadge && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 border-2 border-white rounded-full shadow-sm animate-pulse" />
                  )}
                </div>
              </div>
              <span
                className={`
                  text-xs font-medium transition-all duration-300
                  ${isActive ? 'opacity-100 scale-105' : 'opacity-70 scale-100'}
                `}
              >
                {item.label}
              </span>
              {isActive && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-navy-900 rounded-full animate-slide-down" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
