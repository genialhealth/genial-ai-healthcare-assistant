import { LucideIcon } from 'lucide-react';
import { HTMLAttributes } from 'react';

interface IconProps extends HTMLAttributes<HTMLDivElement> {
  icon: LucideIcon;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'danger' | 'warning';
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
};

const variantClasses = {
  default: 'text-text-tertiary',
  primary: 'text-navy-900',
  secondary: 'text-text-secondary',
  success: 'text-green-600',
  danger: 'text-red-600',
  warning: 'text-yellow-600',
};

export function Icon({
  icon: LucideIcon,
  size = 'md',
  variant = 'default',
  className = '',
  ...props
}: IconProps) {
  return (
    <div className={`inline-flex items-center justify-center ${className}`} {...props}>
      <LucideIcon className={`${sizeClasses[size]} ${variantClasses[variant]}`} />
    </div>
  );
}
