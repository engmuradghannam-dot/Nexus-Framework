// components/FluentUI/FluentPanel.tsx
import { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

interface FluentPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  width?: 'small' | 'medium' | 'large';
  footer?: ReactNode;
}

export function FluentPanel({ isOpen, onClose, title, subtitle, children, width = 'medium', footer }: FluentPanelProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  const widthMap = {
    small: 'w-[400px]',
    medium: 'w-[500px]',
    large: 'w-[640px]',
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`
        absolute right-0 top-0 h-full bg-white shadow-2xl
        ${widthMap[width]}
        flex flex-col
        animate-in slide-in-from-right duration-200
      `}>
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#e1dfdd] flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-[#323130]">{title}</h2>
            {subtitle && <p className="text-sm text-[#605e5c]">{subtitle}</p>}
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-[#605e5c] hover:bg-[#f3f2f1] rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-5 py-4 border-t border-[#e1dfdd] bg-[#faf9f8]">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export default FluentPanel;
