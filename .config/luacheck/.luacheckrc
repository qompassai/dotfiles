-- /qompassai/dotfiles/.config/luacheck/.luacheckrc
-- Qompass AI Diver Luacheck Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-- --------------------------------------------------
return {
	std = 'lua5.1+luajit+pandoc',
	read_globals = {
		"vim",
		cache = true
	},
	stds = {
		pandoc = {
			read_globals = {
				"FORMAT",
				"PANDOC_READER_OPTIONS",
				"PANDOC_WRITER_OPTIONS",
				"PANDOC_VERSION",
				"PANDOC_API_VERSION",
				"PANDOC_SCRIPT_FILE",
				"PANDOC_STATE",
				"pandoc",
				"lpeg",
				"re"
			},
			globals = {
				"traverse",
				"BlockQuote",
				"Blocks",
				"BulletList",
				"Cite",
				"Code",
				"CodeBlock",
				"DefinitionList",
				"Div",
				"Emph",
				"Figure",
				"Header",
				"HorizontalRule",
				"Image",
				"Inlines",
				"LineBlock",
				"LineBreak",
				"Link",
				"Math",
				"Meta",
				"Note",
				"OrderedList",
				"Pandoc",
				"Para",
				"Plain",
				"Quote",
				"RawBlock",
				"RawInline",
				"SmallCaps",
				"SoftBreak",
				"Space",
				"Span",
				"Strikeout",
				"Strong",
				"Subscript",
				"Superscript",
				"Underline",
				"Table"
			}
		}
	},
	globals = {
		"vim",
		"use",
		"describe",
		"it",
		"before_each",
		"after_each",
		"assert",
		"spy",
		"mock",
		"require",
		"package",
		"jit",
		"arg",
		"m",
		"vim.g",
		"vim.b",
		"vim.w",
		"vim.o",
		"vim.bo",
		"vim.wo",
		"vim.go",
		"vim.env",
		"_",
	},
	unused_args = true,
	redefined = true,
	ignore = {
		"113",
		"121",
		"122",
		"211",
		"212/_.*",
		"214",
		"431",
		"542",
		"581",
		"631",
	},
	max_line_length = 150,
	files = {
		["spec/**/*.lua"] = {
			globals = {
				"describe",
				"it",
				"before_each",
				"after_each",
				"assert"
			}
		},

		["**/spec/**/*_spec.lua"] = {
			std = "+busted"
		},
		["**/test/**/*_spec.lua"] = {
			std = "+busted"
		},
		["**/tests/**/*_spec.lua"] = {
			std = "+busted"
		},
		["**/*.rockspec"] = {
			std = "+rockspec"
		},
		["**/.luacheckrc"] = {
			std = "+luacheckrc"
		}
	}
}
