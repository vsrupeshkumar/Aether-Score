'use client';

import { useState, useRef, useEffect } from 'react';
import { ethers } from 'ethers';
import { getApiUrl } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  offer?: any;
  signature?: string;
}

interface ChatConsoleProps {
  address: string | null;
}

export default function ChatConsole({ address }: ChatConsoleProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your NeuroLend AI assistant. I can help you get a personalized loan based on your AETHER-SCORE score. How can I help you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !address || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await fetch(`${getApiUrl()}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address,
          message: userMessage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(errorData.message || errorData.detail || 'Failed to get response');
      }

      const data = await response.json();
      
      // Add assistant response
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: data.response,
          offer: data.offer,
          signature: data.signature,
        }
      ]);
    } catch (error: any) {
      console.error('Error sending message:', error);
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes('fetch')) {
        setMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: 'âŒ Network error: Unable to connect to the server. Please check if the backend is running on ' + getApiUrl(),
          }
        ]);
      } else {
        setMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error.message || 'Please try again.'}`,
          }
        ]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatOffer = (offer: any) => {
    if (!offer) return null;
    
    // Safely convert BigInt values to readable format
    const formatAmount = (value: any): string => {
      if (!value) return '0.00';
      try {
        // Handle BigInt, string, or number
        const bigIntValue = typeof value === 'bigint' 
          ? value 
          : typeof value === 'string' 
            ? BigInt(value) 
            : BigInt(String(value));
        // Use ethers to format (handles BigInt correctly)
        return parseFloat(ethers.formatEther(bigIntValue)).toFixed(2);
      } catch (error) {
        console.error('Error formatting amount:', error);
        return '0.00';
      }
    };
    
    return {
      amount: formatAmount(offer.amount),
      collateral: formatAmount(offer.collateralAmount),
      rate: (Number(offer.interestRate || 0) / 100).toFixed(2),
      duration: Math.floor(Number(offer.duration || 0) / (24 * 60 * 60)),
    };
  };

  return (
    <div className="flex flex-col h-full glass rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-glass-hover">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <h3 className="font-semibold text-white">NeuroLend AI Assistant</h3>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white shadow-lg'
                  : 'glass text-white'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              
              {/* Loan Offer Card */}
              {msg.offer && msg.signature && (
                <div className="mt-4 glass rounded-xl p-4 border border-cyan-500/30 neon-border animate-fade-in">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                    <h4 className="font-semibold text-white">Loan Offer</h4>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary text-sm">Loan Amount</span>
                      <span className="font-mono font-bold text-white text-lg">
                        {formatOffer(msg.offer)?.amount} QIE
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary text-sm">Collateral Required</span>
                      <span className="font-mono font-semibold text-white">
                        {formatOffer(msg.offer)?.collateral} QIE
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary text-sm">Interest Rate</span>
                      <span className="font-mono font-semibold text-green-400">
                        {formatOffer(msg.offer)?.rate}% APR
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-3 border-t border-white/10">
                      <span className="text-text-secondary text-sm">Duration</span>
                      <span className="font-semibold text-white">
                        {formatOffer(msg.offer)?.duration} days
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (window.dispatchEvent) {
                        window.dispatchEvent(new CustomEvent('acceptOffer', {
                          detail: { offer: msg.offer, signature: msg.signature }
                        }));
                      }
                    }}
                    className="mt-4 w-full px-4 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-[1.02]"
                  >
                    Accept Offer
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="glass rounded-2xl p-4">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/10 p-4 bg-glass-hover">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-3 glass rounded-lg text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
            disabled={isLoading || !address}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim() || !address}
            className="btn-gradient px-6 py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

