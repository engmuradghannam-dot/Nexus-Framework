// components/FluentUI/FluentSearchBox.tsx
import { Search, Dismiss } from 'lucide-react';
import { useState } from 'react';

interface FluentSearchBoxProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  className?: string;
}

export function FluentSearchBox({ placeholder = 'البحث...', value, onChange, onSearch, className = '' }: FluentSearchBoxProps) {
  const [internalValue, setInternalValue] = useState(value || '');
  const currentValue = value !== undefined ? value : internalValue;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (value === undefined) setInternalValue(newValue);
    onChange?.(newValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSearch?.(currentValue);
    }
  };

  const clearSearch = () => {
    if (value === undefined) setInternalValue('');
    onChange?.('');
  };

  return (
    <div className={`relative ${className}`}>
      <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-[#605e5c]" size={16} />
      <input
        type="text"
        value={currentValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="
          w-full pr-9 pl-9 py-2
          bg-[#f3f2f1] border border-transparent
          hover:bg-white hover:border-[#e1dfdd]
          focus:bg-white focus:border-[#0078d4] focus:outline-none focus:ring-1 focus:ring-[#0078d4]
          rounded-sm text-sm text-[#323130]
          transition-all duration-150
        "
      />
      {currentValue && (
        <button
          onClick={clearSearch}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[#605e5c] hover:text-[#323130]"
        >
          <Dismiss size={14} />
        </button>
      )}
    </div>
  );
}

export default FluentSearchBox;
