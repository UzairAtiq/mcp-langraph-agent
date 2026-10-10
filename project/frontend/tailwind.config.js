/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Poppins", "sans-serif"],
      },
      colors: {
        page: "#E5E5E5",
        sidebar: "#0A0A0A",
        darkcard: "#0A0A0A",
        accent: {
          DEFAULT: "#FACC15",
          hover: "#EAB308",
        },
        danger: "#EF4444",
        purpleAccent: "#8B5CF6",
        mutedText: "#737373",
      },
      borderRadius: {
        "3xl": "1.5rem",
        "4xl": "2rem",
      },
      boxShadow: {
        soft: "0 4px 20px -2px rgba(0, 0, 0, 0.05)",
      },
    },
  },
  plugins: [],
};
