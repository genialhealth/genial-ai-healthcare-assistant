/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0B1F3A',
          800: '#0F2A4A',
          700: '#132F55',
        },
        background: {
          primary: '#FFFFFF',
          secondary: '#F7F9FC',
        },
        text: {
          primary: '#0A0A0A',
          secondary: '#3A3A3A',
          tertiary: '#6B7280',
        },
        border: {
          DEFAULT: '#E5E7EB',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          50: '#fefce8',
          100: '#fef9c3',
          500: '#eab308',
          600: '#ca8a04',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      maxWidth: {
        mobile: '428px',
      },
      screens: {
        xs: '375px',
        sm: '428px',
      },
    },
  },
  plugins: [],
};
