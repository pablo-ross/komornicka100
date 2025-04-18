/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'strava-orange': '#FC4C02',
      },
    },
  },
  plugins: [
    //require('@tailwindcss/typography'),
  ],
}