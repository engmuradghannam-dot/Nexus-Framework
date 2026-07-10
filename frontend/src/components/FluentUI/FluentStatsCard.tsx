// components/FluentUI/FluentStatsCard.tsx
import { ReactNode } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface FluentStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'red' | 'purple';
}

export function FluentStatsCard({ title, value, subtitle, trend, trendValue, icon, color = 'blue' }: FluentStatsCardProps) {
  const colorMap = {
    blue: { bg: 'bg-[#eff6fc]', icon: 'text-[#0078d4]', accent: 'border-l-[#0078d4]' },
    green: { bg: 'bg-[#f3faf3]', icon: 'text-[#107c10]', accent: 'border-l-[#107c10]' },
    orange: { bg: 'bg-[#fff8f0]', icon: 'text-[#d83b01]', accent: 'border-l-[#d83b01]' },
    red: { bg: 'bg-[#fdf2f2]', icon: 'text-[#a4262c]', accent: 'border-l-[#a4262c]' },
    purple: { bg: 'bg-[#f5f0fa]', icon: 'text-[#5c2d91]', accent: 'border-l-[#5c2d91]' },
  };

  const c = colorMap[color];

  return (
    <div className={`
      bg-white border border-[#e1dfdd] rounded-sm shadow-sm
      border-l-4 ${c.accent} p-5
    `}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-[#605e5c]">{title}</p>
          <p className="text-2xl font-bold text-[#323130] mt-1">{value}</p>

          {trend && trendValue && (
            <div className="flex items-center gap-1 mt-2">
              {trend === 'up' && <ArrowUpRight size={16} className="text-[#107c10]" />}
              {trend === 'down' && <ArrowDownRight size={16} className="text-[#d83b01]" />}
              {trend === 'neutral' && <Minus size={16} className="text-[#605e5c]" />}
              <span className={`text-sm font-medium ${
                trend === 'up' ? 'text-[#107c10]' : 
                trend === 'down' ? 'text-[#d83b01]' : 'text-[#605e5c]'
              }`}>
                {trendValue}
              </span>
            </div>
          )}

          {subtitle && !trend && (
            <p className="text-sm text-[#605e5c] mt-1">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div className={`p-2.5 rounded ${c.bg}`}>
            <span className={c.icon}>{icon}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default FluentStatsCard;
