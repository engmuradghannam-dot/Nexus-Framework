// pages/AI/AIPage.tsx
import { useState } from 'react';
import { useChat } from '../../hooks/useChat';
import { 
  Brain, MessageSquare, Sparkles, Zap, Settings, 
  Send, Mic, Image, Paperclip, Bot, User, Clock, BarChart3, TrendingUp 
} from 'lucide-react';

interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model?: string;
}

export default function AIPage() {
  const { sendMessage, isLoading } = useChat();
  const [messages, setMessages] = useState<AIMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'مرحباً! أنا مساعدك الذكي المتقدم. كيف يمكنني مساعدتك في تحليل البيانات أو الإجابة على استفساراتك؟',
      timestamp: new Date(),
      model: 'GPT-4'
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('GPT-4');
  const [showSettings, setShowSettings] = useState(false);
  const [creativity, setCreativity] = useState(70);
  const [maxTokens, setMaxTokens] = useState(2048);

  const models = [
    { id: 'gpt4', name: 'GPT-4', provider: 'OpenAI', icon: Brain },
    { id: 'gpt35', name: 'GPT-3.5', provider: 'OpenAI', icon: Zap },
    { id: 'claude', name: 'Claude 3', provider: 'Anthropic', icon: Sparkles },
    { id: 'gemini', name: 'Gemini Pro', provider: 'Google', icon: Bot },
  ];

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: AIMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    try {
      const response = await sendMessage(input);
      const assistantMsg: AIMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        model: selectedModel
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) { console.error(err); }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-xl"><Brain className="text-purple-600" size={24} /></div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">الذكاء الاصطناعي</h1>
              <p className="text-sm text-gray-500">AI Module — تحليل البيانات والمساعدة الذكية</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500">
              {models.map(m => <option key={m.id} value={m.name}>{m.name} ({m.provider})</option>)}
            </select>
            <button onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-lg transition-colors ${showSettings ? 'bg-purple-100 text-purple-600' : 'text-gray-400 hover:bg-gray-100'}`}>
              <Settings size={20} />
            </button>
          </div>
        </div>
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-50 rounded-xl border grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">درجة الإبداع: {creativity}%</label>
              <input type="range" min="0" max="100" value={creativity} onChange={(e) => setCreativity(parseInt(e.target.value))} className="w-full" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">الحد الأقصى: {maxTokens}</label>
              <input type="range" min="256" max="4096" step="256" value={maxTokens} onChange={(e) => setMaxTokens(parseInt(e.target.value))} className="w-full" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">نمط الرد</label>
              <select className="w-full border rounded-lg px-3 py-2"><option>مفصل</option><option>مختصر</option><option>احترافي</option></select>
            </div>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-purple-600' : 'bg-gradient-to-br from-purple-500 to-pink-500'}`}>
              {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
            </div>
            <div className={`max-w-[70%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`p-4 rounded-2xl ${msg.role === 'user' ? 'bg-purple-600 text-white rounded-tr-none' : 'bg-white border shadow-sm rounded-tl-none'}`}>
                <p className="leading-relaxed">{msg.content}</p>
                {msg.model && <span className="text-xs opacity-70 mt-2 block">{msg.model}</span>}
              </div>
              <span className="text-xs text-gray-400 mt-1 block">{msg.timestamp.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center"><Bot size={20} className="text-white" /></div>
            <div className="bg-white border shadow-sm rounded-2xl rounded-tl-none p-4">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="border-t bg-white p-4">
        <div className="flex items-end gap-2">
          <div className="flex gap-1">
            <button className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"><Paperclip size={20} /></button>
            <button className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"><Mic size={20} /></button>
            <button className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"><Image size={20} /></button>
          </div>
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="اسألني أي شيء..." rows={1}
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
            style={{ minHeight: '48px', maxHeight: '120px' }} />
          <button onClick={handleSend} disabled={isLoading || !input.trim()}
            className="p-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"><Send size={20} /></button>
        </div>
      </div>
    </div>
  );
}
