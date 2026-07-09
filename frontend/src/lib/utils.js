// Utility functions for shadcn/ui compatibility
export function cn(...inputs) {
  return inputs.filter(Boolean).join(' ')
}
