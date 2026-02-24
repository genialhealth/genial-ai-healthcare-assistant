'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Info, TrendingUp, Loader2 } from 'lucide-react';
import { Header } from '@/components/header';
import { MessageBubble } from '@/components/message-bubble';
import { useGenialStore } from '@/lib/store';
import { DiseaseChatRequest } from '@/types';
import { getToken, handleUnauthorized } from '@/lib/auth';

interface DiseaseChatViewProps {
  onBack: () => void;
  headerRightElements?: React.ReactNode;
}

// Module-level flag to prevent duplicate fetches when multiple instances of this view mount simultaneously (e.g., responsive layouts)
let currentlyFetchingDiseaseId: string | null = null;

export function DiseaseChatView({ onBack, headerRightElements }: DiseaseChatViewProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const {
    selectedDisease,
    symptoms,
    messages,
    diseaseMessages,
    medicalReport,
    addDiseaseMessage,
  } = useGenialStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [diseaseMessages, streamingMessage]);

  useEffect(() => {
    const fetchInitialAnalysis = async () => {
      if (diseaseMessages.length === 0 && selectedDisease) {
        // Prevent duplicate simultaneous requests from other mounted instances
        if (currentlyFetchingDiseaseId === selectedDisease.id) {
          return;
        }
        
        currentlyFetchingDiseaseId = selectedDisease.id;
        
        try {
          await streamResponse('', []);
        } finally {
          // Clear the flag when done, whether success or failure
          currentlyFetchingDiseaseId = null;
        }
      }
    };

    fetchInitialAnalysis();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const streamResponse = async (userMessage: string, history: any[]) => {
    if (!selectedDisease) return;
    
    setIsLoading(true);
    setStreamingMessage('');

    try {
      const request: DiseaseChatRequest = {
        message: userMessage,
        disease: selectedDisease,
        evidences: medicalReport?.evidences ?? null,
        conversationHistory: history,
      };

      const token = getToken();
      const response = await fetch(`/api/disease-chat`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(request),
        // credentials: 'include'
      });

      if (response.status === 401) {
        window.location.href = '/login';
        return;
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedMessage = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line || !line.startsWith('data:')) continue;

            try {
                const jsonStr = line.replace('data:', '').trim();
                if (!jsonStr) continue;
                
                const event = JSON.parse(jsonStr);
                if (event.content) {
                    accumulatedMessage += event.content;
                    setStreamingMessage(prev => prev + event.content);
                }
            } catch (e) {
                console.error('Error parsing SSE line:', line, e);
            }
        }
      }

      if (accumulatedMessage) {
        addDiseaseMessage({ role: 'assistant', content: accumulatedMessage });
      }

    } catch (error) {
      console.error("Stream error:", error);
      addDiseaseMessage({
        role: 'assistant',
        content: 'I apologize, but I encountered an issue. Please try again.',
      });
    } finally {
      setIsLoading(false);
      setStreamingMessage('');
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 50);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !selectedDisease) return;

    const userMessage = input.trim();
    setInput('');
    addDiseaseMessage({ role: 'user', content: userMessage });
    
    // Focus immediately after sending
    setTimeout(() => {
        textareaRef.current?.focus();
    }, 10);

    await streamResponse(userMessage, diseaseMessages);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!selectedDisease) return null;

  return (
    <div className="flex flex-col h-full">
      <Header title={selectedDisease.name} onBack={onBack} rightElements={headerRightElements} />

      <div className="flex-1 overflow-y-auto px-4 py-4 no-scrollbar">
        <div className="mb-4 p-4 bg-navy-900 bg-opacity-5 rounded-xl border-2 border-navy-900 border-opacity-10">
          <div className="flex items-start gap-3 mb-2">
            <div className="bg-navy-900 p-2 rounded-lg shadow-sm">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-text-primary">
                  Likelihood Match
                </span>
                <span className="text-sm font-semibold text-navy-900">
                  {selectedDisease.likelihood}%
                </span>
              </div>
              <p className="text-sm text-text-secondary">
                {selectedDisease.reason}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2 mt-3 pt-3 border-t border-border">
            <Info className="w-4 h-4 text-text-tertiary flex-shrink-0 mt-0.5" />
            <p className="text-xs text-text-tertiary">
              This is informational only. Always consult a healthcare provider for medical advice.
            </p>
          </div>
        </div>

        {diseaseMessages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {/* Streaming Message Bubble */}
        {(isLoading && streamingMessage) && (
             <MessageBubble 
                message={{
                    id: 'streaming',
                    role: 'assistant',
                    content: streamingMessage,
                    timestamp: Date.now()
                }} 
             />
        )}
        
        {/* Loading Indicator (only if no tokens yet) */}
        {(isLoading && !streamingMessage) && (
          <div className="flex justify-start mb-4">
            <div className="bg-background-secondary rounded-2xl px-4 py-3 border border-border/50">
               <Loader2 className="w-5 h-5 text-navy-900 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border bg-white p-4">
        <div className="max-w-md mx-auto">
          <div className="flex gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about this condition..."
              className="flex-1 resize-none rounded-lg border border-border px-4 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-navy-900 focus:ring-offset-1"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-12 h-12 rounded-lg bg-navy-900 text-white shadow-md active:scale-95 transition-all disabled:opacity-40 disabled:shadow-none"
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
