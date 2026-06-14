'use client';

import { useState } from 'react';
import { UploadCloud, FileText, CheckCircle, Send, Bot, User, BarChart3, Database } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

interface Message {
  sender: 'user' | 'ai';
  text: string;
  chartData?: any[]; 
}

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<{ id: number; filename: string; columns: Record<string, string> } | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setMessages([]); 

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/datasets/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to upload file');

      const data = await response.json();
      setUploadSuccess({ 
        id: data.dataset_id, 
        filename: data.filename,
        columns: data.detected_columns 
      });
      
      setMessages([
        { sender: 'ai', text: `Hi there! I've successfully processed **${data.filename}**. Ask me for summaries, tell me to draw charts, or ask follow-up questions!` }
      ]);
    } catch (err: any) {
      setUploadError(err.message || 'Something went wrong during upload. Make sure your backend API allows this file type.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !uploadSuccess || isChatLoading) return;

    const userText = inputMessage;
    setInputMessage('');
    setChatError(null);
    
    const simpleHistory = messages.map((m) => ({
      role: m.sender,
      content: m.text
    }));

    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setIsChatLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: uploadSuccess.id,
          message: userText,
          history: simpleHistory
        }),
      });

      if (!response.ok) throw new Error('Agent engine failed to synthesize response.');

      const data = await response.json();
      
      let aiText = "Sorry, I couldn't process that.";
      let safeChartData = [];

      try {
        const parsedResponse = JSON.parse(data.response);
        aiText = parsedResponse.text_answer || data.response;
        
        if (parsedResponse.chart_data && Array.isArray(parsedResponse.chart_data)) {
          safeChartData = parsedResponse.chart_data.map((item: any) => {
            const keys = Object.keys(item);
            const labelKey = keys.find(k => typeof item[k] === 'string') || keys[0];
            const numberKey = keys.find(k => typeof item[k] === 'number') || keys[1] || keys[0];
            
            return {
              name: String(item.name || item[labelKey] || 'Unknown').substring(0, 15),
              value: Number(item.value || item[numberKey] || 0)
            };
          });
        }
      } catch (e) {
        aiText = data.response;
      }
      
      setMessages((prev) => [...prev, { sender: 'ai', text: aiText, chartData: safeChartData }]);
    } catch (err: any) {
      setChatError(err.message || 'Communication drop with AI brain.');
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <header className="border-b border-slate-200 pb-6">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">AI BI Copilot</h1>
          <p className="text-slate-600 text-lg">Your intelligent data analysis and reasoning workspace.</p>
        </header>

        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-semibold mb-4">1. Dataset Context Layer</h2>
          
          <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 flex flex-col items-center justify-center bg-slate-50 hover:bg-slate-100 transition-colors relative">
            <input 
              type="file" 
              accept=".csv, .xlsx, .xls, .json" 
              onChange={handleFileUpload}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            
            {isUploading ? (
              <div className="flex flex-col items-center animate-pulse">
                <UploadCloud className="w-12 h-12 text-blue-500 mb-3" />
                <p className="text-slate-600 font-medium">Parsing data layout structures...</p>
              </div>
            ) : uploadSuccess ? (
              <div className="flex flex-col items-center text-emerald-600">
                <CheckCircle className="w-10 h-10 mb-2" />
                <p className="font-semibold text-md">Active Context: {uploadSuccess.filename}</p>
                <p className="text-xs text-slate-500 mt-1">Database Registration Reference ID: {uploadSuccess.id}</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <FileText className="w-12 h-12 text-slate-400 mb-2" />
                <p className="text-slate-700 font-medium">Select or drop CSV or Excel (.xlsx) file</p>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-md border border-red-200 text-sm">
              {uploadError}
            </div>
          )}
        </section>

        {uploadSuccess && (
          <section className="bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col h-[650px] overflow-hidden">
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-blue-400" />
                <span className="font-semibold">LangGraph Decision Execution Terminal</span>
              </div>
              <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded border border-emerald-500/30 font-mono">
                CONNECTED
              </span>
            </div>

            <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex items-start space-x-2 max-w-[85%] ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`p-2 rounded-full flex-shrink-0 ${msg.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-800'}`}>
                      {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    
                    <div className="flex flex-col space-y-3 w-full">
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm inline-block ${msg.sender === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white text-slate-800 rounded-tl-none border border-slate-200'}`}>
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      </div>

                      {msg.chartData && msg.chartData.length > 0 && (
                        <div className="w-full bg-white p-4 rounded-xl border border-slate-200 shadow-sm mt-2 flex flex-col">
                          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2">
                            <div className="flex items-center space-x-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                              <BarChart3 className="w-4 h-4 text-blue-500" />
                              <span>Visual Output Generated</span>
                            </div>
                            <div className="flex items-center space-x-1 text-slate-400 text-[10px] font-mono bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                              <Database className="w-3 h-3" />
                              <span>Rows Detected: {msg.chartData.length}</span>
                            </div>
                          </div>
                          
                          <div className="overflow-x-auto pt-2">
                            <BarChart width={650} height={240} data={msg.chartData} margin={{ top: 10, right: 10, left: -10, bottom: 30 }}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 10 }} />
                              <Tooltip cursor={{ fill: '#F8FAFC' }} contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0', fontSize: '12px' }} />
                              <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} maxBarSize={50} />
                            </BarChart>
                          </div>
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              ))}
              
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center space-x-2 bg-white p-3 rounded-2xl border border-slate-200 shadow-sm text-slate-500 text-xs animate-pulse">
                    <Bot className="w-4 h-4 text-blue-500 animate-spin" />
                    <span>AI analyzing context and plotting chart data...</span>
                  </div>
                </div>
              )}

              {chatError && (
                <div className="p-3 bg-red-50 text-red-600 rounded-md border border-red-100 text-xs">
                  {chatError}
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="p-4 bg-white border-t border-slate-200 flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="E.g., 'Draw a chart showing the top 5 customers by Total'"
                disabled={isChatLoading}
                className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
              />
              <button
                type="submit"
                disabled={isChatLoading || !inputMessage.trim()}
                className="bg-blue-600 text-white px-4 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </section>
        )}

      </div>
    </main>
  );
}