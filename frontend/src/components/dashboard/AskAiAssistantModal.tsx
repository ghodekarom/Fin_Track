"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  Send,
  X,
  Bot,
  User,
  Loader2,
  HelpCircle,
  TrendingUp,
  CreditCard,
  PieChart,
  ShieldCheck,
  ChevronRight,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { AskAiQueryRequest, AskAiQueryResponse, ChatMessage } from "@/types/ai";

interface AskAiAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEFAULT_PROMPT_CHIPS = [
  "How much budget do I have left?",
  "Where did most of my money go this month?",
  "Can I afford a ₹5,000 gadget?",
  "What are my active subscriptions?",
  "What was my biggest expense this month?",
  "How much did I spend on Food & Dining?",
];

export default function AskAiAssistantModal({ isOpen, onClose }: AskAiAssistantModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "**Hello! I'm your FinTrack AI Assistant.** 🤖\n\nI have access to your personal expense ledger, monthly budgets, and spending history. Ask me anything in plain English about your finances!",
      suggested_followups: [
        "How much budget do I have left?",
        "Where did most of my money go this month?",
        "Can I afford a ₹5,000 purchase?",
      ],
      provider: "FinTrack Engine",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (!isOpen) return null;

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText || inputValue).trim();
    if (!textToSend || isLoading) return;

    const userMessage: ChatMessage = {
      id: String(Date.now()),
      role: "user",
      content: textToSend,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const historyPayload = messages
        .filter((m) => m.id !== "welcome")
        .slice(-4)
        .map((m) => ({ role: m.role, content: m.content }));

      const payload: AskAiQueryRequest = {
        question: textToSend,
        history: historyPayload,
      };

      const res = await apiClient.post<AskAiQueryResponse>("/ai/ask", payload);

      const assistantMessage: ChatMessage = {
        id: String(Date.now() + 1),
        role: "assistant",
        content: res.data.answer,
        timestamp: new Date().toISOString(),
        suggested_followups: res.data.suggested_followups,
        provider: res.data.provider,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: String(Date.now() + 1),
        role: "assistant",
        content:
          "⚠️ **Sorry, I encountered an issue retrieving your answer.** Please check your connection and try again.",
        timestamp: new Date().toISOString(),
        provider: "System",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to format simple markdown (bold, bullet points, headers) into JSX
  const renderFormattedContent = (content: string) => {
    const lines = content.split("\n");
    return (
      <div className="space-y-1.5 text-xs leading-relaxed text-foreground/90">
        {lines.map((line, idx) => {
          if (line.startsWith("### ")) {
            return (
              <h4 key={idx} className="font-bold text-sm text-cyan-300 mt-2 mb-1">
                {line.replace("### ", "")}
              </h4>
            );
          }
          if (line.startsWith("## ")) {
            return (
              <h3 key={idx} className="font-bold text-base text-cyan-200 mt-2 mb-1">
                {line.replace("## ", "")}
              </h3>
            );
          }
          if (line.startsWith("- ")) {
            const bulletText = line.replace("- ", "");
            return (
              <div key={idx} className="flex items-start gap-1.5 ml-1">
                <span className="text-cyan-400 mt-1 text-[8px]">•</span>
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(bulletText) }} />
              </div>
            );
          }
          if (line.trim() === "") {
            return <div key={idx} className="h-1" />;
          }
          return (
            <p
              key={idx}
              dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(line) }}
            />
          );
        })}
      </div>
    );
  };

  const formatInlineMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-foreground'>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em class='italic text-muted-foreground'>$1</em>");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-background/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl h-[85vh] max-h-[750px] bg-card/95 border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-2xl">
        {/* Glow accents */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-400 shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-foreground tracking-tight">
                  Ask FinTrack AI
                </h3>
                <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Live Ledger
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Private & grounded strictly in your personal financial records
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/10 transition-colors cursor-pointer"
            title="Close Assistant"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Chat Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          {messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={msg.id || index}
                className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-4 transition-all shadow-sm ${
                    isUser
                      ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-tr-sm ml-auto"
                      : "bg-background/80 border border-white/10 rounded-tl-sm backdrop-blur-md"
                  }`}
                >
                  {isUser ? (
                    <p className="text-xs font-medium leading-relaxed">{msg.content}</p>
                  ) : (
                    <>
                      {renderFormattedContent(msg.content)}

                      {/* Suggested Followups */}
                      {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                            Suggested Follow-ups
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.suggested_followups.map((chip, chipIdx) => (
                              <button
                                key={chipIdx}
                                onClick={() => handleSendMessage(chip)}
                                className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-300 border border-cyan-500/20 hover:border-cyan-500/40 transition-all text-left cursor-pointer flex items-center gap-1"
                              >
                                <span>{chip}</span>
                                <ChevronRight className="w-3 h-3 text-cyan-400/60" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Provider pill */}
                      {msg.provider && (
                        <div className="mt-2 text-right">
                          <span className="text-[9px] text-muted-foreground/60 uppercase tracking-widest">
                            {msg.provider}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-300 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator Bubble */}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-background/80 border border-white/10 rounded-2xl rounded-tl-sm p-4 backdrop-blur-md flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                <span className="text-xs text-muted-foreground">
                  Analyzing your ledger and calculating numbers...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-3 sm:p-4 border-t border-white/10 bg-background/50">
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/20 transition-all">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your expenses, budgets, or savings..."
              disabled={isLoading}
              className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground focus:outline-none py-1.5"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputValue.trim()}
              className="p-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-zinc-950 disabled:opacity-40 disabled:hover:bg-cyan-500 transition-all cursor-pointer shadow-sm"
              title="Send question"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-muted-foreground">
            <span>Press Enter to send</span>
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-400" /> Isolated to your account
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
