"use client";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { cn } from '@/lib/utils';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div 
      className={cn("text-sm", className)}
      style={{
        color: 'var(--color-text-secondary)',
        lineHeight: '1.8'
      }}
    >
      <style dangerouslySetInnerHTML={{__html: `
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4 {
          font-size: 0.875rem;
          font-weight: 700;
          color: var(--color-text-primary);
          margin-top: 1.25rem;
          margin-bottom: 0.75rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid var(--color-border-light);
        }
        
        .markdown-content p {
          margin-bottom: 1rem;
          line-height: 1.8;
          color: var(--color-text-secondary);
        }
        
        .markdown-content ul,
        .markdown-content ol {
          margin: 1rem 0;
          padding-left: 1.5rem;
        }
        
        .markdown-content li {
          margin-bottom: 0.75rem;
          line-height: 1.8;
          color: var(--color-text-secondary);
        }
        
        /* Remove all default list styling */
        .markdown-content ul,
        .markdown-content ol {
          list-style: none;
        }
        
        /* Only show bullets on innermost ul (no nested ul inside) */
        .markdown-content ul > li:not(:has(ul)):not(:has(ol))::before {
          content: "•";
          color: var(--color-accent-blue);
          font-weight: bold;
          font-size: 1.4em;
          margin-right: 0.5em;
          position: absolute;
          left: -1em;
        }
        
        .markdown-content ul > li {
          position: relative;
        }
        
        /* Only show numbers on innermost ol (no nested ul/ol inside) */
        .markdown-content ol {
          counter-reset: item;
        }
        
        .markdown-content ol > li {
          counter-increment: item;
        }
        
        .markdown-content ol > li:not(:has(ul)):not(:has(ol))::before {
          content: counter(item) ".";
          color: var(--color-accent-blue);
          font-weight: bold;
          margin-right: 0.5em;
          position: absolute;
          left: -1.5em;
        }
        
        .markdown-content strong {
          font-weight: 600;
          color: var(--color-text-primary);
        }
        
        .markdown-content a {
          color: var(--color-accent-blue);
          text-decoration: none;
          font-weight: 500;
        }
        
        .markdown-content a:hover {
          text-decoration: underline;
        }
      `}} />
      
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}