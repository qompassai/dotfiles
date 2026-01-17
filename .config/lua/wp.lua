-- wp.lua
-- Qompass AI - [ ]
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
---@meta
---@class WPAudioGroupUtils
---@field set_audio_group                             fun(node: any, group: string|nil)
---@field get_audio_group                             fun(node: any): string|nil
---@field contains_audio_group                        fun(group: string): boolean
---@type WPAudioGroupUtils
agutils = agutils
---@class WPConstraint
---@field key                                         string
---@field operator                                    string
---@field value                                       any
---@param c                                           { [1]: string, [2]: string, [3]: any, type?: string }
---@return WPConstraint
local function Constraint_ctor(c) end
---@type fun(c: { [1]: string, [2]: string, [3]: any, type?: string }): WPConstraint
Constraint = Constraint or Constraint_ctor
---@class WPEvent
---@field get_source                                  fun(self: WPEvent): any
---@field get_subject                                 fun(self: WPEvent): any
---@class WPEventInterest
---@param spec                                        WPConstraint[]
---@return WPEventInterest
local function EventInterest_ctor(spec) end
---@type fun(spec: WPConstraint[]): WPEventInterest
EventInterest = EventInterest or EventInterest_ctor
---@class WPJsonObject
---@field get_data                                    fun(self: WPJsonObject): table
---@class WPJson
---@field Object                                      fun(tbl: table): WPJsonObject
---@type WPJson
Json = Json
---@class WPLocalModule
---@field destroy                                     fun(self: WPLocalModule)
---@param name                                        string # e.g. "libpipewire-module-loopback"
---@param args                                        table                 
---@param opts                                        table
---@return WPLocalModule
local function LocalModule_ctor(name, args, opts) end
---@type fun(name: string, args: table, opts: table): WPLocalModule
LocalModule = LocalModule or LocalModule_ctor
---@class WPLog
---@field info                                        fun(...: any)
---@field warning                                     fun(...: any)
---@field error                                       fun(...: any)
---@type WPLog
Log = Log
---@class WPProcInfo
---@field get_arg                                     fun(self: WPProcInfo, index: integer): string|nil 
---@field get_n_args                                  fun(self: WPProcInfo): integer                   
---@field get_parent_pid                              fun(self: WPProcInfo): integer         
---@class WPProcUtils
---@field get_proc_info                               fun(pid: integer): WPProcInfo
---@type WPProcUtils
ProcUtils = ProcUtils
---@class WPSimpleEventHook
---@field register                                    fun(self: WPSimpleEventHook)
---@param opts                                        { name: string, interests: WPEventInterest[], execute: fun(event: WPEvent) }
---@return WPSimpleEventHook
local function SimpleEventHook_ctor(opts) end
---@type fun(opts: { name: string, interests: WPEventInterest[], execute: fun(event: WPEvent) }): WPSimpleEventHook
SimpleEventHook = SimpleEventHook or SimpleEventHook_ctor
