/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          50: '#f4f6fa',
          100: '#e4ebf5',
          200: '#c9d7ec',
          300: '#9ebadc',
          400: '#6d9ac9',
          500: '#4a7db4',
          600: '#34639b',
          700: '#2a4f7d',
          800: '#254367',
          900: '#0f2942',
          950: '#0a1b2d',
        },
        navy: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          800: '#102a43',
          900: '#0b1e33',
          950: '#061220',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgba(15, 23, 42, 0.04)',
        'subtle': '0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px 0 rgba(15, 23, 42, 0.04)',
      }
    },
  },
  plugins: [],
}
