import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', className = '', children, ...props }, ref) => {
    const baseStyles =
      'rounded-lg px-6 py-3 font-medium transition-opacity active:opacity-70 disabled:opacity-40 disabled:cursor-not-allowed';

    const variantStyles = {
      primary: 'bg-navy-900 text-white shadow-sm',
      secondary: 'bg-white text-navy-900 border border-navy-900',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
