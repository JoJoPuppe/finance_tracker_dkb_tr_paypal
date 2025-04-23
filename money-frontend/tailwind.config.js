module.exports = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        purple: {
          400: '#9f7aea',
          600: '#6b46c1',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};