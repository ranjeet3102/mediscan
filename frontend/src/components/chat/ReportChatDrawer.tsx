'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, ChatMessage, AIStatus, TestResultItem } from '@/lib/api';
import {
  MessageSquare,
  Send,
  X,
  Sparkles,
  Bot,
  User,
  Trash2,
  HelpCircle,
  ShieldAlert,
  Globe,
  RefreshCw,
  CornerDownLeft,
  ChevronRight,
  Activity,
  HeartPulse,
} from 'lucide-react';

interface ReportChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  reportId: string;
  reportTitle: string;
  testResults: TestResultItem[];
  aiStatus: AIStatus | null;
}

export default function ReportChatDrawer({
  isOpen,
  onClose,
  reportId,
  reportTitle,
  testResults,
  aiStatus,
}: ReportChatDrawerProps) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [language, setLanguage] = useState<'en' | 'ta' | 'hi'>('en');
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
    if (isOpen) {
      fetchChatHistory();
    }
  }, [isOpen, reportId, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const fetchChatHistory = async () => {
    setLoadingHistory(true);
    try {
      const activeToken = token || 'dev-user-token';
      const history = await api.getReportChatHistory(activeToken, reportId);
      if (history && history.messages) {
        setMessages(history.messages);
      }
    } catch {
      // Non-blocking
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const messageContent = (textToSend || inputMessage).trim();
    if (!messageContent || sending) return;

    setInputMessage('');
    setSending(true);

    // Optimistically add user message
    const optimisticMsg: ChatMessage = {
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);

    try {
      const activeToken = token || 'dev-user-token';
      const res = await api.sendReportChatMessage(activeToken, reportId, {
        message: messageContent,
        language: language,
      });

      if (res && res.messages) {
        setMessages(res.messages);
      } else if (res && res.reply) {
        setMessages((prev) => [...prev, res.reply]);
      }

      if (res.suggested_followups && res.suggested_followups.length > 0) {
        setSuggestedChips(res.suggested_followups);
      }
    } catch (err: any) {
      // Add error message as assistant response
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to generate response. Please try again.'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleClearChat = async () => {
    if (!confirm('Are you sure you want to clear this conversation history?')) return;
    try {
      const activeToken = token || 'dev-user-token';
      await api.clearReportChatHistory(activeToken, reportId);
      setMessages([]);
      setSuggestedChips([
        'Which values are out of range?',
        'What questions should I ask my doctor?',
        'Explain my report in simple terms',
      ]);
    } catch (err: any) {
      alert(err.message || 'Failed to clear chat.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm transition-all duration-300 animate-fadeIn">
      <div className="w-full max-w-xl h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col justify-between overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/90 backdrop-blur flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/20 text-white">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-1.5">
                  Ask My Report
                </h3>
                <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                  RAG Active
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate max-w-[280px]">
                {reportTitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <div className="flex items-center gap-1 bg-slate-800/80 px-2 py-1 rounded-lg border border-slate-700 text-xs text-slate-300">
              <Globe className="w-3.5 h-3.5 text-teal-400" />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as 'en' | 'ta' | 'hi')}
                className="bg-transparent border-none text-xs text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="en" className="bg-slate-900 text-slate-200">EN</option>
                <option value="ta" className="bg-slate-900 text-slate-200">தமிழ் (TA)</option>
                <option value="hi" className="bg-slate-900 text-slate-200">हिंदी (HI)</option>
              </select>
            </div>

            {/* Clear button */}
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                title="Clear Conversation"
                className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Runtime Status Pill */}
        <div className="bg-slate-950/70 border-b border-slate-800/60 px-4 py-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                aiStatus?.available ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span className="text-slate-400">
              AI Engine:{' '}
              <strong className="text-slate-300 font-medium">
                {aiStatus?.available ? aiStatus.model : 'Deterministic Clinical RAG'}
              </strong>
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            {testResults.length} biomarkers in memory
          </span>
        </div>

        {/* Chat Messages Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loadingHistory ? (
            <div className="flex flex-col items-center justify-center h-48 space-y-3">
              <RefreshCw className="w-6 h-6 text-teal-400 animate-spin" />
              <p className="text-xs text-slate-400">Loading conversation history...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-800/40 to-slate-900/60 border border-slate-800 text-center space-y-4 my-auto">
              <div className="w-12 h-12 rounded-2xl bg-teal-500/10 text-teal-400 flex items-center justify-center mx-auto border border-teal-500/20">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-slate-200">
                  Welcome to Ask My Report
                </h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  I can explain specific test results, highlight abnormal parameters, discuss dietary context, or suggest questions for your physician.
                </p>
              </div>

              <div className="pt-2 text-left space-y-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Suggested Prompts:
                </p>
                <div className="flex flex-col gap-2">
                  {suggestedChips.map((chip, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(chip)}
                      className="text-left text-xs bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-teal-300 px-3.5 py-2.5 rounded-xl border border-slate-700/60 hover:border-teal-500/40 transition-all flex items-center justify-between group"
                    >
                      <span>{chip}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-teal-400 transition-transform group-hover:translate-x-0.5" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        isUser
                          ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                          : 'bg-gradient-to-tr from-teal-500 to-emerald-500 text-white shadow-md shadow-teal-500/20'
                      }`}
                    >
                      {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>

                    {/* Content Box */}
                    <div
                      className={`max-w-[84%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                        isUser
                          ? 'bg-blue-600/20 border border-blue-500/30 text-slate-100'
                          : 'bg-slate-800/80 border border-slate-700/60 text-slate-200'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Cited Biomarker Pills */}
                      {!isUser && msg.sources && msg.sources.length > 0 && (
                        <div className="pt-2 border-t border-slate-700/50 flex flex-wrap items-center gap-1.5 mt-2">
                          <span className="text-[10px] text-slate-400 flex items-center gap-1">
                            <Activity className="w-3 h-3 text-teal-400" /> Cited Tests:
                          </span>
                          {msg.sources.map((src, sIdx) => (
                            <span
                              key={sIdx}
                              className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/30 font-medium"
                            >
                              {src}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Sending / Typing Indicator */}
              {sending && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-teal-500 to-emerald-500 text-white flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl px-4 py-3 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.4s]" />
                    <span className="text-[11px] text-slate-400 ml-2">Consulting report findings & clinical data...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Dynamic Follow-up Prompt Chips (if messages present) */}
        {messages.length > 0 && !sending && suggestedChips.length > 0 && (
          <div className="px-4 py-2 bg-slate-900/60 border-t border-slate-800/50 flex gap-1.5 overflow-x-auto no-scrollbar">
            {suggestedChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(chip)}
                className="text-[11px] whitespace-nowrap bg-slate-800 hover:bg-slate-700/80 text-slate-300 hover:text-teal-300 px-3 py-1.5 rounded-full border border-slate-700 transition-colors shrink-0"
              >
                + {chip}
              </button>
            ))}
          </div>
        )}

        {/* Footer & Input Box */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 backdrop-blur space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 bg-slate-950 border border-slate-700/80 focus-within:border-teal-500/80 rounded-2xl p-1.5 transition-all shadow-inner"
          >
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder={
                language === 'ta'
                  ? 'உங்கள் மருத்துவ அறிக்கை பற்றி கேளுங்கள்...'
                  : language === 'hi'
                  ? 'अपनी मेडिकल रिपोर्ट के बारे में पूछें...'
                  : 'Ask a question about this report (e.g. What does my TSH mean?)...'
              }
              className="flex-1 bg-transparent border-none text-xs text-slate-200 placeholder-slate-500 px-3 py-2 resize-none focus:outline-none max-h-24"
            />

            <button
              type="submit"
              disabled={!inputMessage.trim() || sending}
              className="p-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-semibold transition-all shadow-md shadow-teal-500/20 disabled:shadow-none shrink-0"
            >
              {sending ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>

          {/* Educational Disclaimer */}
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 px-1">
            <ShieldAlert className="w-3 h-3 text-amber-500 shrink-0" />
            <p>
              HealthGuide AI is for health-literacy education only. Always discuss your report with your doctor.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
