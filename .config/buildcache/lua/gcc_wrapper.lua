-- #################################################################
-- /qompassai/dotfiles/.config/buildcache/lua/gcc_wrapper.lua
-- Qompass AI Buildcache Gcc Wrapper
-- SPDX-License-Identifier: Apache-2.0
-- Copyright (c) 2026 Qompass AI
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at:
--   http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
-- #################################################################
-- match(.*(gcc|g\+\+|clang|clang\+\+).*)
require_std('io')
require_std('os')
require_std('string')
require_std('table')
require_std('bcache')
---@param args string[]
---@param preprocessed_file string
---@return string[]
local function make_preprocessor_cmd(args, preprocessed_file)
	local preprocess_args = {}
	local drop_next_arg = false
	for i, arg in ipairs(args) do
		local is_first_arg = (i == 1)
		local drop_this_arg = drop_next_arg
		drop_next_arg = false
		if arg == '-c' then
			drop_this_arg = true
		elseif arg == '-o' then
			drop_this_arg = true
			drop_next_arg = true
		end
		if not drop_this_arg and not is_first_arg then
			table.insert(preprocess_args, arg)
		elseif not drop_this_arg and is_first_arg then
			table.insert(preprocess_args, arg)
		end
	end
	table.insert(preprocess_args, '-E')
	table.insert(preprocess_args, '-P')
	table.insert(preprocess_args, '-o')
	table.insert(preprocess_args, preprocessed_file)
	return preprocess_args
end
---@param path string
---@return boolean
local function is_source_file(path)
	local ext = bcache.get_extension(path):lower()
	return (ext == '.cpp') or (ext == '.cc') or (ext == '.cxx') or (ext == '.c')
end
---@return string[]
function get_capabilities()
	return { 'hard_links' }
end
---@return table<string, string>
function get_build_files()
	local files = {}
	local found_object_file = false
	for i = 2, #ARGS do
		local next_idx = i + 1
		if (ARGS[i] == '-o') and (next_idx <= #ARGS) then
			if found_object_file then
				error('Only a single target object file can be specified.')
			end
			files['object'] = ARGS[next_idx]
			found_object_file = true
		elseif ARGS[i] == '-ftest-coverage' then
			error('Code coverage data is currently not supported.')
		end
	end
	if not found_object_file then
		error('Unable to get the target object file.')
	end
	return files
end
---@return string
function get_program_id()
	local result = bcache.run({ ARGS[1], '--version' })
	if result.return_code ~= 0 then
		error('Unable to get the compiler version information string.')
	end
	return result.std_out
end
---@return string[]
function get_relevant_arguments()
	local filtered_args = {}
	table.insert(filtered_args, bcache.get_file_part(ARGS[1]))
	local skip_next_arg = true
	for i, arg in ipairs(ARGS) do
		local is_first_arg = (i == 1)
		if not skip_next_arg then
			local is_arg_plus_file_name = (arg == '-I')
				or (arg == '-MF')
				or (arg == '-MT')
				or (arg == '-MQ')
				or (arg == '-o')
			local first_two_chars = arg:sub(1, 2)
			local is_unwanted_arg = is_first_arg
				or (first_two_chars == '-I')
				or (first_two_chars == '-D')
				or (first_two_chars == '-M')
				or is_source_file(arg)
			if is_arg_plus_file_name then
				skip_next_arg = true
			elseif not is_unwanted_arg then
				table.insert(filtered_args, arg)
			end
		else
			skip_next_arg = false
		end
	end
	return filtered_args
end
---@return string
function preprocess_source()
	local is_object_compilation = false
	local has_object_output = false
	for i, arg in ipairs(ARGS) do
		local is_first_arg = (i == 1)
		if not is_first_arg then
			if arg == '-c' then
				is_object_compilation = true
			elseif arg == '-o' then
				has_object_output = true
			elseif arg:sub(1, 1) == '@' then
				error('Response files are currently not supported.')
			end
		end
	end
	if (not is_object_compilation) or not has_object_output then
		error('Unsupported compilation command.')
	end
	local preprocessed_file = os.tmpname()
	local preprocessor_args = make_preprocessor_cmd(ARGS, preprocessed_file)
	local result = bcache.run(preprocessor_args)
	if result.return_code ~= 0 then
		os.remove(preprocessed_file)
		error('Preprocessing command was unsuccessful.')
	end
	local f = assert(io.open(preprocessed_file, 'rb'))
	local preprocessed_source = f:read('*all')
	f:close()
	os.remove(preprocessed_file)
	return preprocessed_source
end
