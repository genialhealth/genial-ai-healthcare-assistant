'use client';

import { useState, useEffect } from 'react';
import { Header } from '@/components/header';
import { Card } from '@/components/card';
import { 
  User, 
  Info, 
  Settings, 
  FileText, 
  Shield,
  ChevronRight,
  LogOut,
  X
} from 'lucide-react';
import { handleUnauthorized, isAuthenticated } from '@/lib/auth';
import { useGenialStore } from '@/lib/store';

interface ProfileViewProps {
  onClose?: () => void;
}

export function ProfileView({ onClose }: ProfileViewProps) {
  const [showToast, setShowToast] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { reset } = useGenialStore();
  const isLoggedIn = isAuthenticated();

  useEffect(() => {
    setSessionId(sessionStorage.getItem('chat_session_id'));
  }, []);

  const handleComingSoon = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2500);
  };

  const handleLogout = () => {
    reset();
    sessionStorage.removeItem('chat_session_id');
    handleUnauthorized();
  };

  return (
    <div className="flex flex-col h-full bg-background-primary">
      <Header 
        title="Profile" 
        rightElements={onClose && (
          <button 
            onClick={onClose}
            className="p-2 -mr-2 text-navy-900 hover:bg-background-secondary rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        )}
      />

      <div className="flex-1 overflow-y-auto px-4 py-6 no-scrollbar">
        <Card>
          <div className="flex items-center gap-4 pb-6 border-b border-border">
            <div className="w-16 h-16 rounded-full bg-navy-900 flex items-center justify-center">
              <User className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-navy-900">
                {isLoggedIn ? 'User' : 'Guest User'}
              </h2>
              <p className="text-sm text-text-secondary">
                {isLoggedIn ? 'Logged in' : 'Not logged in'}
              </p>
              {sessionId && (
                <div className="mt-1 inline-block bg-background-secondary px-2 py-0.5 rounded border border-border">
                  <p className="text-[10px] text-text-tertiary font-mono" title={`${sessionId}`}>
                    {sessionId}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-6 space-y-1">
            <button 
              onClick={handleComingSoon}
              className="w-full flex items-center justify-between py-3 px-3 -mx-3 rounded-lg hover:bg-background-secondary transition-colors active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <Info className="w-5 h-5 text-navy-900" />
                <div className="text-left">
                  <p className="font-medium text-navy-900">App Information</p>
                  <p className="text-xs text-text-secondary">Genial v1.0.0</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-text-tertiary" />
            </button>

            <button 
              onClick={handleComingSoon}
              className="w-full flex items-center justify-between py-3 px-3 -mx-3 rounded-lg hover:bg-background-secondary transition-colors active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <Settings className="w-5 h-5 text-navy-900" />
                <div className="text-left">
                  <p className="font-medium text-navy-900">Settings</p>
                  <p className="text-xs text-text-secondary">Preferences and options</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-text-tertiary" />
            </button>

            <button 
              onClick={handleComingSoon}
              className="w-full flex items-center justify-between py-3 px-3 -mx-3 rounded-lg hover:bg-background-secondary transition-colors active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-navy-900" />
                <div className="text-left">
                  <p className="font-medium text-navy-900">Privacy Policy</p>
                  <p className="text-xs text-text-secondary">How we protect your data</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-text-tertiary" />
            </button>

            <button 
              onClick={handleComingSoon}
              className="w-full flex items-center justify-between py-3 px-3 -mx-3 rounded-lg hover:bg-background-secondary transition-colors active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-navy-900" />
                <div className="text-left">
                  <p className="font-medium text-navy-900">Terms of Service</p>
                  <p className="text-xs text-text-secondary">Usage terms and conditions</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-text-tertiary" />
            </button>
            
            {isLoggedIn && (
              <button 
                onClick={handleLogout}
                className="w-full flex items-center justify-between py-3 px-3 -mx-3 mt-4 rounded-lg hover:bg-red-50 transition-colors active:scale-[0.98] border-t border-border"
              >
                <div className="flex items-center gap-3">
                  <LogOut className="w-5 h-5 text-red-600" />
                  <div className="text-left">
                    <p className="font-medium text-red-600">Log Out</p>
                  </div>
                </div>
              </button>
            )}
          </div>
        </Card>

        <Card className="mt-4">
          <div className="text-center py-6">
            <p className="text-sm text-text-secondary mb-4">
              Genial is an informational health assistant
            </p>
            <p className="text-xs text-text-tertiary">
              Not a substitute for professional medical advice
            </p>
          </div>
        </Card>
      </div>

      {showToast && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-fade-in">
          <div className="bg-navy-900 text-white px-6 py-3 rounded-full shadow-lg">
            <p className="text-sm font-medium">Coming Soon</p>
          </div>
        </div>
      )}
    </div>
  );
}


