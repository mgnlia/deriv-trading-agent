/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        deriv: {
          red: '#FF444F',
          dark: '#0E0E0E',
          card: '#1A1A1A',
          border: '#2A2A2A',
          green: '#00C853',
          yellow: '#FFD600',
        }
      }
    },
  },
  plugins: [],
}
