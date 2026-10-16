/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './**/forms.py',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: '#FBF6EF',
          50: '#FFFFFF',
          100: '#FAF4EC',
          200: '#F5E8D8',
          300: '#EEDAC2',
          400: '#E4C9A8',
        },
        kraft: {
          light: '#DEBE9B',
          DEFAULT: '#C9A27A',
          dark: '#B08860',
          darker: '#8F6B45',
        },
        cocoa: {
          light: '#5A3928',
          DEFAULT: '#3B2418',
          dark: '#24140D',
          darkest: '#140A06',
        },
        heart: {
          light: '#E64C60',
          DEFAULT: '#D7263D',
          dark: '#B21E31',
          hover: '#C21B2F',
        },
        blush: {
          light: '#FDF2F0',
          DEFAULT: '#F4D6D0',
          dark: '#E8B9B0',
        },
        gold: {
          light: '#E6CB7D',
          DEFAULT: '#D8B45A',
          dark: '#B8943B',
        },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'serif'],
        display: ['"Playfair Display"', 'serif'],
        sans: ['"DM Sans"', 'sans-serif'],
        script: ['"Dancing Script"', 'cursive'],
      },
      boxShadow: {
        'soft': '0 10px 30px -10px rgba(59, 36, 24, 0.08)',
        'warm': '0 15px 35px -5px rgba(201, 162, 122, 0.25)',
        'heart': '0 10px 25px -5px rgba(215, 38, 61, 0.3)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
