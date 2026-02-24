/**
 * ChatView Component
 * 
 * The primary interface for interacting with the Genial Team Assistant.
 * Handles real-time messaging, file uploads (medical images/reports), 
 * and processes streaming AI responses via Server-Sent Events (SSE).
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Image as ImageIcon, X, Loader2 } from 'lucide-react';
import { Header } from '@/components/header';
import { Button } from '@/components/button';
import { MessageBubble } from '@/components/message-bubble';
import { useGenialStore } from '@/lib/store';
import { ChatRequest, ApiResponse, ChatResponse } from '@/types';
import { getToken, handleUnauthorized } from '@/lib/auth';

const WELCOME_MESSAGE = 'Hi! \n\nShare a **medical image**, a **test result**, or **describe your symptoms**. I\'ll help you find answers about your condition.';

interface ChatViewProps {
  /** Whether to hide the default page header */
  hideHeader?: boolean;
  /** Optional React nodes to render on the right side of the header */
  headerRightElements?: React.ReactNode;
}

export function ChatView({ hideHeader = false, headerRightElements }: ChatViewProps) {
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { 
    messages, 
    chatIsLoading, 
    chatStreamingMessage,
    suggestedActions,
    addMessage, 
    addSymptom, 
    updateMedicalReport,
    setChatLoading,
    setChatStreamingMessage,
    setSuggestedActions,
    reset
  } = useGenialStore();

  // Automatically scroll to bottom when new messages arrive or streaming content updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatStreamingMessage]);

  /**
   * Validates and processes an uploaded image file.
   * Generates a base64 preview for the UI.
   */
  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      alert('Image must be less than 20MB');
      return;
    }
    setSelectedImage(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    };
    reader.readAsDataURL(file);
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!chatIsLoading) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (chatIsLoading) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  /**
   * Clears the current image selection and preview.
   */
  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  /**
   * Primary function to send a message to the backend.
   * Handles session management and SSE stream consumption.
   * 
   * @param overrideMessage - Optional string to send instead of the current input value (used for suggested actions).
   */
  const handleSend = async (overrideMessage?: string) => {
    const currentInput = overrideMessage || input;
    if ((!currentInput.trim() && !selectedImage) || chatIsLoading) return;

    const userMessage = currentInput.trim() || 'Image sent';
    setInput('');
    setSuggestedActions([]);
    setChatStreamingMessage(''); 
    let turnHasReportUpdate = false;
    let turnHasDiagnosisUpdate = false;
    let currentTurnDiseases: { name: string; likelihood: number }[] = [];
    
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 10);
    
    let imageBase64: string | undefined;
    if (selectedImage && imagePreview) {
      imageBase64 = imagePreview.split(',')[1];
      addMessage({ 
        role: 'user', 
        content: userMessage,
        imageUrl: imagePreview
      });
    } else {
      addMessage({ role: 'user', content: userMessage });
    }
    
    clearImage();
    setChatLoading(true);

    try {
      const request: ChatRequest = {
        message: userMessage,
        imageBase64,
      };

      // Session persistence logic
      let sessionId = sessionStorage.getItem('chat_session_id');
      if (!sessionId) {
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            sessionId = crypto.randomUUID();
        } else {
            sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        sessionStorage.setItem('chat_session_id', sessionId);
      }

      const token = getToken();
      const response = await fetch(`/api/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-session-id': sessionId,
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(request),
      });

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported in this browser.');
      }

      // Consuming the SSE Stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

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
            
            // Process different SSE event types
            if (event.type === 'progress') {
              setChatStreamingMessage(event.payload.message);
            } else if (event.type === 'report_update') {
              updateMedicalReport(event.payload);
              turnHasReportUpdate = true;
            } else if (event.type === 'diagnosis_update') {
              const { setDiseases } = useGenialStore.getState();
              setDiseases(event.payload.diseases);
              turnHasDiagnosisUpdate = true;
              currentTurnDiseases = event.payload.diseases.map((d: any) => ({
                name: d.name,
                likelihood: d.likelihood
              }));
            } else if (event.type === 'result') {
              addMessage({ 
                role: 'assistant', 
                content: event.payload.message,
                reportUpdated: turnHasReportUpdate,
                diagnosisUpdated: turnHasDiagnosisUpdate,
                updatedDiseases: currentTurnDiseases
              });
              
              if (event.payload.suggestedActions) {
                setSuggestedActions(event.payload.suggestedActions);
              }

              if (event.payload.extractedSymptoms) {
                event.payload.extractedSymptoms.forEach((symptom: any) => {
                  addSymptom(symptom);
                });
              }
            } else if (event.type === 'error') {
               console.error('Agent Error Event:', event.payload.message);
               throw new Error(event.payload.message);
            }
          } catch (e) {
            console.error('Error parsing SSE event line:', line, e);
          }
        }
      }

    } catch (error: any) {
      console.error('Chat Error:', error);
      addMessage({
        role: 'assistant',
        content: error?.message || 'I apologize, but I encountered an issue. Please try again.',
      });
    } finally {
      setChatLoading(false);
      setChatStreamingMessage('');
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 10);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      {!hideHeader && (
        <Header 
          title="Genial Team Assistant" 
          showLogo 
          rightElements={headerRightElements}
        />
      )}

      <div 
        className="flex-1 overflow-y-auto px-4 py-4 no-scrollbar relative"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-navy-50/80 backdrop-blur-sm border-2 border-dashed border-navy-900 m-4 rounded-xl transition-all duration-200 animate-in fade-in zoom-in-95">
            <div className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl shadow-lg">
              <div className="p-3 bg-navy-50 rounded-full">
                <ImageIcon className="w-8 h-8 text-navy-900" />
              </div>
              <div className="text-center">
                <h3 className="font-bold text-navy-900">Drop Image Here</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Upload medical image or report
                </p>
              </div>
            </div>
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {chatIsLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-background-secondary rounded-2xl px-4 py-3 flex items-center gap-3 shadow-sm border border-border/50">
              <Loader2 className="w-5 h-5 text-navy-900 animate-spin" />
              <span className="text-[15px] text-text-primary animate-pulse transition-all duration-300">
                {chatStreamingMessage || 'Thinking...'}
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border bg-white p-4">
        {/* Suggested Actions Row */}
        {!chatIsLoading && suggestedActions.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {suggestedActions.map((action, i) => (
              <button
                key={i}
                onClick={() => handleSend(action)}
                className="px-4 py-2 bg-navy-50 text-navy-900 text-sm font-medium rounded-full border border-navy-100 shadow-sm active:scale-95 transition-all hover:bg-navy-100"
              >
                {action}
              </button>
            ))}
          </div>
        )}

        {imagePreview && (
          <div className="mb-3 relative inline-block">
            <img
              src={imagePreview}
              alt="Preview"
              className="h-24 w-24 object-cover rounded-lg border-2 border-navy-900"
            />
            <button
              onClick={clearImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center shadow-md"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={chatIsLoading}
            className="flex items-center justify-center w-12 h-12 rounded-lg border-2 border-navy-900 text-navy-900 active:scale-95 transition-all disabled:opacity-40"
            aria-label="Upload image"
          >
            <ImageIcon className="w-5 h-5" />
          </button>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (suggestedActions.length > 0) setSuggestedActions([]);
            }}
            onKeyDown={handleKeyPress}
            placeholder="Describe your symptoms..."
            className="flex-1 resize-none rounded-lg border border-border px-4 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-navy-900 focus:ring-offset-1"
            rows={1}
            disabled={chatIsLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={(!input.trim() && !selectedImage) || chatIsLoading}
            className="flex items-center justify-center w-12 h-12 rounded-lg bg-navy-900 text-white shadow-md active:scale-95 transition-all disabled:opacity-40 disabled:shadow-none"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
