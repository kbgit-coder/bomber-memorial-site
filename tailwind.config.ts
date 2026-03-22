import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: "#1a2332",
        "navy-light": "#2c3e50",
        gold: "#c9b98a",
        "gold-border": "#8b7355",
        link: "#2c5f8a",
        heritage: "#f5f3f0",
      },
      fontFamily: {
        serif: ["Georgia", "Times New Roman", "serif"],
        heading: ["Helvetica Neue", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
