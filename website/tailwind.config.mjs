import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        night: {
          950: '#030814',
          900: '#071225',
          850: '#0b1830',
          800: '#102448',
          700: '#1b3a72',
        },
        brand: {
          blue: '#2f7cff',
          lightBlue: '#79aaff',
          accent: '#8eb8ff',
          amber: '#f0c36b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      }
    },
  },
  plugins: [typography],
};
