// components/FluentUI/FluentBadge.tsx
interface FluentBadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'primary';
  size?: 'small' | 'medium';
}

export function FluentBadge({ label, variant = 'neutral', size = 'medium' }: FluentBadgeProps) {
  const variants = {
    success: 'bg-[#f3faf3] text-[#107c10] border-[#107c10]',
    warning: 'bg-[#fff8f0] text-[#d83b01] border-[#d83b01]',
    error: 'bg-[#fdf2f2] text-[#a4262c] border-[#a4262c]',
    info: 'bg-[#eff6fc] text-[#0f6cbd] border-[#0f6cbd]',
    neutral: 'bg-[#f3f2f1] text-[#605e5c] border-[#8a8886]',
    primary: 'bg-[#eff6fc] text-[#0078d4] border-[#0078d4]',
  };

  const sizes = {
    small: 'px-2 py-0.5 text-xs',
    medium: 'px-3 py-1 text-sm',
  };

  return (
    <span className={`
      inline-flex items-center font-medium border rounded
      ${variants[variant]}
      ${sizes[size]}
    `}>
      {label}
    </span>
  );
}

export default FluentBadge;
