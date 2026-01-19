// /qompassai/dotfiles/.config/npm/init.js
// Qompass AI Node Package Manager (NPM) Init JS Config
// Copyright (C) 2025 Qompass AI, All rights reserved
/////////////////////////////////////////////////////

module.exports = {
  name: "qnpm",
  version: "0.1.0",
  description: "Qompass AI global npm default package",
  private: true,
  author: {
    name: "Matt Porter",
    email: "matt@qompass.ai",
    url: "https://qompass.ai"
  },
  license: "MIT",
  main: "index.js",
  module: "index.mjs",
  types: "index.d.ts",
  scripts: {
    start: "node index.js",
    test: "echo \"No tests yet\" && exit 0"
  },
  homepage: "https://www.github.com/qompassai/npm",
  repository: {
    type: "git",
    url: "https://github.com/qompassai/js.git"
  },
  bugs: {
    url: "https://github.com/qompassai/js/issues"
  },

  keywords: ["qompass", "ai", "init", "template"],

  dependencies: {},

  devDependencies: {
    typescript: "^5.4.0"
  },

  publishConfig: {
    access: "public"
  },

  engines: {
    node: ">=18.0.0",
    npm: ">=9.0.0"
  }
};

