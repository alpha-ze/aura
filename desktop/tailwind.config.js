/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // AURA brand palette
        aura: {
          50:  "#f0f4ff",
          100: "#e0e9ff",
          200: "#c7d7fe",
          300: "#a5bcfd",
          400: "#8097fc",
          500: "#6272f8",   // primary
          600: "#4f55ef",
          700: "#4044d4",
          800: "#3538aa",
          900: "#313587",
          950: "#1e1f50",
        },
        surface: {
          DEFAULT: "#0f0f1a",
          50: "#1a1a2e",
          100: "#16213e",
          200: "#0f3460",
        },
      },
      fontFamily: {
        sans: ["Inter var", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        "aura": "0 0 40px rgba(98, 114, 248, 0.15)",
        "aura-lg": "0 0 80px rgba(98, 114, 248, 0.25)",
        "glass": "0 8px 32px rgba(0, 0, 0, 0.3)",
      },
      backgroundImage: {
        "aura-gradient": "linear-gradient(135deg, #6272f8 0%, #a78bfa 100%)",
        "dark-gradient": "linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
        "bounce-subtle": "bounce-subtle 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "glow": "glow 2s ease-in-out infinite",
        "wave": "wave 1.5s ease-in-out infinite",
      },
      keyframes: {
        "bounce-subtle": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-4px)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "glow": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(98, 114, 248, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(98, 114, 248, 0.7)" },
        },
        "wave": {
          "0%, 100%": { transform: "scaleY(0.5)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
