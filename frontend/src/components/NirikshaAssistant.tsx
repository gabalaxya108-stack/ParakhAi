import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot, Sparkles, Shield, ChevronRight, RefreshCw, Trash2 } from 'lucide-react';
import { fetchJson } from '../api/client';

interface ChatMessage {
  id: string;
  sender: 'user' | 'niriksha';
  text: string;
  timestamp: string;
  model?: string;
  evidence_used?: any;
}

interface NirikshaAssistantProps {
  currentInspectionId?: string;
}

// Formatter for markdown-like text (bold, headers, lists, code)
const FormattedMessage: React.FC<{ text: string; isUser: boolean }> = ({ text, isUser }) => {
  if (isUser) {
    return <span>{text}</span>;
  }

  const lines = text.split('\n');
  return (
    <div className="space-y-1.5 text-xs leading-relaxed font-sans">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }

        // Headers
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={idx} className="font-bold text-slate-900 dark:text-slate-100 text-xs mt-2 mb-1 border-b border-slate-200 dark:border-slate-800 pb-0.5">
              {renderInlineStyles(trimmed.slice(4))}
            </h4>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h3 key={idx} className="font-bold text-slate-900 dark:text-slate-100 text-sm mt-2 mb-1">
              {renderInlineStyles(trimmed.slice(3))}
            </h3>
          );
        }

        // Bullet points
        if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
          return (
            <div key={idx} className="flex items-start gap-1.5 pl-1.5 my-0.5">
              <span className="text-blue-500 shrink-0 select-none">•</span>
              <span className="text-slate-800 dark:text-slate-200">{renderInlineStyles(trimmed.slice(2))}</span>
            </div>
          );
        }

        // Italic / Disclaimer
        if (trimmed.startsWith('*') && trimmed.endsWith('*') && trimmed.length > 2) {
          return (
            <p key={idx} className="italic text-[10px] text-slate-500 dark:text-slate-400 mt-2 pt-1 border-t border-slate-100 dark:border-slate-800">
              {trimmed.slice(1, -1)}
            </p>
          );
        }

        return (
          <p key={idx} className="text-slate-800 dark:text-slate-200">
            {renderInlineStyles(trimmed)}
          </p>
        );
      })}
    </div>
  );
};

// Helper for bold and inline code
function renderInlineStyles(text: string): React.ReactNode[] {
  // Regex to split by bold **text** or `code`
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-bold text-slate-950 dark:text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[11px] font-mono text-blue-600 dark:text-blue-400">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export const NirikshaAssistant: React.FC<NirikshaAssistantProps> = ({ currentInspectionId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeModel, setActiveModel] = useState<string>('Groq • Qwen-3.8-27B');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'niriksha',
      text: "Namaste, Inspector! I am **NIRIKSHA**, your conversational AI Inspection Assistant on the PARAKH AI platform.\n\nAsk me anything in plain language about active inspections, MRP rules, manufacturer details, unit sale pricing, or Gazette amendments.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      model: 'Groq • Qwen-3.8-27B'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleClearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'niriksha',
        text: "Chat cleared. Ready for your next inquiry, Inspector.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: activeModel
      }
    ]);
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input.trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // Prepare multi-turn history
    const historyPayload = messages
      .filter((m) => m.id !== 'welcome-1')
      .map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setIsLoading(true);

    try {
      const res = await fetchJson<any>('/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          inspection_id: currentInspectionId,
          history: historyPayload
        })
      });

      if (res.model) {
        setActiveModel(res.model);
      }

      const nirikshaMsg: ChatMessage = {
        id: `niriksha-${Date.now()}`,
        sender: 'niriksha',
        text: res.reply || 'No response returned from regulatory engine.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: res.model,
        evidence_used: res.evidence_used
      };

      setMessages((prev) => [...prev, nirikshaMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'niriksha',
          text: `⚠️ Could not connect to assistant engine: ${err.message || 'Network error'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = [
    "What does this rule mean?",
    "Why is this marked for review?",
    "Show me the evidence.",
    "What source supports this requirement?",
    "Explain this inspection.",
    "Why isn't this a confirmed violation?"
  ];

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-full shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 border border-blue-500/40 group"
          title="Open NIRIKSHA Inspection Assistant"
        >
          <div className="relative">
            <Bot className="w-5 h-5 text-blue-300 group-hover:rotate-12 transition-transform duration-300" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full" />
          </div>
          <div className="flex flex-col text-left">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold tracking-wider uppercase">NIRIKSHA</span>
              <span className="px-1.5 py-0.2 bg-emerald-500/30 border border-emerald-400/40 text-[9px] text-emerald-300 rounded font-mono">
                Groq AI
              </span>
            </div>
            <span className="text-[10px] text-blue-200 font-medium">Inspection Assistant</span>
          </div>
        </button>
      )}

      {/* Assistant Modal Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[450px] max-w-[calc(100vw-2rem)] h-[620px] max-h-[calc(100vh-4rem)] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          
          {/* Header Bar */}
          <div className="px-4 py-3 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-blue-600/30 border border-blue-400/30 rounded-xl text-blue-300">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold tracking-wide">NIRIKSHA</h3>
                  <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-mono border border-blue-400/20">
                    {activeModel}
                  </span>
                </div>
                <p className="text-[11px] text-slate-300">Parakh AI Inspection Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleClearChat}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                title="Clear Conversation"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                title="Close Assistant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Active Context Banner */}
          {currentInspectionId && (
            <div className="px-3 py-1.5 bg-blue-50 dark:bg-blue-950/40 border-b border-blue-100 dark:border-blue-900/40 flex items-center justify-between text-[11px] text-blue-900 dark:text-blue-300">
              <span className="flex items-center gap-1 font-medium">
                <Shield className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                Active Context: <code className="font-mono text-[10px] font-bold">{currentInspectionId}</code>
              </span>
              <span className="text-[10px] text-blue-600 dark:text-blue-400 font-semibold">Grounded in DB</span>
            </div>
          )}

          {/* Messages Scroll View */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-slate-50/50 dark:bg-slate-950/50">
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[90%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-br-none shadow-md'
                        : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-none shadow-sm'
                    }`}
                  >
                    <FormattedMessage text={msg.text} isUser={isUser} />

                    <div
                      className={`mt-2 text-[9px] flex items-center justify-end gap-1.5 ${
                        isUser ? 'text-blue-200' : 'text-slate-400'
                      }`}
                    >
                      <span>{msg.timestamp}</span>
                      {!isUser && msg.model && (
                        <span className="font-mono text-[8px] opacity-75">[{msg.model}]</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-center gap-2.5 p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-bl-none text-xs text-slate-600 dark:text-slate-300 max-w-[85%] shadow-sm">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                <span>NIRIKSHA is analyzing regulatory evidence via Groq...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestion Chips */}
          <div className="px-3 py-2 bg-slate-100/70 dark:bg-slate-900/70 border-t border-slate-200 dark:border-slate-800 flex gap-1.5 overflow-x-auto no-scrollbar">
            {suggestions.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip)}
                disabled={isLoading}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[10px] font-medium text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-700 transition"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask NIRIKSHA anything about rules, inspections, gazettes..."
              disabled={isLoading}
              className="flex-1 px-3 py-2 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-xl disabled:opacity-40 disabled:cursor-not-allowed transition shadow"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

        </div>
      )}
    </>
  );
};
