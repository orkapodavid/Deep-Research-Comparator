/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        typing: {
          'from': { opacity: '0.5' },
          'to': { opacity: '1' }
        }
      },
      animation: {
        'typing': 'typing 0.5s infinite alternate'
      }
    },
  },
  plugins: [],
} 