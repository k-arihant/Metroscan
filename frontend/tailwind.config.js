/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gov: {
          blue: '#1A5276',
          dark: '#0B3C5D',
          navy: '#152744',
          saffron: '#F39C12',
          saffronLight: '#F5B942',
          green: '#27AE60',
          red: '#C0392B',
          amber: '#F1C40F',
          canvas: '#F8F9FA',
        },
        brand: {
          50: '#EBF5FB',
          100: '#D6EAF8',
          500: '#1A5276',
          600: '#154360',
          700: '#0B3C5D',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'spin-slow': 'spin 8s linear infinite',
        'spin-reverse': 'spin-reverse 12s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'scan-line': 'scan-line 2.5s ease-in-out infinite',
        'blink': 'blink 1.5s ease-in-out infinite',
        'slide-in-up': 'slide-in-up 0.5s ease-out',
        'fade-in': 'fade-in 0.4s ease-out',
        'star-rotate': 'star-rotate 8s linear infinite',
        'bounce-in': 'bounce-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'shimmer': 'shimmer 2s infinite',
        'confetti-fall': 'confetti-fall 2s ease-in forwards',
      },
      keyframes: {
        'spin-reverse': {
          from: { transform: 'rotate(360deg)' },
          to: { transform: 'rotate(0deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 8px rgba(26,82,118,0.4)' },
          '50%': { boxShadow: '0 0 24px rgba(26,82,118,0.8)' },
        },
        'scan-line': {
          '0%': { top: '0%', opacity: 1 },
          '50%': { top: '100%', opacity: 0.6 },
          '100%': { top: '0%', opacity: 1 },
        },
        blink: {
          '0%, 90%, 100%': { scaleY: 1 },
          '95%': { scaleY: 0.05 },
        },
        'slide-in-up': {
          from: { transform: 'translateY(24px)', opacity: 0 },
          to: { transform: 'translateY(0)', opacity: 1 },
        },
        'fade-in': {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },
        'star-rotate': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        'bounce-in': {
          from: { transform: 'scale(0.3)', opacity: 0 },
          '60%': { transform: 'scale(1.1)' },
          '80%': { transform: 'scale(0.95)' },
          to: { transform: 'scale(1)', opacity: 1 },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        'confetti-fall': {
          '0%': { transform: 'translateY(-100px) rotate(0deg)', opacity: 1 },
          '100%': { transform: 'translateY(400px) rotate(720deg)', opacity: 0 },
        },
      },
      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
        'gov-gradient': 'linear-gradient(135deg, #0B3C5D 0%, #1A5276 50%, #154360 100%)',
        'scan-gradient': 'linear-gradient(180deg, rgba(26,82,118,0) 0%, rgba(26,82,118,0.6) 50%, rgba(26,82,118,0) 100%)',
      },
      boxShadow: {
        'gov': '0 4px 24px rgba(26,82,118,0.18)',
        'gov-lg': '0 8px 40px rgba(26,82,118,0.28)',
        'card': '0 2px 16px rgba(0,0,0,0.06)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
};
