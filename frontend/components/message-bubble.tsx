import { Message } from '@/types';
import { FileText, ChevronRight, TrendingUp } from 'lucide-react';
import { useGenialStore } from '@/lib/store';
import { MarkdownRenderer } from '@/components/markdown-renderer';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const { setActiveTab } = useGenialStore();

  const imageUrl = message.imageUrl;

  const getLikelihoodColor = (likelihood: number) => {
    if (likelihood >= 70) return 'text-red-700 bg-red-50 border-red-200';
    if (likelihood >= 40) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-blue-700 bg-blue-50 border-blue-200';
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 w-full`}>
      <div
        className={`rounded-2xl px-4 py-3 shadow-sm ${
          isUser
            ? 'max-w-[85%] bg-navy-900 text-white rounded-br-none'
            : 'w-full bg-white border border-border text-text-primary rounded-bl-none'
        }`}
      >
        {imageUrl && (
          <img
            src={imageUrl}
            alt="User uploaded"
            className="max-w-full rounded-lg mb-2 border border-white/20"
          />
        )}
        
        <MarkdownRenderer 
          content={message.content} 
          theme={isUser ? 'dark' : 'light'}
          className="text-[15px] leading-relaxed"
        />

        {!isUser && (message.reportUpdated || message.diagnosisUpdated) && (
          <div className="mt-3 pt-2 border-t border-border space-y-2">
            {message.reportUpdated && (
              <div 
                onClick={() => setActiveTab('report')}
                className="flex items-center gap-1.5 text-navy-900 font-semibold text-xs cursor-pointer hover:underline"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Evidence collected</span>
                <ChevronRight className="w-3 h-3 ml-auto" />
              </div>
            )}
            {message.diagnosisUpdated && (
              <div 
                onClick={() => setActiveTab('results')}
                className="flex flex-col gap-1.5 cursor-pointer group"
              >
                <div className="flex items-center gap-1.5 text-navy-900 font-semibold text-xs">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Possible matches available</span>
                  <ChevronRight className="w-3 h-3 ml-auto group-hover:translate-x-0.5 transition-transform" />
                </div>
                
                {message.updatedDiseases && message.updatedDiseases.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 ml-5">
                    {message.updatedDiseases.map((disease, idx) => (
                      <span 
                        key={idx}
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getLikelihoodColor(disease.likelihood)}`}
                      >
                        {disease.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
