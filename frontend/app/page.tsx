'use client';

import { useState, useEffect } from 'react';
import { ChatView } from '@/features/chat/chat-view';
import { ReportView } from '@/features/report/report-view';
import { ResultsView } from '@/features/results/results-view';
import { ProfileView } from '@/features/profile/profile-view';
import { DiseaseChatView } from '@/features/disease-chat/disease-chat-view';
import { BottomNav } from '@/components/bottom-nav';
import { Header } from '@/components/header';
import { useGenialStore } from '@/lib/store';
import { User, Plus, MessageSquare, FileText, TrendingUp, X } from 'lucide-react';
import { SessionRecoveryModal } from '@/features/chat/session-recovery-modal';
import { SessionResetModal } from '@/features/chat/session-reset-modal';
import { getToken, handleUnauthorized } from '@/lib/auth';

type View = 'chat' | 'report' | 'results' | 'profile' | 'disease-chat';
const WELCOME_MESSAGE = 'Hi! \n\nShare a **medical image**, a **test result**, or **describe your symptoms**. I\'ll help you find answers about your condition.';

export default function Home() {
  const { activeTab, setActiveTab, selectedDisease, selectDisease, reset, addMessage, setSuggestedActions, updateMedicalReport, messages } = useGenialStore();
  const [currentView, setCurrentView] = useState<View>('chat');
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [mediumTab, setMediumTab] = useState<'disease' | 'evidence'>('disease');
  const [chatSessionKey, setChatSessionKey] = useState(0);

  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [pendingSessionData, setPendingSessionData] = useState<any>(null);

  // Session Recovery Logic
  useEffect(() => {
    const checkSession = async () => {
      if (useGenialStore.getState().messages.length > 0) {
        return;
      }

      const sessionId = sessionStorage.getItem('chat_session_id');
      if (!sessionId) {
        if (useGenialStore.getState().messages.length === 0) {
           addMessage({
            role: 'assistant',
            content: WELCOME_MESSAGE,
          });
        }
        return;
      }

      try {
        const token = getToken();
        const res = await fetch(`/api/session`, {
          headers: { 
            'x-session-id': sessionId,
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
        });

        if (res.status === 401) {
          handleUnauthorized();
          return;
        }

        const data = await res.json();

        if (data.success && data.data && data.data.messages.length > 0) {
          setPendingSessionData(data.data);
          setShowRecoveryModal(true);
        } else {
           if (useGenialStore.getState().messages.length === 0) {
             addMessage({
              role: 'assistant',
              content: WELCOME_MESSAGE,
            });
           }
        }
      } catch (e) {
        console.error("Failed to recover session", e);
      }
    };

    checkSession();
  }, []);

  const handleResumeSession = () => {
    if (pendingSessionData) {
      let restoredMessages = [...pendingSessionData.messages];
      if (restoredMessages.length === 0 || restoredMessages[0].content !== WELCOME_MESSAGE) {
        restoredMessages.unshift({
          id: 'welcome-message',
          role: 'assistant',
          content: WELCOME_MESSAGE,
          timestamp: Date.now()
        });
      }
      useGenialStore.setState({ messages: restoredMessages });
      
      if (pendingSessionData.medicalReport) {
        updateMedicalReport(pendingSessionData.medicalReport);
        if (pendingSessionData.medicalReport.most_likely_disease) {
           const { setDiseases } = useGenialStore.getState();
           setDiseases(pendingSessionData.medicalReport.most_likely_disease);
        }
      }
    }
    setShowRecoveryModal(false);
    setPendingSessionData(null);
  };

  useEffect(() => {
    if (selectedDisease) {
      setCurrentView('disease-chat');
    } else {
      setCurrentView(activeTab);
    }
  }, [selectedDisease, activeTab]);

  const handleBackFromDiseaseChat = () => {
    selectDisease(null);
    setActiveTab('results');
  };

  const showBottomNav = currentView !== 'disease-chat';

  const handleNewSession = () => {
    sessionStorage.removeItem('chat_session_id');
    reset();
    addMessage({
      role: 'assistant',
      content: WELCOME_MESSAGE,
    });
    setSuggestedActions([]);
    setChatSessionKey(prev => prev + 1);
    selectDisease(null);
    setShowResetModal(false);
    setShowRecoveryModal(false);
  };

  const handleResetRequest = () => {
    if (messages.length > 1) {
      setShowResetModal(true);
    } else {
      handleNewSession();
    }
  };

  const ProfileButton = (
    <button 
      onClick={() => setShowProfileModal(true)}
      className="p-2 text-navy-900 hover:bg-background-secondary rounded-full transition-colors active:scale-95"
      aria-label="Profile"
    >
      <User className="w-6 h-6" />
    </button>
  );

  const MobileRightElements = (
    <>
      {messages.length > 1 && (
        <button
          onClick={handleResetRequest}
          className="flex items-center gap-1 p-1.5 px-3 bg-navy-900 text-white hover:bg-navy-800 rounded-full transition-colors active:scale-95 mr-1"
          aria-label="New Session"
          title="Start New Session"
        >
          <Plus className="w-4 h-4" />
          <span className="text-xs font-medium">New Session</span>
        </button>
      )}
      {ProfileButton}
    </>
  );

  return (
    <main className="h-full flex flex-col bg-background-primary">
      {/* Mobile Layout (< md) */}
      <div className="md:hidden flex-col h-full flex">
        <div className={`flex-1 overflow-hidden ${showBottomNav ? 'pb-16' : ''}`}>
          {currentView === 'chat' && <ChatView key={chatSessionKey} headerRightElements={MobileRightElements} />}
          {currentView === 'report' && <ReportView headerRightElements={MobileRightElements} />}
          {currentView === 'results' && <ResultsView headerRightElements={MobileRightElements} />}
          {currentView === 'profile' && <ProfileView />}
          {currentView === 'disease-chat' && (
            <DiseaseChatView onBack={handleBackFromDiseaseChat} headerRightElements={MobileRightElements} />
          )}
        </div>
        {showBottomNav && (
          <BottomNav />
        )}
      </div>

      {/* Desktop Layout (>= md) */}
      <div className="hidden md:flex flex-col h-full">
        {/* Global Header */}
        <Header 
          title="Genial Team Assistant" 
          showLogo 
          rightElements={
            <>
              {messages.length > 1 && (
                <button
                  onClick={handleResetRequest}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-900 text-white hover:bg-navy-800 rounded-full transition-colors active:scale-95 shadow-sm mr-2"
                >
                  <Plus className="w-4 h-4" />
                  <span className="text-sm font-medium">New Session</span>
                </button>
              )}
              {ProfileButton}
            </>
          }
          className="border-b shadow-sm z-20"
        />

        <div className="flex-1 grid md:grid-cols-2 lg:grid-cols-3 overflow-hidden bg-background-secondary/50">
          {/* Col: Disease (Order 1 on LG, Order 2 on MD) */}
          <div className="order-2 lg:order-1 border-r border-border flex flex-col h-full overflow-hidden relative bg-white">
            {/* Medium Screen Switcher */}
            <div className="lg:hidden flex items-center border-b border-border bg-white sticky top-0 z-10">
               <button 
                 onClick={() => setMediumTab('disease')}
                 className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${mediumTab === 'disease' ? 'border-navy-900 text-navy-900' : 'border-transparent text-text-tertiary hover:text-text-primary'}`}
               >
                 <TrendingUp className="w-4 h-4" />
                 Diseases
               </button>
               <button 
                 onClick={() => setMediumTab('evidence')}
                 className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${mediumTab === 'evidence' ? 'border-navy-900 text-navy-900' : 'border-transparent text-text-tertiary hover:text-text-primary'}`}
               >
                 <FileText className="w-4 h-4" />
                 Evidence
               </button>
            </div>

            {/* Disease Panel */}
            <div className={`flex-1 overflow-hidden h-full flex flex-col ${mediumTab === 'disease' ? 'flex' : 'hidden lg:flex'}`}>
               {selectedDisease ? (
                 <DiseaseChatView onBack={() => selectDisease(null)} />
               ) : (
                 <ResultsView />
               )}
            </div>

            {/* Evidence Panel (Medium Screen Only - via switch) */}
            <div className={`flex-1 overflow-hidden h-full flex-col lg:hidden ${mediumTab === 'evidence' ? 'flex' : 'hidden'}`}>
               <ReportView />
            </div>
          </div>

          {/* Col: Chat (Order 1 on MD, Order 2 on LG) */}
          <div className="order-1 lg:order-2 border-r border-border bg-white flex flex-col h-full overflow-hidden shadow-[0_0_24px_-12px_rgba(0,0,0,0.12)] z-10">
            <ChatView key={chatSessionKey} hideHeader={true} />
          </div>

          {/* Col: Evidence (Order 3) */}
          <div className="order-3 hidden lg:flex flex-col h-full overflow-hidden bg-white">
            <ReportView />
          </div>
        </div>
      </div>

      {/* Profile Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 bg-navy-900/40 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div 
            className="bg-white rounded-2xl w-full max-w-md h-[85vh] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <ProfileView onClose={() => setShowProfileModal(false)} />
          </div>
        </div>
      )}

      {/* Session Recovery Modal */}
      {showRecoveryModal && (
        <SessionRecoveryModal 
          onResume={handleResumeSession} 
          onNewSession={handleNewSession} 
        />
      )}

      {/* Session Reset Modal */}
      {showResetModal && (
        <SessionResetModal
          onConfirm={handleNewSession}
          onCancel={() => setShowResetModal(false)}
        />
      )}
    </main>
  );
}
