import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1B1F6B',
          50: '#EEEEF8',
          100: '#D5D6EE',
          200: '#ABADE0',
          300: '#8184D1',
          400: '#575BC3',
          500: '#1B1F6B',
          600: '#161956',
          700: '#111341',
          800: '#0C0D2C',
          900: '#070717',
        },
        accent: {
          DEFAULT: '#E8712B',
          50: '#FDF2EB',
          100: '#FAE0D0',
          200: '#F5C1A1',
          300: '#F0A272',
          400: '#EB8343',
          500: '#E8712B',
          600: '#C25A1E',
          700: '#9B4718',
          800: '#743511',
          900: '#4D230B',
        },
        secondary: {
          DEFAULT: '#6B3FA0',
          50: '#F3EFF8',
          100: '#E2D7EF',
          200: '#C5AFDF',
          300: '#A887CF',
          400: '#8B5FBF',
          500: '#6B3FA0',
          600: '#563280',
          700: '#402660',
          800: '#2B1940',
          900: '#150D20',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
