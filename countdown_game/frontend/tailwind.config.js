/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        countdown: {
          blue: '#0066cc',
          yellow: '#ffcc00',
          red: '#cc0000',
          green: '#00cc66',
        }
      },
      fontFamily: {
        'countdown': ['Arial', 'sans-serif'],
      },
      animation: {
        'countdown': 'pulse 1s ease-in-out infinite',
        'tile-flip': 'flip 0.6s ease-in-out',
        'score-update': 'bounce 0.5s ease-in-out',
      },
      keyframes: {
        flip: {
          '0%': { transform: 'rotateY(0deg)' },
          '50%': { transform: 'rotateY(90deg)' },
          '100%': { transform: 'rotateY(0deg)' },
        }
      }
    },
  },
  plugins: [],
}