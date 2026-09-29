/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        fog: '#EDF0F3',
        ink: '#18212B',
        mute: '#5C6875',
        line: '#D3D9E0',
        mem: '#2A4BD7',
        memsoft: '#E7ECFC',
        warn: '#8F5208',
        warnsoft: '#FBF0DC',
        ok: '#1F6B4F',
        oksoft: '#E1F1EA',
        bad: '#B3261E',
        badsoft: '#FBE8E6',
      },
      fontFamily: {
        sans: ['"Instrument Sans Variable"', 'system-ui', 'Segoe UI', 'sans-serif'],
        serif: ['"Source Serif 4 Variable"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
