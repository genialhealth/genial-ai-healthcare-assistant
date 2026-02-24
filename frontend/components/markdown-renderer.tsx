import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  theme?: 'light' | 'dark'; // light = dark text (default), dark = white text
}

export function MarkdownRenderer({ content, className = '', theme = 'light' }: MarkdownRendererProps) {
  const textColor = theme === 'dark' ? 'text-white' : 'text-text-primary';
  const linkColor = theme === 'dark' ? 'text-white' : 'text-navy-900';
  const headerColor = theme === 'dark' ? 'bg-navy-800' : 'bg-background-secondary';

  return (
    <div className={`markdown-content ${textColor} ${className}`}>
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
          ul: ({children}) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
          ol: ({children}) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
          li: ({children}) => <li className="pl-1">{children}</li>,
          strong: ({children}) => <span className="font-semibold">{children}</span>,
          a: ({href, children}) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`underline ${linkColor}`}
            >
              {children}
            </a>
          ),
          table: ({children}) => (
            <div className="overflow-x-auto my-2 rounded-lg border border-border/50">
              <table className="min-w-full divide-y divide-border/50 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({children}) => <thead className={headerColor}>{children}</thead>,
          tbody: ({children}) => <tbody className="divide-y divide-border/50">{children}</tbody>,
          tr: ({children}) => <tr>{children}</tr>,
          th: ({children}) => <th className="px-3 py-2 text-left font-semibold">{children}</th>,
          td: ({children}) => <td className="px-3 py-2">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
