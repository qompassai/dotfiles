-- vim: filetype=lua

-- #################################################################
-- /qompassai/.config/buildcache/lua/.luacheckrc
-- Qompass AI Config
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
read_globals = {
  "require_std",
  "m_unresolved_args",
  bcache = {
    fields = {
      append_path = {},
      dir_exists = {},
      file_exists = {},
      get_dir_part = {},
      get_extension = {},
      get_file_info = {},
      get_file_part = {},
      log_debug = {},
      log_error = {},
      log_fatal = {},
      log_info = {},
      log_warning = {},
      parse_json = {},
      resolve_path = {},
      run = {},
      split_args = {},
    }
  },
}
-- Globals that are read/write by the wrapper, plus wrapper interface functions
-- that scripts define at global scope.
globals = {
  -- Synced between wrapper and script.
  "m_args",
  "m_implicit_input_files",

  "can_handle_command",
  "finalize_after_hit",
  "get_build_files",
  "get_capabilities",
  "get_hash_extra_content",
  "get_input_files",
  "get_program_id",
  "get_relevant_arguments",
  "get_relevant_env_vars",
  "preprocess_source",
  "resolve_args",
  "run_for_miss",
}

