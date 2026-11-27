/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FDFCF7',
          100: '#FAF8F0',
          200: '#F5F0E1',
          300: '#EDE4CB',
          400: '#DECFA9',
        },
        lavender: {
          50: '#F7F5FC',
          100: '#EFEAFC',
          200: '#DFD5F8',
          300: '#C7B5F0',
          400: '#A98EE6',
          500: '#8A64DC',
          600: '#7346D1',
        },
        fashion: {
          dark: '#121214',
          card: '#1A1A1E',
          border: '#E8E5DD',
          beige: '#F4EFE6',
          sand: '#ECE5D8',
          charcoal: '#232327',
          muted: '#71717A'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'Georgia', 'serif']
      }
    },
  },
  plugins: [],
}
