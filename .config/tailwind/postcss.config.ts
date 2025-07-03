// /qompassai/dotfiles/.config/tailwind/postcss.config.mjs
// Qompass AI Postcss Typescript Config Dotfile
// Copyright (C) 2025 Qompass AI, All rights reserved
////////////////////////////////////////////////////

import tailwindcss from "tailwindcss"
import autoprefixer from "autoprefixer"
import type { ProcessOptions } from "postcss"

const config: ProcessOptions = {
  plugins: [tailwindcss, autoprefixer],
}

export default config
