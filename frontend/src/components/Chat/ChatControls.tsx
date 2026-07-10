// components/Chat/ChatControls.tsx
import { useState } from 'react';
import { Send, Settings, Paperclip, Mic, Image, Smile } from 'lucide-react';

interface ChatControlsProps {
  onSendMessage: (message: string, attachments?: File[]) => void;
  onVoiceInput?: () => void;
  disabled?: boolean;
}

export function ChatControls({ onSendMessage, onVoiceInput, disabled }: ChatControlsProps) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [showSettings, setShowSettings] = useState(false);

  const handleSend = () => {
    if (!message.trim() && attachments.length === 0) return;
    onSendMessage(message, attachments);
    setMessage('');
    setAttachments([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachments(Array.from(e.target.files));
    }
  };

  return (
    <div className="border-t bg-white p-4">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex gap-2 mb-3 flex-wrap">
          {attachments.map((file, idx) => (
            <div key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm flex items-center gap-2">
              <Paperclip size={14} />
              {file.name}
              <button 
                onClick={() => setAttachments(prev => prev.filter((_, i) => i !== idx))}
                className="text-blue-400 hover:text-blue-600"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* Action Buttons */}
        <div className="flex gap-1">
          <label className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg cursor-pointer transition-colors">
            <Paperclip size={20} />
            <input type="file" multiple className="hidden" onChange={handleFileChange} />
          </label>
          <button 
            className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            onClick={onVoiceInput}
          >
            <Mic size={20} />
          </button>
          <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
            <Image size={20} />
          </button>
          <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
            <Smile size={20} />
          </button>
        </div>

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="اكتب رسالتك هنا..."
            disabled={disabled}
            rows={1}
            className="w-full border border-gray-200 rounded-xl px-4 py-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
        </div>

        {/* Send & Settings */}
        <div className="flex gap-1">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-3 rounded-xl transition-colors ${showSettings ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'}`}
          >
            <Settings size={20} />
          </button>
          <button
            onClick={handleSend}
            disabled={disabled || (!message.trim() && attachments.length === 0)}
            className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mt-3 p-4 bg-gray-50 rounded-xl border">
          <h4 className="font-semibold text-gray-700 mb-3">إعدادات المحادثة</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">نموذج AI</label>
              <select className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500">
                <option>GPT-4</option>
                <option>GPT-3.5</option>
                <option>Claude</option>
                <option>Gemini</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">درجة الإبداع</label>
              <input type="range" min="0" max="100" className="w-full" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">طول الرد</label>
              <select className="w-full border rounded-lg px-3 py-2">
                <option>قصير</option>
                <option>متوسط</option>
                <option>مفصل</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
