// components/FluentUI/FluentCard.tsx
import { ReactNode } from 'react';

interface FluentCardProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  padding?: 'none' | 'small' | 'medium' | 'large';
  shadow?: 'none' | 'small' | 'medium';
  border?: boolean;
}

export function FluentCard({ children, title, subtitle, className = '', padding = 'medium', shadow = 'small', border = true }: FluentCardProps) {
  const paddingMap = {
    none: '',
    small: 'p-3',
    medium: 'p-5',
    large: 'p-6',
  };

  const shadowMap = {
    none: '',
    small: 'shadow-sm',
    medium: 'shadow-md',
  };

  return (
    <div className={`
      bg-white rounded-sm
      ${border ? 'border border-[#e1dfdd]' : ''}
      ${shadowMap[shadow]}
      ${className}
    `}>
      {(title || subtitle) && (
        <div className={`${paddingMap[padding]} pb-0 mb-4`}>
          {title && <h3 className="text-base font-semibold text-[#323130]">{title}</h3>}
          {subtitle && <p className="text-sm text-[#605e5c] mt-1">{subtitle}</p>}
        </div>
      )}
      <div className={paddingMap[padding]}>
        {children}
      </div>
    </div>
  );
}

export default FluentCard;
