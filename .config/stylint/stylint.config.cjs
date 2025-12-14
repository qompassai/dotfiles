/** 
 * /qompassai/dotfiles/.config/stylint/styling.config.cjs
 * Qompass AI Stylelint Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************************
 */
module.exports = {
  extends: [
    "stylelint-config-prettier",
    "stylelint-config-recommended-scss",
    "stylelint-config-recommended-less",
    "stylelint-config-standard",
    "stylelint-config-standard-scss",
  ],
  plugins: [
    "stylelint-order",
    "stylelint-declaration-strict-value",
    "stylelint-high-performance-animation",
  ],
  rules: {
    "color-named": "never",
    "color-no-invalid-hex": true,
    "function-url-quotes": "always",
    "indentation": 2,
    "max-line-length": 160,
    "no-descending-specificity": null,
    "selector-type-no-unknown": [true, { ignore: ["custom-elements"] }],
    "string-quotes": "single",
    "unit-no-unknown": true,
    "property-no-unknown": [true, { ignoreProperties: ["composes"] }],
    "plugin/declaration-strict-value": [
      [
        "/color/",
        "z-index",
        "font-size",
        {
          ignoreKeywords: ["inherit", "transparent", "currentColor", "initial", "unset"],
        },
      ],
    ],
    "plugin/no-low-performance-animation-properties": true,
    "order/order": [
      "custom-properties",
      "declarations",
      "dollar-variables",
      {
        type: "at-rule",
        name: "include",
      },
      "rules"
    ],
    "order/properties-order": [],
  },
  overrides: [
    {
      files: ["**/*.scss"],
      customSyntax: "postcss-scss",
    },
    {
      files: ["**/*.less"],
      customSyntax: "postcss-less",
    },
    {
      files: ["**/*.css"],
      customSyntax: "postcss-css",
    },
  ],
  ignoreFiles: [
    "**/node_modules/**",
    "**/dist/**",
    "**/target/**",
    "**/.git/**",
  ],
};
