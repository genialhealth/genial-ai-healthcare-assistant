'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/header';
import { Card } from '@/components/card';
import { useGenialStore } from '@/lib/store';
import { 
  AlertCircle, 
  FileText, 
  Activity, 
  Image as ImageIcon,
  CheckCircle2,
  ClipboardList,
  FileDown,
  Loader2
} from 'lucide-react';
import { MarkdownRenderer } from '@/components/markdown-renderer';
import { generateMedicalReportPDF } from '@/utils/pdf-generator';
import { getToken, handleUnauthorized } from '@/lib/auth';

interface ReportViewProps {
  headerRightElements?: React.ReactNode;
}

export function ReportView({ headerRightElements }: ReportViewProps) {
  const { medicalReport, markReportRead } = useGenialStore();
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    markReportRead();
  }, [markReportRead]);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    const sessionId = sessionStorage.getItem('chat_session_id');
    
    if (!sessionId) {
      alert("No active session found.");
      setIsGenerating(false);
      return;
    }

    try {
      const token = getToken();
      const response = await fetch(`/api/report/generate`, {
        headers: { 
          'x-session-id': sessionId,
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        // credentials: 'include'
      });
      
      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        generateMedicalReportPDF(result.data);
      } else {
        alert("Failed to generate report content. Please try again.");
      }
    } catch (error) {
      console.error("Report generation failed:", error);
      alert("An error occurred while generating the report.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (!medicalReport) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Evidence" rightElements={headerRightElements} />
        <div className="flex-1 flex items-center justify-center p-6 text-center">
          <Card className="max-w-xs">
            <AlertCircle className="w-12 h-12 text-text-tertiary mx-auto mb-3" />
            <p className="text-text-secondary">
              No report data collected yet. Describe your symptoms in the chat to build your report.
            </p>
          </Card>
        </div>
      </div>
    );
  }

  const hasEvidences = Object.keys(medicalReport.evidences).length > 0;
  const hasImages = Object.keys(medicalReport.images).length > 0;

  return (
    <div className="flex flex-col h-full bg-background-primary">
      <Header title="Evidence" rightElements={headerRightElements} />

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 pb-24 no-scrollbar">
        
        {/* Action Bar */}
        <div className="flex justify-end">
          <button
            onClick={handleGenerateReport}
            disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-2 bg-navy-900 text-white rounded-lg shadow-md active:scale-95 transition-all disabled:opacity-70 disabled:cursor-not-allowed hover:bg-navy-800"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <FileDown className="w-4 h-4" />
                <span>Download PDF Report</span>
              </>
            )}
          </button>
        </div>

        {/* Summary Section */}
        {medicalReport.summary && (
          <section>
            <div className="flex items-center gap-2 mb-3 text-navy-900">
              <FileText className="w-5 h-5" />
              <h2 className="text-lg font-bold">Situation Summary</h2>
            </div>
            <Card className="bg-white border-l-4 border-l-navy-900">
              <MarkdownRenderer 
                content={medicalReport.summary}
                className="text-text-primary leading-relaxed italic text-[15px]"
              />
            </Card>
          </section>
        )}

        {/* Evidences Section */}
        <section>
          <div className="flex items-center gap-2 mb-3 text-navy-900">
            <ClipboardList className="w-5 h-5" />
            <h2 className="text-lg font-bold">Collected Information</h2>
          </div>
          {!hasEvidences ? (
            <p className="text-text-tertiary text-sm italic px-2">No specific symptoms recorded yet.</p>
          ) : (
            <div className="grid gap-3">
              {Object.entries(medicalReport.evidences).map(([key, value]) => (
                <div 
                  key={key} 
                  className="bg-white border border-border rounded-xl p-4 flex items-start gap-3 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="mt-1 bg-green-50 p-1.5 rounded-full">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-text-tertiary uppercase tracking-wider">{key}</h3>
                    <p className="text-navy-900 font-semibold text-[15px]">{value}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Images Section */}
        {hasImages && (
          <section>
            <div className="flex items-center gap-2 mb-3 text-navy-900">
              <ImageIcon className="w-5 h-5" />
              <h2 className="text-lg font-bold">Visual Analysis</h2>
            </div>
            <div className="space-y-4">
              {Object.entries(medicalReport.images).map(([title, path]) => {
                const analysis = medicalReport.images_analyses[title];
                const imageUrl = `/api/static/${path}`;

                return (
                  <Card key={title} className="overflow-hidden p-0 border-none shadow-md">
                    <div className="bg-navy-900 p-3 flex items-center justify-between">
                      <h3 className="text-white font-bold text-sm truncate pr-4">{title}</h3>
                    </div>
                    <div className="p-4 space-y-4">
                      <div className="relative aspect-video rounded-lg overflow-hidden bg-background-secondary border border-border">
                        <img 
                          src={imageUrl} 
                          alt={title} 
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'https://placehold.co/400x300?text=Image+Not+Found';
                          }}
                        />
                      </div>
                      {analysis ? (
                        <div className="bg-background-secondary rounded-lg p-4 border-l-2 border-l-navy-900">
                          <h4 className="text-[11px] font-bold text-text-tertiary uppercase mb-2">Description</h4>
                          <MarkdownRenderer 
                            content={analysis}
                            className="text-sm text-text-primary leading-relaxed"
                          />
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-text-tertiary italic text-sm py-2">
                          <Activity className="w-4 h-4 animate-pulse" />
                          <span>Analysis in progress...</span>
                        </div>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
