#!/usr/bin/env lua
--luacheck: globals require_std ARGS bcache
-- Qompass AI BuildCache Clang-Tidy LuaScript
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
require_std('*')
local _OPTIONS_WITH_ARGS = {
    ['-p'] = true,
    ['--checks'] = true,
    ['--config'] = true,
    ['--export-fixes'] = true,
    ['--extra-arg'] = true,
    ['--extra-arg-before'] = true,
    ['--format-style'] = true,
    ['--header-filter'] = true,
    ['--line-filter'] = true,
    ['--store-check-profile'] = true,
    ['--vfsoverlay'] = true,
    ['--warnings-as-errors'] = true,
}
local function parse_arg(idx)
    local arg = ARGS[idx]
    local arg2
    if _OPTIONS_WITH_ARGS[arg] then
        arg2 = ARGS[idx + 1]
        return idx + 2, arg, arg2
    end

    arg2 = arg:match('.*=(.*)')
    if arg2 then
        arg = arg:match('(.*)=.*')
    end
    return idx + 1, arg, arg2
end
local function for_each_arg(f)
    local i = 2
    while i <= #ARGS do
        local arg, arg2
        i, arg, arg2 = parse_arg(i)
        f(arg, arg2)
    end
end
local _SOURCE_FILE_EXTS = {
    ['.cpp'] = true,
    ['.cc'] = true,
    ['.cxx'] = true,
    ['.c'] = true,
}
local function is_source_file(path)
    if path[1] == '-' then
        return false
    end
    local ext = bcache.get_extension(path):lower()
    return _SOURCE_FILE_EXTS[ext]
end
local function is_dir(path)
    local info = bcache.get_file_info(path)
    return info['is_dir']
end

local function find_file_in_parents(path, name)
    local dir = path
    if not is_dir(path) then
        dir = bcache.get_dir_part(dir)
    end
    while #dir > 0 do
        local file_path = bcache.append_path(dir, name)
        if bcache.file_exists(file_path) then
            return file_path
        end
        dir = bcache.get_dir_part(dir)
    end
    return nil
end
local function load_file(path)
    local f = assert(io.open(path, 'rb'))
    local data = f:read('*all')
    f:close()
    return data
end
local function load_config(src_file)
    local config_path = nil
    for_each_arg(function(arg, arg2)
        if arg == '--config' and arg2 then
            config_path = bcache.remsolve_path(arg2)
        end
    end)
    if not config_path then
        config_path = find_file_in_parents(src_file, '.clang-tidy')
    end
    local config = ''
    if config_path then
        config = load_file(config_path)
    end
    return config
end
local function load_compile_db(first_src_file)
    -- Use the "-p=<path>" argument to find compile_commands.json.
    local compile_db_path = nil
    for_each_arg(function(arg, arg2)
        if arg == '-p' and arg2 then
            compile_db_path = arg2
        end
    end)
    if compile_db_path and is_dir(compile_db_path) then
        compile_db_path = bcache.append_path(compile_db_path, 'compile_commands.json')
    end
    if not compile_db_path then
        compile_db_path = find_file_in_parents(first_src_file, 'compile_commands.json')
    end
    if (not compile_db_path) or (not bcache.file_exists(compile_db_path)) then
        error('No compile_commands.json file found')
    end
    bcache.log_debug('Found compile_commands.json: ' .. compile_db_path)
    return load_file(compile_db_path)
end
local function get_string_from_db_entry(entry, key)
    local start = entry:find('"' .. key .. '":')
    if not start then
        error('Key "' .. key .. '" not found in compilation database')
    end
    local pos = start + #key + 3
    while pos < #entry and entry:sub(pos, pos) ~= '"' do
        pos = pos + 1
    end
    pos = pos + 1
    local str_chars = {}
    while pos < #entry and entry:sub(pos, pos) ~= '"' do
        local c = entry:sub(pos, pos)
        if c == '\\' then
            pos = pos + 1
            c = entry:sub(pos, pos)
            if c == 'n' then
                c = '\n'
            elseif c == 'r' then
                c = '\r'
            elseif c == 't' then
                c = '\t'
            end
        end
        table.insert(str_chars, c)
        pos = pos + 1
    end
    return table.concat(str_chars, '')
end
local function get_compile_cmd(compile_db, src_path)
    local start = compile_db:find('"' .. src_path .. '"', nil, true)
    if not start then
        error('Entry for ' .. src_path .. ' not found in compilation database')
    end
    local stop = start + #src_path + 2
    while start > 1 and compile_db:sub(start, start) ~= '{' do
        start = start - 1
    end
    while stop < #compile_db and compile_db:sub(stop, stop) ~= '}' do
        stop = stop + 1
    end
    local entry = compile_db:sub(start, stop)
    local cmd = get_string_from_db_entry(entry, 'command')
    local work_dir = get_string_from_db_entry(entry, 'directory')
    return cmd, work_dir
end
local function extract_compiler_flags(compile_args)
    local flags = {}
    for _, arg in ipairs(compile_args) do
        local two = arg:sub(1, 2)
        if (two == '-D') or (two == '/D') or (two == '-U') or (two == '/U') or (two == '-I') or (two == '/I') then
            -- TODO(m): Support two-part arguments (e.g. /U foo).
            if #arg < 3 then
                error('Unsupported compiler flag: ' .. arg)
            end
            table.insert(flags, '-' .. arg:sub(2))
        end
    end
    return flags
end
local _KNOWN_GCC_PREPROCESSORS = {
    'gcc',
    'g++',
    'clang',
}
local _KNOWN_CPP_PREPROCESSORS = {
    '/usr/bin/cpp',
    '/usr/bin/clang-cpp',
}
local function preprocess_src(src_path, cmd, work_dir)
    local compile_args = bcache.split_args(cmd)
    pp_type = '?'
    local pp_path = bcache.resolve_path(compile_args[1])
    local pp_name = bcache.get_file_part(pp_path:lower())
    for _, name in ipairs(_KNOWN_GCC_PREPROCESSORS) do
        if pp_name:find(name, nil, true) then
            pp_type = 'gcc'
            break
        end
    end
    if pp_type == '?' then
        for _, path in ipairs(_KNOWN_CPP_PREPROCESSORS) do
            if bcache.file_exists(path) then
                pp_path = bcache.resolve_path(path)
                pp_name = bcache.get_file_part(pp_path)
                pp_type = 'cpp'
                break
            end
        end
    end
    if pp_type == '?' then
        error('Could not find a useful preprocessor')
    end
    bcache.log_debug('Using ' .. pp_path .. ' for ' .. pp_type .. '-style preprocessing')
    local preprocessor_args = extract_compiler_flags(compile_args)
    table.insert(preprocessor_args, 1, pp_path)
    local preprocessed_file = os.tmpname()
    if pp_type == 'gcc' then
        table.insert(preprocessor_args, '-E')
        table.insert(preprocessor_args, '-P')
        table.insert(preprocessor_args, '-o')
        table.insert(preprocessor_args, preprocessed_file)
        table.insert(preprocessor_args, src_path)
    elseif pp_type == 'cpp' then
        table.insert(preprocessor_args, src_path)
        table.insert(preprocessor_args, '-o')
        table.insert(preprocessor_args, preprocessed_file)
    end
    local result = bcache.run(preprocessor_args, true, work_dir)
    if result.return_code ~= 0 then
        os.remove(preprocessed_file)
        error('Preprocessing command was unsuccessful:\n' .. result.std_err)
    end
    local preprocessed_source = load_file(preprocessed_file)
    os.remove(preprocessed_file)
    return pp_path .. '#:#' .. preprocessed_source
end
function can_handle_command() ---@return boolean
    for_each_arg(function(arg, arg2)
        if
            (arg == '--fix')
            or (arg == '--fix-errors')
            or ((arg == '--format-style') and (arg2 ~= 'none'))
            or (arg == '--vfsoverlay')
            or (arg == '--store-check-profile')
        then
            error('Unsupported argument: ' .. arg)
        end
    end)
    return true
end

function get_build_files() ---@return table<string, string>
    local build_files = {}
    local found_fixes_file = false
    for_each_arg(function(arg, arg2)
        if arg == '--export-fixes' and arg2 then
            if found_fixes_file then
                error('Only a single --export-fixes file can be specified.')
            end
            build_files['fixes'] = arg2
            found_fixes_file = true
        end
    end)
    return build_files
end

function get_program_id() ---@return string
    local result = bcache.run({ ARGS[1], '--version' })
    if result.return_code ~= 0 then
        error('Unable to get the program version information string.')
    end
    return ARGS[1] .. ':' .. result.std_out
end

function get_relevant_arguments() ---@return table<integer, string>
    local filtered_args = {}
    table.insert(filtered_args, bcache.get_file_part(ARGS[1]))
    for_each_arg(function(arg, arg2)
        local ignore_arg = ((arg == '--config') or (arg == '--export-fixes') or (arg == '-p'))
        if not ignore_arg then
            if arg2 then
                table.insert(filtered_args, arg .. '=' .. arg2)
            else
                table.insert(filtered_args, arg)
            end
        end
    end)
    bcache.log_debug('Filtered args: ' .. table.concat(filtered_args, ' '))
    return filtered_args
end

function preprocess_source() ---@return string
    local src_files = {}
    for_each_arg(function(arg, arg2)
        if is_source_file(arg) then
            table.insert(src_files, bcache.resolve_path(arg))
        end
    end)
    if next(src_files) == nil then
        error('No source files found')
    end
    bcache.log_debug('Source files: ' .. table.concat(src_files, ', '))
    local db = load_compile_db(src_files[1])
    local input_data_items = {}
    for _, src_path in ipairs(src_files) do
        local config = load_config(src_path)
        table.insert(input_data_items, config)
        local cmd, work_dir = get_compile_cmd(db, src_path)
        table.insert(input_data_items, preprocess_src(src_path, cmd, work_dir))
    end
    return table.concat(input_data_items, '#:#')
end
