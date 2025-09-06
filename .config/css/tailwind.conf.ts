// /qompassai/css/tailwind.conf.ts
// Qompass AI Tailwind Config
// Copyright (C) 2025 Qompass AI, All rights reserved
// ------------------------------

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './*.html',
    './src/**/*.{html,js,ts,jsx,tsx,svelte,vue,mdx}',
    './components/**/*.{js,ts,jsx,tsx,svelte,vue}',
    './pages/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0f172a',
          light: '#1e293b',
        },
      },
    },
  },
  plugins: [],
}

export default config

