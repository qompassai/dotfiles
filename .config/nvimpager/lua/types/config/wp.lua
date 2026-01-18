-- /qompassai/Diver/lua/types/config/wp.lua
-- Qompass AI Diver WirePlumber Types Config
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
---@meta
---@alias WPProperties                                table<string, any>
---@alias WPAccess
---| '"unrestricted"'
---| '"default"'
---| '"flatpak"'
---| '"restricted"'
---| '"flatpak-manager"'
---| nil
---@alias WPPermissions
---| '"all"'
---| '"rx"'
---@class WPAudioGroupUtils
---@field contains_audio_group                        fun(group: string): boolean
---@field get_audio_group                             fun(node: any): string|nil
---@field set_audio_group                             fun(node: any, group: string|nil)
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
---@class WPDevice : WPObject
---@field iterate_params                              fun(self: WPDevice, id: string): fun(): any
---@class WPEvent
---@field get_data                                    fun(self: WPEvent, key: string): any
---@field get_source                                  fun(self: WPEvent): WPObject
---@field get_subject                                 fun(self: WPEvent): any
---@field set_data                                    fun(self: WPEvent, key: string, value: any)
---@class WPEventDispatcher
---@field push_event                                  fun(event: WPEvent)
---@type WPEventDispatcher
EventDispatcher = EventDispatcher
---@class WPEventInterest
---@param spec                                        WPConstraint[]
---@return WPEventInterest
local function EventInterest_ctor(spec) end
---@type fun(spec: WPConstraint[]): WPEventInterest
EventInterest = EventInterest or EventInterest_ctor
---@class WPJson
---@field Array                                       fun(t: table): WPJsonObject
---@field Object                                      fun(tbl: table): WPJsonObject
---@field Raw                                         fun(obj: any): WPJsonObject
---@type WPJson
Json = Json
---@class WPJsonObject
---@field get_data                                    fun(self: WPJsonObject): table
---@field parse                                       fun(self: WPJsonObject): table
---@field to_string                                   fun(self: WPJsonObject): string
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
---@field debug                                       fun(...: any)
---@field error                                       fun(...: any)
---@field info                                        fun(...: any)
---@field open_topic                                  fun(topic: string): WPLog
---@field trace                                       fun(...: any)
---@field warning                                     fun(...: any)
---@type WPLog
Log = Log
---@class WPObject
---@field call                                        fun(self: WPObject, method: string, ...: any): any
---@field get_associated_proxy                        fun(self: WPObject, role: string): WPObject
---@field get_properties                              fun(self: WPObject): table<string, any>
---@field lookup_port                                 fun(self: WPObject, constraints: table): WPObject|nil
---@field properties                                  table<string, any>
---@class WPObjectManager
---@field iterate                                     fun(self: WPObjectManager, filter?: table): fun(): WPObject
---@field lookup                                      fun(self: WPObjectManager, id: any): WPObject|nil
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
---@field remove                                      fun(self: WPSimpleEventHook)
---@param opts                                        { name: string, interests: WPEventInterest[], execute: fun(event: WPEvent) }
---@return WPSimpleEventHook
local function SimpleEventHook_ctor(opts) end
---@type fun(opts: { name: string, interests: WPEventInterest[], execute: fun(event: WPEvent) }): WPSimpleEventHook
SimpleEventHook = SimpleEventHook or SimpleEventHook_ctor
---@class WPState
---@field save_after_timeout                          fun(self: WPState, tbl: table)