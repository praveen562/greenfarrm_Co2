/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canopy: {
          950: "#0F2A1E",
          900: "#153A28",
          800: "#1B4A33",
          700: "#215A3E",
          600: "#2C7350",
          500: "#3B8F65",
          400: "#5FAD82",
          300: "#8FC9A6",
          200: "#C3E4D0",
          100: "#E4F2E9",
          50: "#F3F8F5",
        },
        soil: {
          700: "#6B4A2E",
          500: "#9C6B3E",
          300: "#D9B78C",
        },
        clay: "#C77D2B",
        rust: "#B23A2E",
        ink: "#16241C",
        paper: "#FAFBF8",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(15, 42, 30, 0.06), 0 4px 12px rgba(15, 42, 30, 0.05)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};
