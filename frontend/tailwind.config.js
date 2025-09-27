import { defineConfig } from '@tailwindcss/vite'

export default defineConfig({
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sx: {
          bg: '#0A0D12',
          surface: '#0D1117',
          card: '#10141C',
          text: '#E7E9EE',
          sub: '#9AA4B2',
          border: 'rgba(227,179,65,.14)'
        },
        gold: {
          300: '#F9D98C',
          400: '#F5C063',
          500: '#E3B341',
          600: '#C6972A'
        },
        success: '#10B981',
        warn: '#F59E0B',
        danger: '#EF4444',
        info: '#60A5FA'
      },
      borderRadius: {
        xl: '16px',
        '2xl': '20px'
      },
    },
  },
})
