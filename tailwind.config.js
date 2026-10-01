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
        // UI surfaces and text tones (design: Claude Design canvas "Liber Arcanorum UI", 2026-10-01)
        deep: "#0c1724", // inputs, side panel
        panel: "#14253a", // cards on the night ground
        "panel-hi": "#1b2d3f", // selected card
        soft: "#d9d1bd", // secondary text
        muted: "#b8b1a0", // captions (4.5:1 or more on night)
      },
      fontFamily: {
        // Shippori Mincho is bundled as a subset (titles, headings, buttons, card names: tools/fonts/build_fonts.py);
        // a character outside it falls back to the OS Mincho.
        display: ['"Shippori Mincho"', '"Yu Mincho"', "YuMincho", '"Hiragino Mincho ProN"', "serif"],
        // Body text (AI interpretation, card meanings): the OS Mincho.
        mincho: ['"Yu Mincho"', "YuMincho", '"Hiragino Mincho ProN"', '"Noto Serif JP"', "serif"],
        sans: ['"Yu Gothic UI"', '"Hiragino Sans"', "Meiryo", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
