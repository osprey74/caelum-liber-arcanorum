/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Card frame palette (deep midnight navy, antique gold, muted teal, soft ivory)
        night: "#111f2f",
        gold: "#c9a961",
        teal: "#5f8a87",
        ivory: "#efe6d2",
      },
    },
  },
  plugins: [],
};
