// components/FluentUI/FluentFormField.tsx
import { ReactNode } from 'react';

interface FluentFormFieldProps {
  label: string;
  required?: boolean;
  children: ReactNode;
  hint?: string;
  error?: string;
}

export function FluentFormField({ label, required, children, hint, error }: FluentFormFieldProps) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-[#323130] mb-1.5">
        {label}
        {required && <span className="text-[#d83b01] mr-1">*</span>}
      </label>
      {children}
      {hint && !error && <p className="mt-1 text-xs text-[#605e5c]">{hint}</p>}
      {error && <p className="mt-1 text-xs text-[#d83b01]">{error}</p>}
    </div>
  );
}

export function FluentInput({ className = '', ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`
        w-full px-3 py-2
        bg-[#f3f2f1] border border-transparent
        hover:bg-white hover:border-[#e1dfdd]
        focus:bg-white focus:border-[#0078d4] focus:outline-none focus:ring-1 focus:ring-[#0078d4]
        rounded-sm text-sm text-[#323130]
        transition-all duration-150
        disabled:bg-[#f3f2f1] disabled:text-[#a19f9d]
        ${className}
      `}
      {...props}
    />
  );
}

export function FluentSelect({ className = '', children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`
        w-full px-3 py-2
        bg-[#f3f2f1] border border-transparent
        hover:bg-white hover:border-[#e1dfdd]
        focus:bg-white focus:border-[#0078d4] focus:outline-none focus:ring-1 focus:ring-[#0078d4]
        rounded-sm text-sm text-[#323130]
        transition-all duration-150
        ${className}
      `}
      {...props}
    >
      {children}
    </select>
  );
}

export function FluentTextArea({ className = '', ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`
        w-full px-3 py-2
        bg-[#f3f2f1] border border-transparent
        hover:bg-white hover:border-[#e1dfdd]
        focus:bg-white focus:border-[#0078d4] focus:outline-none focus:ring-1 focus:ring-[#0078d4]
        rounded-sm text-sm text-[#323130]
        transition-all duration-150
        resize-vertical
        ${className}
      `}
      {...props}
    />
  );
}

export default FluentFormField;
