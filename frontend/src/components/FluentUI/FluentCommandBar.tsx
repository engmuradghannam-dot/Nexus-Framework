// components/FluentUI/FluentCommandBar.tsx
import { ReactNode } from 'react';
import { ChevronDown, MoreHorizontal } from 'lucide-react';

interface CommandItem {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  split?: boolean;
}

interface FluentCommandBarProps {
  title?: string;
  subtitle?: string;
  commands: CommandItem[];
  breadcrumbs?: { label: string; href?: string }[];
  backButton?: boolean;
  onBack?: () => void;
}

export function FluentCommandBar({ title, subtitle, commands, breadcrumbs, backButton, onBack }: FluentCommandBarProps) {
  return (
    <div className="bg-white border-b border-[#e1dfdd] shadow-sm">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div className="px-5 pt-3 pb-1 flex items-center gap-1 text-sm text-[#605e5c]">
          {backButton && (
            <button onClick={onBack} className="mr-2 p-1 hover:bg-[#f3f2f1] rounded">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          {breadcrumbs.map((crumb, idx) => (
            <span key={idx} className="flex items-center gap-1">
              {idx > 0 && <span className="text-[#a19f9d] mx-1">/</span>}
              {crumb.href ? (
                <a href={crumb.href} className="text-[#0078d4] hover:underline">{crumb.label}</a>
              ) : (
                <span className="text-[#323130]">{crumb.label}</span>
              )}
            </span>
          ))}
        </div>
      )}

      <div className="px-5 py-3 flex items-center justify-between">
        <div>
          {title && <h1 className="text-xl font-semibold text-[#323130]">{title}</h1>}
          {subtitle && <p className="text-sm text-[#605e5c] mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-1">
          {commands.map((cmd) => (
            <div key={cmd.id} className="relative group">
              {cmd.split ? (
                <div className="flex">
                  <button
                    onClick={cmd.onClick}
                    disabled={cmd.disabled}
                    className={`
                      flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-l
                      ${cmd.variant === 'primary' 
                        ? 'bg-[#0078d4] text-white hover:bg-[#106ebe] disabled:bg-[#c8c6c4]' 
                        : cmd.variant === 'danger'
                        ? 'bg-[#d83b01] text-white hover:bg-[#a4262c]'
                        : 'bg-white text-[#323130] border border-[#8a8886] hover:bg-[#f3f2f1] disabled:text-[#a19f9d]'
                      }
                    `}
                  >
                    {cmd.icon && <span className="w-4 h-4">{cmd.icon}</span>}
                    {cmd.label}
                  </button>
                  <button className={`
                    px-1.5 rounded-r border-l-0
                    ${cmd.variant === 'primary' 
                      ? 'bg-[#0078d4] text-white hover:bg-[#106ebe] border border-[#0078d4]' 
                      : 'bg-white text-[#323130] border border-[#8a8886] hover:bg-[#f3f2f1]'
                    }
                  `}>
                    <ChevronDown size={14} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={cmd.onClick}
                  disabled={cmd.disabled}
                  className={`
                    flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded
                    transition-colors duration-150
                    ${cmd.variant === 'primary' 
                      ? 'bg-[#0078d4] text-white hover:bg-[#106ebe] disabled:bg-[#c8c6c4]' 
                      : cmd.variant === 'danger'
                      ? 'bg-[#d83b01] text-white hover:bg-[#a4262c]'
                      : 'bg-white text-[#323130] border border-[#8a8886] hover:bg-[#f3f2f1] disabled:text-[#a19f9d]'
                    }
                  `}
                >
                  {cmd.icon && <span className="w-4 h-4">{cmd.icon}</span>}
                  {cmd.label}
                  <ChevronDown size={14} />
                </button>
              )}
            </div>
          ))}

          <button className="p-1.5 text-[#605e5c] hover:bg-[#f3f2f1] rounded ml-1">
            <MoreHorizontal size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default FluentCommandBar;
