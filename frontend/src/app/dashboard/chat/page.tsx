'use client';

import React, { useEffect, useState, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  api,
  ReportItem,
  ChatMessage,
  AIStatus,
  GlossaryItem,
} from '@/lib/api';
import {
  MessageSquare,
  Send,
  Sparkles,
  Bot,
  User,
  Trash2,
  ShieldAlert,
  Globe,
  RefreshCw,
  FileText,
  ChevronRight,
  BookOpen,
  Info,
  CornerDownLeft,
} from 'lucide-react';

function ChatPageContent() {
  const { token, user } = useAuth();
  const searchParams = useSearchParams();
  const initialReportId = searchParams.get('reportId') || '';

  const [reportsList, setReportsList] = useState<ReportItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>(initialReportId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [language, setLanguage] = useState<'en' | 'ta' | 'hi'>('en');
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [suggestedChips, setSuggestedChips] = useState<string[]>([
    'Which values are out of range?',
    'What questions should I ask my doctor?',
    'Explain my report in simple terms',
    'What dietary habits support these results?',
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!token) return;
    const fetchInitial = async () => {
      setLoadingReports(true);
      try {
        const [reps, ai] = await Promise.all([
          api.getReports(token),
          api.getAIStatus(token).catch(() => null),
        ]);
        // Filter completed diagnostic lab reports only
        const completed = reps.filter((r) => r.ocr_status === 'completed' && r.report_type !== 'prescription');
        setReportsList(completed);
        setAiStatus(ai);

        if (!selectedReportId && completed.length > 0) {
          setSelectedReportId(completed[0].id);
        }
      } catch (err) {
        console.error('Failed to load reports:', err);
      } finally {
        setLoadingReports(false);
      }
    };
    fetchInitial();
  }, [token]);

  useEffect(() => {
    if (!token || !selectedReportId) return;

    const fetchHistory = async () => {
      setLoadingHistory(true);
      try {
        const history = await api.getReportChatHistory(token, selectedReportId);
        if (history && history.messages && history.messages.length > 0) {
          setMessages(history.messages);
        } else {
          setMessages([
            {
              role: 'assistant',
              content:
                language === 'ta'
                  ? 'வணக்கம்! உங்கள் மருத்துவ ஆய்வக அறிக்கை பற்றி ஏதேனும் கேள்விகள் இருந்தால் கேளுங்கள்.'
                  : language === 'hi'
                  ? 'नमस्ते! अपनी मेडिकल रिपोर्ट के बारे में कोई भी प्रश्न पूछें।'
                  : 'Hello! I am your medical report assistant. Ask me anything about your lab tests, biomarkers, reference ranges, or questions for your doctor.',
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } catch (err) {
        console.error('Failed to load chat history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [token, selectedReportId, language]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || !token || !selectedReportId || sending) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setSending(true);

    try {
      const response = await api.sendReportChatMessage(token, selectedReportId, {
        message: text,
        language,
      });

      if (response && response.reply) {
        setMessages((prev) => [...prev, response.reply]);
        if (response.suggested_followups && response.suggested_followups.length > 0) {
          setSuggestedChips(response.suggested_followups);
        }
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an issue processing your query. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleClearChat = async () => {
    if (!token || !selectedReportId) return;
    if (confirm('Clear chat conversation history for this report?')) {
      try {
        await api.clearReportChatHistory(token, selectedReportId);
        setMessages([
          {
            role: 'assistant',
            content: 'Conversation history cleared. Ask me any question regarding your lab report.',
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch (err) {
        console.error('Failed to clear chat:', err);
      }
    }
  };

  const selectedReport = reportsList.find((r) => r.id === selectedReportId);

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Breadcrumb & Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Link href="/dashboard" className="hover:text-cyan-400 transition">
            Dashboard
          </Link>
          <ChevronRight className="h-3 w-3" />
          <span className="text-teal-400 font-medium">Ask My Report (Conversational Q&A)</span>
        </div>
        <div className="flex items-center space-x-2">
          {aiStatus?.provider === 'groq' ? (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center space-x-1.5 shadow-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"></span>
              <span>⚡ Groq ({aiStatus.model.includes('/') ? aiStatus.model.split('/')[1] : aiStatus.model})</span>
            </span>
          ) : aiStatus?.available ? (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30 flex items-center space-x-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-400 animate-pulse"></span>
              <span>🦙 Ollama ({aiStatus.model})</span>
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800/80 text-slate-300 border border-slate-700/60 flex items-center space-x-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
              <span>🛡️ Clinical Grounded Engine</span>
            </span>
          )}
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30 flex items-center space-x-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-400 animate-pulse"></span>
            <span>RAG Contextual Chat</span>
          </span>
        </div>
      </div>

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-teal-100 to-cyan-200 bg-clip-text text-transparent flex items-center gap-3">
            <MessageSquare className="h-7 w-7 text-teal-400" />
            Ask My Report
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Multi-turn contextual question answering grounded in your extracted laboratory biomarkers, reference ranges, and medical knowledge base.
          </p>
        </div>

        {/* Report Selector & Language Bar */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedReportId}
            onChange={(e) => setSelectedReportId(e.target.value)}
            disabled={loadingReports || reportsList.length === 0}
            className="bg-slate-900/90 text-white text-xs border border-white/10 rounded-xl px-3 py-2 focus:outline-none focus:border-teal-400"
          >
            {loadingReports ? (
              <option value="">Loading reports...</option>
            ) : reportsList.length === 0 ? (
              <option value="">No completed reports found</option>
            ) : (
              reportsList.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title} ({r.report_date || 'Recent'})
                </option>
              ))
            )}
          </select>

          <div className="inline-flex rounded-xl bg-slate-900/90 p-1 border border-white/10">
            {(['en', 'ta', 'hi'] as const).map((lng) => (
              <button
                key={lng}
                onClick={() => setLanguage(lng)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition uppercase ${
                  language === lng
                    ? 'bg-teal-500 text-slate-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lng}
              </button>
            ))}
          </div>

          <button
            onClick={handleClearChat}
            className="p-2 rounded-xl glass-card hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 border border-white/10 transition"
            title="Clear Chat History"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Chat Box */}
      <div className="glass-card rounded-3xl border border-teal-500/20 bg-gradient-to-b from-slate-950/80 to-[#0a0f1d] flex flex-col h-[600px] overflow-hidden">
        {/* Chat Banner */}
        <div className="px-6 py-3.5 border-b border-white/10 bg-white/[0.02] flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-semibold text-white">
              {selectedReport ? selectedReport.title : 'Active Report Context'}
            </span>
            <span className="text-slate-400">({language.toUpperCase()})</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Model: {aiStatus?.available ? aiStatus.model : 'Grounded Fallback'}
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={idx}
                className={`flex items-start space-x-3 ${
                  isUser ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`h-8 w-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                    isUser
                      ? 'bg-gradient-to-tr from-cyan-500 to-teal-400 text-slate-950'
                      : 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                  }`}
                >
                  {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>

                <div
                  className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed space-y-1.5 ${
                    isUser
                      ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-medium'
                      : 'glass-card bg-slate-900/90 text-slate-200 border border-white/10 whitespace-pre-line'
                  }`}
                >
                  <p>{msg.content}</p>
                  <p
                    className={`text-[9px] font-mono text-right ${
                      isUser ? 'text-slate-900/70' : 'text-slate-500'
                    }`}
                  >
                    {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </p>
                </div>
              </div>
            );
          })}

          {sending && (
            <div className="flex items-start space-x-3">
              <div className="h-8 w-8 rounded-xl bg-teal-500/20 text-teal-300 border border-teal-500/30 flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 animate-pulse" />
              </div>
              <div className="glass-card p-3 rounded-2xl border border-white/10 text-xs text-slate-400 flex items-center space-x-2">
                <RefreshCw className="h-3.5 w-3.5 text-teal-400 animate-spin" />
                <span>Analyzing clinical context & crafting grounded reply...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Follow-up Chips */}
        <div className="px-6 py-2.5 border-t border-white/5 bg-white/[0.01] flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex-shrink-0">
            Suggested:
          </span>
          {suggestedChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(chip)}
              disabled={sending}
              className="px-2.5 py-1 rounded-lg text-[11px] bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/20 whitespace-nowrap transition disabled:opacity-50"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-white/10 bg-slate-950/90 flex items-center gap-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={
              language === 'ta'
                ? 'உங்கள் மருத்துவ அறிக்கை பற்றி கேளுங்கள்...'
                : language === 'hi'
                ? 'अपनी मेडिकल रिपोर्ट के बारे में पूछें...'
                : 'Ask a question about your biomarkers, reference ranges, or doctor questions...'
            }
            disabled={sending || !selectedReportId}
            className="flex-1 bg-slate-900 border border-white/10 rounded-2xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-400 transition"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || sending || !selectedReportId}
            className="p-3 rounded-2xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold shadow-lg shadow-teal-500/20 transition disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <RefreshCw className="h-8 w-8 text-teal-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Ask My Report...</p>
        </div>
      }
    >
      <ChatPageContent />
    </Suspense>
  );
}
