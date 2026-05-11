import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        panel: "rgb(var(--panel) / <alpha-value>)",
        elevated: "rgb(var(--elevated) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        text: "rgb(var(--text) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        accent: {
          cyan: "rgb(var(--accent-cyan) / <alpha-value>)",
          amber: "rgb(var(--accent-amber) / <alpha-value>)",
          lime: "rgb(var(--accent-lime) / <alpha-value>)",
          orange: "rgb(var(--accent-orange) / <alpha-value>)",
          rose: "rgb(var(--accent-rose) / <alpha-value>)",
          sky: "rgb(var(--accent-sky) / <alpha-value>)"
        }
      },
      fontFamily: {
        sans: ["Space Grotesk", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "Consolas", "monospace"]
      },
      boxShadow: {
        panel: "0 24px 80px rgba(0, 0, 0, 0.42)"
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" }
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.38", transform: "scale(0.98)" },
          "50%": { opacity: "0.88", transform: "scale(1.02)" }
        },
        scan: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(200%)" }
        }
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        pulseSoft: "pulseSoft 5s ease-in-out infinite",
        scan: "scan 10s linear infinite"
      }
    }
  },
  plugins: []
} satisfies Config;
