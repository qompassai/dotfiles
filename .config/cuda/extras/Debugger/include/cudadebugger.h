/*
 * Copyright 2007-2024 NVIDIA Corporation.  All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *  * Neither the name of NVIDIA CORPORATION nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */


/*--------------------------------- Includes --------------------------------*/

#ifndef CUDADEBUGGER_H
#define CUDADEBUGGER_H

#include <stdint.h>
#include <stdlib.h>

#if defined(_MSC_VER) && _MSC_VER < 1800
// old MSVC does not support stdbool.h
typedef unsigned char bool;
#undef false
#undef true
#define false 0
#define true  1
#else
#include <stdbool.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* OS-agnostic _CUDBG_INLINE */
#if defined(_WIN32)
#define _CUDBG_INLINE __inline
#else
#define _CUDBG_INLINE inline
#endif


/*--------------------------------- API Version ------------------------------*/

#define CUDBG_API_VERSION_MAJOR      12 /* Major release version number */
#define CUDBG_API_VERSION_MINOR       9 /* Minor release version number */
#define CUDBG_API_VERSION_REVISION  156 /* Revision (build) number */

/*---------------------------------- Constants -------------------------------*/

#define CUDBG_MAX_DEVICES       64 /* Maximum number of supported devices */
#define CUDBG_MAX_SMS          256 /* Maximum number of SMs per device */
#define CUDBG_MAX_WARPS         64 /* Maximum number of warps per SM */
#define CUDBG_MAX_LANES         32 /* Maximum number of lanes per warp */
#define CUDBG_MAX_WARP_BARRIERS 16 /* Maximum number of convergence barriers per warp */
#define CUDBG_MAX_LOG_LEN      256 /* Maximum length of a single CUDA log message */

/*----------------------- Thread/Block Coordinates Types ---------------------*/

typedef struct { uint32_t x, y; }    CuDim2;   /* DEPRECATED */
typedef struct { uint32_t x, y, z; } CuDim3;   /* 3-dimensional coordinates for threads,... */

/*--------------------- Memory Segments (as used in DWARF) -------------------*/

typedef enum {
    ptxUNSPECIFIEDStorage,
    ptxCodeStorage,
    ptxRegStorage,
    ptxSregStorage,
    ptxConstStorage,
    ptxGlobalStorage,
    ptxLocalStorage,
    ptxParamStorage,
    ptxSharedStorage,
    ptxSurfStorage,
    ptxTexStorage,
    ptxTexSamplerStorage,
    ptxGenericStorage,
    ptxIParamStorage,
    ptxOParamStorage,
    ptxFrameStorage,
    ptxURegStorage,
    ptxMAXStorage
} ptxStorageKind;

/*--------------------------- Debugger System Calls --------------------------*/

#define CUDBG_IPC_FLAG_NAME                 cudbgIpcFlag
#define CUDBG_RPC_ENABLED                   cudbgRpcEnabled
#define CUDBG_APICLIENT_PID                 cudbgApiClientPid
#define CUDBG_DEBUGGER_INITIALIZED          cudbgDebuggerInitialized
#define CUDBG_APICLIENT_REVISION            cudbgApiClientRevision
#define CUDBG_SESSION_ID                    cudbgSessionId
#define CUDBG_ATTACH_HANDLER_AVAILABLE      cudbgAttachHandlerAvailable
#define CUDBG_DETACH_SUSPENDED_DEVICES_MASK cudbgDetachSuspendedDevicesMask
#define CUDBG_ENABLE_LAUNCH_BLOCKING        cudbgEnableLaunchBlocking
#define CUDBG_ENABLE_INTEGRATED_MEMCHECK    cudbgEnableIntegratedMemcheck
#define CUDBG_ENABLE_PREEMPTION_DEBUGGING   cudbgEnablePreemptionDebugging
#define CUDBG_RESUME_FOR_ATTACH_DETACH      cudbgResumeForAttachDetach

/*
 * Bitmask of the capabilities supported by the debugger front-end
 */
#define CUDBG_DEBUGGER_CAPABILITIES         cudbgDebuggerCapabilities

/*
 * Can be read to detect whether the external debugger implementation
 * (libcudadebugger.so) is used or not.
 */
#define CUDBG_USE_EXTERNAL_DEBUGGER          cudbgUseExternalDebugger

typedef enum {
    CUDBG_DEBUGGER_CAPABILITY_NONE                  = 0,
    CUDBG_DEBUGGER_CAPABILITY_LAZY_FUNCTION_LOADING = (1 << 0),
    CUDBG_DEBUGGER_CAPABILITY_SUSPEND_EVENTS        = (1 << 1),
    CUDBG_DEBUGGER_CAPABILITY_REPORT_EXCEPTIONS_IN_EXITED_WARPS = (1 << 2),
    CUDBG_DEBUGGER_CAPABILITY_NO_CONTEXT_PUSH_POP_EVENTS        = (1 << 3),
} CUDBGCapabilityFlags;

/*---------------- Internal Breakpoint Entries for Error Reporting ------------*/

#define CUDBG_REPORT_DRIVER_API_ERROR                   cudbgReportDriverApiError
#define CUDBG_REPORT_DRIVER_API_ERROR_FLAGS             cudbgReportDriverApiErrorFlags
#define CUDBG_REPORTED_DRIVER_API_ERROR_CODE            cudbgReportedDriverApiErrorCode
#define CUDBG_REPORTED_DRIVER_API_ERROR_FUNC_NAME_SIZE  cudbgReportedDriverApiErrorFuncNameSize
#define CUDBG_REPORTED_DRIVER_API_ERROR_FUNC_NAME_ADDR  cudbgReportedDriverApiErrorFuncNameAddr
#define CUDBG_REPORTED_DRIVER_API_ERROR_SOURCE          cudbgReportedDriverApiErrorSource
#define CUDBG_REPORTED_DRIVER_API_ERROR_NAME_SIZE       cudbgReportedDriverApiErrorNameSize
#define CUDBG_REPORTED_DRIVER_API_ERROR_NAME_ADDR       cudbgReportedDriverApiErrorNameAddr
#define CUDBG_REPORTED_DRIVER_API_ERROR_STRING_SIZE     cudbgReportedDriverApiErrorStringSize
#define CUDBG_REPORTED_DRIVER_API_ERROR_STRING_ADDR     cudbgReportedDriverApiErrorStringAddr
#define CUDBG_REPORT_DRIVER_INTERNAL_ERROR              cudbgReportDriverInternalError
#define CUDBG_REPORTED_DRIVER_INTERNAL_ERROR_CODE       cudbgReportedDriverInternalErrorCode

/*----------------------------- API Return Types -----------------------------*/

typedef enum {
    CUDBG_SUCCESS                           = 0x0000,  /* Successful execution */
    CUDBG_ERROR_UNKNOWN                     = 0x0001,  /* Error type not listed below */
    CUDBG_ERROR_BUFFER_TOO_SMALL            = 0x0002,  /* Cannot copy all the queried data into the buffer argument */
    CUDBG_ERROR_UNKNOWN_FUNCTION            = 0x0003,  /* Function cannot be found in the CUDA kernel */
    CUDBG_ERROR_INVALID_ARGS                = 0x0004,  /* Wrong use of arguments (NULL pointer, illegal value,...) */
    CUDBG_ERROR_UNINITIALIZED               = 0x0005,  /* Debugger API has not yet been properly initialized */
    CUDBG_ERROR_INVALID_COORDINATES         = 0x0006,  /* Invalid block or thread coordinates were provided */
    CUDBG_ERROR_INVALID_MEMORY_SEGMENT      = 0x0007,  /* Invalid memory segment requested (read/write) */
    CUDBG_ERROR_INVALID_MEMORY_ACCESS       = 0x0008,  /* Requested address (+size) is not within proper segment boundaries */
    CUDBG_ERROR_MEMORY_MAPPING_FAILED       = 0x0009,  /* Memory is not mapped and cannot be mapped */
    CUDBG_ERROR_INTERNAL                    = 0x000a,  /* A debugger internal error occurred */
    CUDBG_ERROR_INVALID_DEVICE              = 0x000b,  /* Specified device cannot be found */
    CUDBG_ERROR_INVALID_SM                  = 0x000c,  /* Specified sm cannot be found */
    CUDBG_ERROR_INVALID_WARP                = 0x000d,  /* Specified warp cannot be found */
    CUDBG_ERROR_INVALID_LANE                = 0x000e,  /* Specified lane cannot be found */
    CUDBG_ERROR_SUSPENDED_DEVICE            = 0x000f,  /* device is suspended */
    CUDBG_ERROR_RUNNING_DEVICE              = 0x0010,  /* device is running and not suspended */
    CUDBG_ERROR_RESERVED_0                  = 0x0011,  /* Reserved error code */
    CUDBG_ERROR_INVALID_ADDRESS             = 0x0012,  /* address is out-of-range */
    CUDBG_ERROR_INCOMPATIBLE_API            = 0x0013,  /* API version does not match */
    CUDBG_ERROR_INITIALIZATION_FAILURE      = 0x0014,  /* The CUDA Driver failed to initialize */
    CUDBG_ERROR_INVALID_GRID                = 0x0015,  /* Specified grid cannot be found */
    CUDBG_ERROR_NO_EVENT_AVAILABLE          = 0x0016,  /* No event left to be processed */
    CUDBG_ERROR_SOME_DEVICES_WATCHDOGGED    = 0x0017,  /* One or more devices have an associated watchdog (eg. X) */
    CUDBG_ERROR_ALL_DEVICES_WATCHDOGGED     = 0x0018,  /* All devices have an associated watchdog (eg. X) */
    CUDBG_ERROR_INVALID_ATTRIBUTE           = 0x0019,  /* Specified attribute does not exist or is incorrect */
    CUDBG_ERROR_ZERO_CALL_DEPTH             = 0x001a,  /* No function calls have been made on the device */
    CUDBG_ERROR_INVALID_CALL_LEVEL          = 0x001b,  /* Specified call level is invalid */
    CUDBG_ERROR_COMMUNICATION_FAILURE       = 0x001c,  /* Communication error between the debugger and the application. */
    CUDBG_ERROR_INVALID_CONTEXT             = 0x001d,  /* Specified context cannot be found */
    CUDBG_ERROR_ADDRESS_NOT_IN_DEVICE_MEM   = 0x001e,  /* Requested address was not originally allocated from device memory (most likely visible in system memory) */
    CUDBG_ERROR_MEMORY_UNMAPPING_FAILED     = 0x001f,  /* Memory is not unmapped and cannot be unmapped */
    CUDBG_ERROR_INCOMPATIBLE_DISPLAY_DRIVER = 0x0020,  /* The display driver is incompatible with the API */
    CUDBG_ERROR_INVALID_MODULE              = 0x0021,  /* The specified module is not valid */
    CUDBG_ERROR_LANE_NOT_IN_SYSCALL         = 0x0022,  /* The specified lane is not inside a device syscall */
    CUDBG_ERROR_MEMCHECK_NOT_ENABLED        = 0x0023,  /* Memcheck has not been enabled */
    CUDBG_ERROR_INVALID_ENVVAR_ARGS         = 0x0024,  /* Some environment variable's value is invalid */
    CUDBG_ERROR_OS_RESOURCES                = 0x0025,  /* Error while allocating resources from the OS */
    CUDBG_ERROR_FORK_FAILED                 = 0x0026,  /* Error while forking the debugger process */
    CUDBG_ERROR_NO_DEVICE_AVAILABLE         = 0x0027,  /* No CUDA capable device was found */
    CUDBG_ERROR_ATTACH_NOT_POSSIBLE         = 0x0028,  /* Attaching to the CUDA program is not possible */
    CUDBG_ERROR_WARP_RESUME_NOT_POSSIBLE    = 0x0029,  /* The resumeWarpsUntilPC() API is not possible, use resumeDevice() or singleStepWarp() instead */
    CUDBG_ERROR_INVALID_WARP_MASK           = 0x002a,  /* Specified warp mask is zero, or contains invalid warps */
    CUDBG_ERROR_AMBIGUOUS_MEMORY_ADDRESS    = 0x002b,  /* Address cannot be resolved to a GPU unambiguously */
    CUDBG_ERROR_RECURSIVE_API_CALL          = 0x002c,  /* Debug API entry point called from within a debug API callback */
    CUDBG_ERROR_MISSING_DATA                = 0x002d,  /* The requested data is missing */
    CUDBG_ERROR_NOT_SUPPORTED               = 0x002e,  /* Attempted operation is not supported */
} CUDBGResult;

static const char *CUDBGResultNames[] = {
    "CUDBG_SUCCESS",
    "CUDBG_ERROR_UNKNOWN",
    "CUDBG_ERROR_BUFFER_TOO_SMALL",
    "CUDBG_ERROR_UNKNOWN_FUNCTION",
    "CUDBG_ERROR_INVALID_ARGS",
    "CUDBG_ERROR_UNINITIALIZED",
    "CUDBG_ERROR_INVALID_COORDINATES",
    "CUDBG_ERROR_INVALID_MEMORY_SEGMENT",
    "CUDBG_ERROR_INVALID_MEMORY_ACCESS",
    "CUDBG_ERROR_MEMORY_MAPPING_FAILED",
    "CUDBG_ERROR_INTERNAL",
    "CUDBG_ERROR_INVALID_DEVICE",
    "CUDBG_ERROR_INVALID_SM",
    "CUDBG_ERROR_INVALID_WARP",
    "CUDBG_ERROR_INVALID_LANE",
    "CUDBG_ERROR_SUSPENDED_DEVICE",
    "CUDBG_ERROR_RUNNING_DEVICE",
    "CUDBG_ERROR_RESERVED_0",
    "CUDBG_ERROR_INVALID_ADDRESS",
    "CUDBG_ERROR_INCOMPATIBLE_API",
    "CUDBG_ERROR_INITIALIZATION_FAILURE",
    "CUDBG_ERROR_INVALID_GRID",
    "CUDBG_ERROR_NO_EVENT_AVAILABLE",
    "CUDBG_ERROR_SOME_DEVICES_WATCHDOGGED",
    "CUDBG_ERROR_ALL_DEVICES_WATCHDOGGED",
    "CUDBG_ERROR_INVALID_ATTRIBUTE",
    "CUDBG_ERROR_ZERO_CALL_DEPTH",
    "CUDBG_ERROR_INVALID_CALL_LEVEL",
    "CUDBG_ERROR_COMMUNICATION_FAILURE",
    "CUDBG_ERROR_INVALID_CONTEXT",
    "CUDBG_ERROR_ADDRESS_NOT_IN_DEVICE_MEM",
    "CUDBG_ERROR_MEMORY_UNMAPPING_FAILED",
    "CUDBG_ERROR_INCOMPATIBLE_DISPLAY_DRIVER",
    "CUDBG_ERROR_INVALID_MODULE",
    "CUDBG_ERROR_LANE_NOT_IN_SYSCALL",
    "CUDBG_ERROR_MEMCHECK_NOT_ENABLED",
    "CUDBG_ERROR_INVALID_ENVVAR_ARGS",
    "CUDBG_ERROR_OS_RESOURCES",
    "CUDBG_ERROR_FORK_FAILED",
    "CUDBG_ERROR_NO_DEVICE_AVAILABLE",
    "CUDBG_ERROR_ATTACH_NOT_POSSIBLE",
    "CUDBG_ERROR_WARP_RESUME_NOT_POSSIBLE",
    "CUDBG_ERROR_INVALID_WARP_MASK",
    "CUDBG_ERROR_AMBIGUOUS_MEMORY_ADDRESS",
    "CUDBG_ERROR_RECURSIVE_API_CALL",
    "CUDBG_ERROR_MISSING_DATA",
    "CUDBG_ERROR_NOT_SUPPORTED",
};

static _CUDBG_INLINE const char *cudbgGetErrorString (CUDBGResult error)
{
    if (((unsigned)error)*sizeof(char *) >= sizeof(CUDBGResultNames))
        return "*UNDEFINED*";
    return CUDBGResultNames[(unsigned)error];
}


/*------------------------- API Error Reporting Flags -------------------------*/
typedef enum {
    CUDBG_REPORT_DRIVER_API_ERROR_FLAGS_NONE = 0x0000, /* Default is that there is no flag */
    CUDBG_REPORT_DRIVER_API_ERROR_FLAGS_SUPPRESS_NOT_READY = ( 1U << 0 ), /* When set, cudaErrorNotReady/cuErrorNotReady will not be reported */
} CUDBGReportDriverApiErrorFlags;

typedef enum {
    CUDBG_REPORTED_DRIVER_API_ERROR_SOURCE_NONE     = 0x000,   /* Default is that there is no error and no source */
    CUDBG_REPORTED_DRIVER_API_ERROR_SOURCE_DRIVER   = 0x001,   /* The error originates from the CUDA Driver API */
    CUDBG_REPORTED_DRIVER_API_ERROR_SOURCE_RUNTIME  = 0x002,   /* The error originates from the CUDA Runtime API */
} CUDBGReportedDriverApiErrorSource;

/*------------------------------ Grid Attributes -----------------------------*/

typedef enum {
    CUDBG_ATTR_GRID_LAUNCH_BLOCKING    = 0x000,   /* Whether the grid launch is blocking or not. */
    CUDBG_ATTR_GRID_TID                = 0x001,   /* Id of the host thread that launched the grid. */
} CUDBGAttribute;

typedef struct {
    CUDBGAttribute attribute;
    uint64_t       value;
} CUDBGAttributeValuePair;

typedef enum {
    CUDBG_GRID_STATUS_INVALID,          /* An invalid grid ID was passed, or an error occurred during status lookup */
    CUDBG_GRID_STATUS_PENDING,          /* The grid was launched but is not running on the HW yet */
    CUDBG_GRID_STATUS_ACTIVE,           /* The grid is currently running on the HW */
    CUDBG_GRID_STATUS_SLEEPING,         /* The grid is on the device, doing a join */
    CUDBG_GRID_STATUS_TERMINATED,       /* The grid has finished executing */
    CUDBG_GRID_STATUS_UNDETERMINED,     /* The grid is either PENDING or TERMINATED */
} CUDBGGridStatus;

/*------------------------------- Kernel Types -------------------------------*/

typedef enum {
    CUDBG_KNL_TYPE_UNKNOWN             = 0x000,   /* Any type not listed below. */
    CUDBG_KNL_TYPE_SYSTEM              = 0x001,   /* System kernel, such as MemCpy. */
    CUDBG_KNL_TYPE_APPLICATION         = 0x002,   /* Application kernel, user-defined or libraries. */
} CUDBGKernelType;

/*--------------------------- Elf Image Properties ---------------------------*/

typedef enum {
    CUDBG_ELF_IMAGE_PROPERTIES_SYSTEM  = 0x001,   /* ELF image contains system kernels. */
} CUDBGElfImageProperties;

/*-------------------------- Physical Register Types -------------------------*/

typedef enum {
    REG_CLASS_INVALID                  = 0x000,   /* invalid register */
    REG_CLASS_REG_CC                   = 0x001,   /* Condition register */
    REG_CLASS_REG_PRED                 = 0x002,   /* Predicate register */
    REG_CLASS_REG_ADDR                 = 0x003,   /* Address register */
    REG_CLASS_REG_HALF                 = 0x004,   /* 16-bit register (Currently unused) */
    REG_CLASS_REG_FULL                 = 0x005,   /* 32-bit register */
    REG_CLASS_MEM_LOCAL                = 0x006,   /* register spilled in memory */
    REG_CLASS_LMEM_REG_OFFSET          = 0x007,   /* register at stack offset (ABI only) */
    REG_CLASS_UREG_PRED                = 0x009,   /* uniform predicate register */
    REG_CLASS_UREG_HALF                = 0x00a,   /* 16-bit uniform register */
    REG_CLASS_UREG_FULL                = 0x00b,   /* 32-bit uniform register */
} CUDBGRegClass;

/*---------------------------- Application Events ----------------------------*/

typedef enum {
    CUDBG_EVENT_INVALID                = 0x000,   /* Invalid event */
    CUDBG_EVENT_ELF_IMAGE_LOADED       = 0x001,   /* ELF image for CUDA kernel(s) is ready */
    CUDBG_EVENT_KERNEL_READY           = 0x002,   /* A CUDA kernel is ready to be launched */
    CUDBG_EVENT_KERNEL_FINISHED        = 0x003,   /* A CUDA kernel has terminated */
    CUDBG_EVENT_INTERNAL_ERROR         = 0x004,   /* Unexpected error. The API may be unstable. */
    CUDBG_EVENT_CTX_PUSH               = 0x005,   /* A CUDA context has been pushed. */
    CUDBG_EVENT_CTX_POP                = 0x006,   /* A CUDA context has been popped. */
    CUDBG_EVENT_CTX_CREATE             = 0x007,   /* A CUDA context has been created and pushed. */
    CUDBG_EVENT_CTX_DESTROY            = 0x008,   /* A CUDA context has been, popped if pushed, then destroyed. */
    CUDBG_EVENT_TIMEOUT                = 0x009,   /* Nothing happened for a while. This is heartbeat event.
                                                       NOTE: Only sent by the classic backend. */
    CUDBG_EVENT_ATTACH_COMPLETE        = 0x00a,   /* Attach complete. */
    CUDBG_EVENT_DETACH_COMPLETE        = 0x00b,   /* Detach complete. */
    CUDBG_EVENT_ELF_IMAGE_UNLOADED     = 0x00c,   /* ELF image for CUDA kernels(s) no longer available */
    CUDBG_EVENT_FUNCTIONS_LOADED       = 0x00d,   /* A group of functions/kernels have been loaded
                                                   *   NOTE: Will only be sent if the debugger capability
                                                   *   CUDBG_DEBUGGER_CAPABILITY_LAZY_FUNCTION_LOADING is set.
                                                   */
    CUDBG_EVENT_ALL_DEVICES_SUSPENDED  = 0x00e,   /* All CUDA devices have been suspended due to a breakpoint hit
                                                   *   or an exception. Does not get sent for GPU events that
                                                   *   result in synchronous API method calls, such as
                                                   *   singleStepWarp or resumeWarpsUntilPC.
                                                   *   NOTE: Will only be sent if the debugger capability
                                                   *   CUDBG_DEBUGGER_CAPABILITY_SUSPEND_EVENTS is set.
                                                   */
} CUDBGEventKind;

/*------------------------------- Kernel Origin ------------------------------*/

typedef enum {
    CUDBG_KNL_ORIGIN_CPU               = 0x000,   /* The kernel was launched from the CPU. */
    CUDBG_KNL_ORIGIN_GPU               = 0x001,   /* The kernel was launched from the GPU. */
} CUDBGKernelOrigin;

/*------------------------ Kernel Launch Notify Mode --------------------------*/

typedef enum {
    CUDBG_KNL_LAUNCH_NOTIFY_EVENT      = 0x000,   /* The kernel notifications generate events */
    CUDBG_KNL_LAUNCH_NOTIFY_DEFER      = 0x001,   /* The kernel notifications are deferred */
} CUDBGKernelLaunchNotifyMode;

/*---------------------- Application Event Queue Type ------------------------*/

typedef enum {
    CUDBG_EVENT_QUEUE_TYPE_SYNC      = 0,   /* Synchronous event queue */
    CUDBG_EVENT_QUEUE_TYPE_ASYNC     = 1,   /* Asynchronous event queue */
} CUDBGEventQueueType;

/*------------------------------ Elf Image Type ------------------------------*/

typedef enum {
    CUDBG_ELF_IMAGE_TYPE_NONRELOCATED      = 0,   /* Non-relocated ELF image */
    CUDBG_ELF_IMAGE_TYPE_RELOCATED         = 1,   /* Relocated ELF image */
} CUDBGElfImageType;

/*------------------------------ Code Address --------------------------------*/

typedef enum {
    CUDBG_ADJ_PREVIOUS_ADDRESS         = 0x000,   /* Get the adjusted previous code address. */
    CUDBG_ADJ_CURRENT_ADDRESS          = 0x001,   /* Get the adjusted current code address. */
    CUDBG_ADJ_NEXT_ADDRESS             = 0x002,   /* Get the adjusted next code address. */
} CUDBGAdjAddrAction;

/*------------------------------ Single Step Flags --------------------------------*/

typedef enum {
    /* Default behavior */
    CUDBG_SINGLE_STEP_FLAGS_NONE                        = 0,
    /* Do not step over warp-wide barriers using a breakpoint and resume,
     * instead perform a single step and return. Passing this flag in means
     * that the API client plans to repeat the singleStepWarp() call until
     * the warp barrier is stepped over. This gives a more precise exception
     * information if an exception is encountered by the diverged threads
     * while stepping. */
    CUDBG_SINGLE_STEP_FLAGS_NO_STEP_OVER_WARP_BARRIERS  = (1U << 0),
} CUDBGSingleStepFlags;

/* Deprecated */
typedef struct {
    CUDBGEventKind kind;
    union cases30_st {
        struct elfImageLoaded30_st {
            char     *relocatedElfImage;
            char     *nonRelocatedElfImage;
            uint32_t  size;
        } elfImageLoaded;
        struct kernelReady30_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
        } kernelReady;
        struct kernelFinished30_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
        } kernelFinished;
    } cases;
} CUDBGEvent30;

/* Deprecated */
typedef struct {
    CUDBGEventKind kind;
    union cases32_st {
        struct elfImageLoaded32_st {
            char     *relocatedElfImage;
            char     *nonRelocatedElfImage;
            uint32_t  size;
            uint32_t  dev;
            uint64_t  context;
            uint64_t  module;
        } elfImageLoaded;
        struct kernelReady32_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
        } kernelReady;
        struct kernelFinished32_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
        } kernelFinished;
        struct contextPush32_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPush;
        struct contextPop32_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPop;
        struct contextCreate32_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextCreate;
        struct contextDestroy32_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextDestroy;
    } cases;
} CUDBGEvent32;

/* Deprecated */
typedef struct {
    CUDBGEventKind kind;
    union cases42_st {
        struct elfImageLoaded42_st {
            char     *relocatedElfImage;
            char     *nonRelocatedElfImage;
            uint32_t  size32;
            uint32_t  dev;
            uint64_t  context;
            uint64_t  module;
            uint64_t  size;
        } elfImageLoaded;
        struct kernelReady42_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            CuDim3   gridDim;
            CuDim3   blockDim;
            CUDBGKernelType type;
        } kernelReady;
        struct kernelFinished42_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
        } kernelFinished;
        struct contextPush42_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPush;
        struct contextPop42_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPop;
        struct contextCreate42_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextCreate;
        struct contextDestroy42_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextDestroy;
    } cases;
} CUDBGEvent42;

typedef struct {
    CUDBGEventKind kind;
    union cases50_st {
        struct elfImageLoaded50_st {
            char     *relocatedElfImage;
            char     *nonRelocatedElfImage;
            uint32_t  size32;
            uint32_t  dev;
            uint64_t  context;
            uint64_t  module;
            uint64_t  size;
        } elfImageLoaded;
        struct kernelReady50_st{
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            CuDim3   gridDim;
            CuDim3   blockDim;
            CUDBGKernelType type;
        } kernelReady;
        struct kernelFinished50_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
        } kernelFinished;
        struct contextPush50_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPush;
        struct contextPop50_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPop;
        struct contextCreate50_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextCreate;
        struct contextDestroy50_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextDestroy;
        struct internalError50_st {
            CUDBGResult errorType;
        } internalError;
    } cases;
} CUDBGEvent50;

typedef struct {
    CUDBGEventKind kind;
    union cases55_st {
        struct elfImageLoaded55_st {
            char     *relocatedElfImage;
            char     *nonRelocatedElfImage;
            uint32_t  size32;
            uint32_t  dev;
            uint64_t  context;
            uint64_t  module;
            uint64_t  size;
        } elfImageLoaded;
        struct kernelReady55_st{
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            CuDim3   gridDim;
            CuDim3   blockDim;
            CUDBGKernelType type;
            uint64_t parentGridId;
            uint64_t gridId64;
            CUDBGKernelOrigin origin;
        } kernelReady;
        struct kernelFinished55_st {
            uint32_t dev;
            uint32_t gridId;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            uint64_t gridId64;
        } kernelFinished;
        struct contextPush55_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPush;
        struct contextPop55_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPop;
        struct contextCreate55_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextCreate;
        struct contextDestroy55_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextDestroy;
        struct internalError55_st {
            CUDBGResult errorType;
        } internalError;
    } cases;
} CUDBGEvent55;

#pragma pack(push,1)
typedef struct {
    CUDBGEventKind kind;
    union cases_st {
        struct elfImageLoaded_st {
            uint32_t dev;
            uint64_t context;
            uint64_t module;
            uint64_t size;
            uint64_t handle;
            uint32_t properties;
        } elfImageLoaded;
        struct elfImageUnloaded_st {
            uint32_t dev;
            uint64_t context;
            uint64_t module;
            uint64_t size;
            uint64_t handle;
        } elfImageUnloaded;
        struct kernelReady_st{
            uint32_t dev;
            uint32_t tid;
            uint64_t gridId;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            CuDim3   gridDim;
            CuDim3   blockDim;
            CUDBGKernelType type;
            uint64_t parentGridId;
            CUDBGKernelOrigin origin;
        } kernelReady;
        struct kernelFinished_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
            uint64_t module;
            uint64_t function;
            uint64_t functionEntry;
            uint64_t gridId;
        } kernelFinished;
        struct contextPush_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPush;
        struct contextPop_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextPop;
        struct contextCreate_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextCreate;
        struct contextDestroy_st {
            uint32_t dev;
            uint32_t tid;
            uint64_t context;
        } contextDestroy;
        struct internalError_st {
            CUDBGResult errorType;
        } internalError;
        struct functionsLoaded_st {
            uint32_t dev;
            uint32_t count;
            uint64_t context;
            uint64_t module;
        } functionsLoaded;
        struct allDevicesSuspended_st {
            /* This mask has bits set for devices with any warps that hit a breakpoint */
            uint64_t brokenDevicesMask;
            /* This mask has bits set for devices with any warps that hit an exception */
            uint64_t faultedDevicesMask;
        } allDevicesSuspended;
    } cases;
} CUDBGEvent;
#pragma pack(pop)

typedef struct {
    uint32_t tid;
} CUDBGEventCallbackData40;

typedef struct {
    uint32_t tid;
    uint32_t timeout;
} CUDBGEventCallbackData;

#pragma pack(push,1)
typedef struct {
    uint32_t dev;
    uint64_t gridId64;
    uint32_t tid;
    uint64_t context;
    uint64_t module;
    uint64_t function;
    uint64_t functionEntry;
    CuDim3   gridDim;
    CuDim3   blockDim;
    CUDBGKernelType type;
    uint64_t parentGridId;
    CUDBGKernelOrigin origin;
} CUDBGGridInfo55;

typedef struct {
    uint32_t dev;
    uint64_t gridId64;
    uint32_t tid;
    uint64_t context;
    uint64_t module;
    uint64_t function;
    uint64_t functionEntry;
    CuDim3   gridDim;
    CuDim3   blockDim;
    CUDBGKernelType type;
    uint64_t parentGridId;
    CUDBGKernelOrigin origin;
    CuDim3   clusterDim;
} CUDBGGridInfo120;

typedef struct {
    uint32_t dev;
    uint64_t gridId64;
    uint32_t tid;
    uint64_t context;
    uint64_t module;
    uint64_t function;
    uint64_t functionEntry;
    CuDim3   gridDim;
    CuDim3   blockDim;
    CUDBGKernelType type;
    uint64_t parentGridId;
    CUDBGKernelOrigin origin;
    CuDim3   clusterDim;
    CuDim3   preferredClusterDim;
} CUDBGGridInfo;
#pragma pack(pop)

#pragma pack(push,1)
typedef struct {
    uint64_t sectionIndex;
    uint64_t address;
} CUDBGLoadedFunctionInfo;
#pragma pack(pop)

typedef void (*CUDBGNotifyNewEventCallback31)(void *data);
typedef void (*CUDBGNotifyNewEventCallback40)(CUDBGEventCallbackData40 *data);
typedef void (*CUDBGNotifyNewEventCallback)(CUDBGEventCallbackData *data);

/*-------------------------------- Exceptions ------------------------------*/

typedef enum {
    CUDBG_EXCEPTION_UNKNOWN = 0xFFFFFFFFU, // Force sizeof(CUDBGException_t)==4
    CUDBG_EXCEPTION_NONE = 0,
    CUDBG_EXCEPTION_LANE_ILLEGAL_ADDRESS = 1,
    CUDBG_EXCEPTION_LANE_USER_STACK_OVERFLOW = 2,
    CUDBG_EXCEPTION_DEVICE_HARDWARE_STACK_OVERFLOW = 3,
    CUDBG_EXCEPTION_WARP_ILLEGAL_INSTRUCTION = 4,
    CUDBG_EXCEPTION_WARP_OUT_OF_RANGE_ADDRESS = 5,
    CUDBG_EXCEPTION_WARP_MISALIGNED_ADDRESS = 6,
    CUDBG_EXCEPTION_WARP_INVALID_ADDRESS_SPACE = 7,
    CUDBG_EXCEPTION_WARP_INVALID_PC = 8,
    CUDBG_EXCEPTION_WARP_HARDWARE_STACK_OVERFLOW = 9,
    CUDBG_EXCEPTION_DEVICE_ILLEGAL_ADDRESS = 10,
    CUDBG_EXCEPTION_LANE_MISALIGNED_ADDRESS = 11,
    CUDBG_EXCEPTION_WARP_ASSERT = 12,
    CUDBG_EXCEPTION_LANE_SYSCALL_ERROR = 13,
    CUDBG_EXCEPTION_WARP_ILLEGAL_ADDRESS = 14,
    CUDBG_EXCEPTION_LANE_NONMIGRATABLE_ATOMSYS = 15,
    CUDBG_EXCEPTION_LANE_INVALID_ATOMSYS = 16,
    CUDBG_EXCEPTION_CLUSTER_OUT_OF_RANGE_ADDRESS = 17,
    CUDBG_EXCEPTION_CLUSTER_BLOCK_NOT_PRESENT = 18,
    CUDBG_EXCEPTION_WARP_STACK_CANARY = 19,
} CUDBGException_t;

typedef enum {
    CUDBG_UVM_MEMORY_ACCESS_TYPE_UNKNOWN  = 0xFFFFFFFFU,
    CUDBG_UVM_MEMORY_ACCESS_TYPE_INVALID  = 0,
    CUDBG_UVM_MEMORY_ACCESS_TYPE_READ     = 1,
    CUDBG_UVM_MEMORY_ACCESS_TYPE_WRITE    = 2,
    CUDBG_UVM_MEMORY_ACCESS_TYPE_ATOMIC   = 3,
    CUDBG_UVM_MEMORY_ACCESS_TYPE_PREFETCH = 4,
} CUDBGUvmMemoryAccessType_t;

typedef enum {
    CUDBG_UVM_FAULT_TYPE_UNKNOWN               =  0xFFFFFFFFU,
    CUDBG_UVM_FAULT_TYPE_INVALID               =  0,
    CUDBG_UVM_FAULT_TYPE_INVALID_PDE           =  1,
    CUDBG_UVM_FAULT_TYPE_INVALID_PTE           =  2,
    CUDBG_UVM_FAULT_TYPE_WRITE                 =  3,
    CUDBG_UVM_FAULT_TYPE_ATOMIC                =  4,
    CUDBG_UVM_FAULT_TYPE_INVALID_PDE_SIZE      =  5,
    CUDBG_UVM_FAULT_TYPE_LIMIT_VIOLATION       =  6,
    CUDBG_UVM_FAULT_TYPE_UNBOUND_INST_BLOCK    =  7,
    CUDBG_UVM_FAULT_TYPE_PRIV_VIOLATION        =  8,
    CUDBG_UVM_FAULT_TYPE_PITCH_MASK_VIOLATION  =  9,
    CUDBG_UVM_FAULT_TYPE_WORK_CREATION         = 10,
    CUDBG_UVM_FAULT_TYPE_UNSUPPORTED_APERTURE  = 11,
    CUDBG_UVM_FAULT_TYPE_COMPRESSION_FAILURE   = 12,
    CUDBG_UVM_FAULT_TYPE_UNSUPPORTED_KIND      = 13,
    CUDBG_UVM_FAULT_TYPE_REGION_VIOLATION      = 14,
    CUDBG_UVM_FAULT_TYPE_POISON                = 15,
} CUDBGUvmFaultType_t;

typedef enum {
    CUDBG_UVM_FATAL_REASON_UNKNOWN             = 0xFFFFFFFFU,
    CUDBG_UVM_FATAL_REASON_INVALID             = 0,
    CUDBG_UVM_FATAL_REASON_INVALID_ADDRESS     = 1,
    CUDBG_UVM_FATAL_REASON_INVALID_PERMISSIONS = 2,
    CUDBG_UVM_FATAL_REASON_INVALID_FAULT_TYPE  = 3,
    CUDBG_UVM_FATAL_REASON_OUT_OF_MEMORY       = 4,
    CUDBG_UVM_FATAL_REASON_INTERNAL_ERROR      = 5,
    CUDBG_UVM_FATAL_REASON_INVALID_OPERATION   = 6,
} CUDBGUvmFatalReason_t;

/*------------------------------ Warp State --------------------------------*/
#pragma pack(push,1)
typedef struct {
    uint64_t virtualPC;
    CuDim3 threadIdx;
    CUDBGException_t exception;
} CUDBGLaneState;

typedef struct {
    uint64_t gridId;
    uint64_t errorPC;
    CuDim3 blockIdx;
    uint32_t validLanes;
    uint32_t activeLanes;
    uint32_t errorPCValid;
    CUDBGLaneState lane[32];
} CUDBGWarpState60;

typedef struct {
    uint64_t gridId;
    uint64_t errorPC;
    CuDim3 blockIdx;
    uint32_t validLanes;
    uint32_t activeLanes;
    uint32_t errorPCValid;
    CUDBGLaneState lane[32];
    CuDim3 clusterIdx;
} CUDBGWarpState120;

typedef struct {
    uint64_t gridId;
    uint64_t errorPC;
    CuDim3 blockIdx;
    uint32_t validLanes;
    uint32_t activeLanes;
    uint32_t errorPCValid;
    CUDBGLaneState lane[32];
    CuDim3 clusterIdx;
    CuDim3 clusterDim;
    uint32_t clusterExceptionTargetBlockIdxValid;
    CuDim3 clusterExceptionTargetBlockIdx;
} CUDBGWarpState127;

typedef struct {
    uint64_t gridId;
    uint64_t errorPC;
    CuDim3 blockIdx;
    uint32_t validLanes;
    uint32_t activeLanes;
    uint32_t errorPCValid;
    CUDBGLaneState lane[32];
    CuDim3 clusterIdx;
    CuDim3 clusterDim;
    uint32_t clusterExceptionTargetBlockIdxValid;
    CuDim3 clusterExceptionTargetBlockIdx;
    uint32_t inSyscallLanes;
} CUDBGWarpState;

typedef struct {
    uint32_t sharedMemSize;
    uint32_t numRegisters;
} CUDBGWarpResources;
#pragma pack(pop)

#pragma pack(push,1)
typedef struct {
    uint64_t startAddress;
    uint64_t size;
} CUDBGMemoryInfo;
#pragma pack(pop)

/*----------------------- Batched device info support ----------------------*/

/* uint32_t sized enum */
typedef enum {
    /* Request state information for all valid SMs/Warps/Lanes */
    CUDBG_RESPONSE_TYPE_FULL,

    /* Request state information for all changed SMs/Warps/Lanes since the last call */
    CUDBG_RESPONSE_TYPE_UPDATE,

    /* Force sizeof(CUDBGDeviceInfoQueryType_t)==4 */
    CUDBG_RESPONSE_TYPE_UNKNOWN = 0xFFFFFFFFU,
} CUDBGDeviceInfoQueryType_t;

/* uint32_t sized enum */
typedef enum {
    /* Mask of updated SMs reported by this response
       Optional: Yes, assume all 1's if absent
       Size: Number of SMs-sized bitmask, rounded up to be divisible by 8 */
    CUDBG_DEVICE_ATTRIBUTE_SM_UPDATE_MASK       = 0,
    /* Mask of SMs with any valid warp
       Optional: No, always returned by the API
       Size: Number of SMs-sized bitmask, rounded up to be divisible by 8 */
    CUDBG_DEVICE_ATTRIBUTE_SM_ACTIVE_MASK       = 1,
    /* Mask of SMs with any warps with exceptions
       Optional: Yes, assume all 0's if absent
       Size: Number of SMs-sized bitmask, rounded up to be divisible by 8 */
    CUDBG_DEVICE_ATTRIBUTE_SM_EXCEPTION_MASK    = 2,

    CUDBG_DEVICE_ATTRIBUTE_COUNT,
} CUDBGDeviceInfoAttribute_t;

/* uint32_t sized enum */
typedef enum {
    /* Mask of updated warps reported by this response
       Optional: Yes, assume all 1's if absent
       Size: uint64_t */
    CUDBG_SM_ATTRIBUTE_WARP_UPDATE_MASK  = 0,

    CUDBG_SM_ATTRIBUTE_COUNT,
} CUDBGSMInfoAttribute_t;

/* uint32_t sized enum */
typedef enum {
    /* Mask of updated lanes reported by this response
       Optional: Yes, assume all 1's if absent
       Size: uint32_t */
    CUDBG_WARP_ATTRIBUTE_LANE_UPDATE_MASK                   = 0,
    /* Signals whether the attribute flags field is present on the lane level for this warp
       Optional: Yes, assume no lane attributes for this warp if absent
       Size: 0 (doesn't have an associated warp-level field) */
    CUDBG_WARP_ATTRIBUTE_LANE_ATTRIBUTES                    = 1,
    /* CUDBGException_t for this warp
       Optional: Yes, assume CUDBG_EXCEPTION_NONE if absent
       Size: uint32_t */
    CUDBG_WARP_ATTRIBUTE_EXCEPTION                          = 2,
    /* Error PC for this warp
       Optional: Yes, assume no error PC is available if absent
       Size: uint64_t */
    CUDBG_WARP_ATTRIBUTE_ERRORPC                            = 3,
    /* Cluster index for this warp
       Optional: Yes if warp is not in a cluster
       Size: CuDim3 */
    CUDBG_WARP_ATTRIBUTE_CLUSTERIDX                         = 4,
    /* Cluster dimensions for this warp
       Optional: Yes if warp is not in a cluster
       Size: CuDim3 */
    CUDBG_WARP_ATTRIBUTE_CLUSTERDIM                         = 5,
    /* For cluster exceptions, this represents the target block index handling
       cluster requests.
       Optional: Yes, assume no block index is available if absent
       Size: CuDim3 */
    CUDBG_WARP_ATTRIBUTE_CLUSTER_EXCEPTION_TARGET_BLOCK_IDX = 6,
    /* Lane mask showing threads that are in a syscall
       Optional: Yes, use readSyscallCallDepth() if this attribute is not present
       Size: uint32_t */
    CUDBG_WARP_ATTRIBUTE_IN_SYSCALL_LANES                   = 7,

    CUDBG_WARP_ATTRIBUTE_COUNT,
} CUDBGWarpInfoAttribute_t;

/* uint32_t sized enum */
typedef enum {
    CUDBG_LANE_ATTRIBUTE_COUNT,
} CUDBGLaneInfoAttribute_t;

/* Sizes of the various structs returned by the batched device update APIs
   No explicit version field - implied by debugAPI major.minor.revision
*/
#pragma pack(push,1)
typedef struct {
    uint32_t requiredBufferSize;
    
    uint32_t deviceInfoSize;
    uint32_t deviceInfoAttributeSizes[32];

    uint32_t smInfoSize;
    uint32_t smInfoAttributeSizes[32];

    uint32_t warpInfoSize;
    uint32_t warpInfoAttributeSizes[32];
 
    uint32_t laneInfoSize;
    uint32_t laneInfoAttributeSizes[32];
} CUDBGDeviceInfoSizes;
#pragma pack(pop)

/* This is the first element in the deviceInfoBuffer, and is always present.
   getDeviceInfo() takes a deviceId as input, so no need to explicitly pass it back here
*/
#pragma pack(push,1)
typedef struct {
    CUDBGDeviceInfoQueryType_t responseType;

    /* Bitmask of CUDBGDeviceInfoAttribute_t enums for a Device */
    uint32_t deviceAttributeFlags;
} CUDBGDeviceInfo;
#pragma pack(pop)

/*
  Only "valid & updated" SMs/Warps/Lanes are included in the buffer, which allows us to determine
  indexes without having to encode an explicit ID field in the following buffer datastructures.
*/ 

/* Represents a SM */
#pragma pack(push,1)
typedef struct {
    uint64_t warpValidMask;
    uint64_t warpBrokenMask;

    /* Bitmask of CUDBGSmInfoAttribute_t enums for a SM */
    uint32_t smAttributeFlags;

    /* New elements are appended (but not added to the struct) */
} CUDBGSMInfo;
#pragma pack(pop)

/* Represents a Warp */
#pragma pack(push,1)
typedef struct {
    uint64_t gridId;

    CuDim3   blockIdx;
    CuDim3   baseThreadIdx;

    uint32_t validLanes;
    uint32_t activeLanes;

    /* Bitmask of CUDBGWarpInfoAttribute_t enums for warps and their lanes */
    uint32_t warpAttributeFlags;

    /* Optional fields based on the "warpAttributeFlags" bitmask */
} CUDBGWarpInfo;
#pragma pack(pop)
 
/* Represents a Lane */
#pragma pack(push,1)
typedef struct {
    uint64_t virtualPC;

    /* Optional: present only if CUDBG_WARP_ATTRIBUTE_LANE_ATTRIBUTES bit
       is set in CUDBGWarpInfo::warpAttributeFlags. Any additional data is
       appended here after this.

       uint32_t laneAttributeFlags;
     */
} CUDBGLaneInfo;
#pragma pack(pop)

/*----------------------- Coredump/snapshot support ------------------------*/

typedef enum {
    CUDBG_COREDUMP_DEFAULT_FLAGS                = 0,
    CUDBG_COREDUMP_SKIP_NONRELOCATED_ELF_IMAGES = (1 << 0),
    CUDBG_COREDUMP_SKIP_GLOBAL_MEMORY           = (1 << 1),
    CUDBG_COREDUMP_SKIP_SHARED_MEMORY           = (1 << 2),
    CUDBG_COREDUMP_SKIP_LOCAL_MEMORY            = (1 << 3),

    /* The value used to be SKIP_ABORT, but it's impossible to change this behavior.  */
    /* DEPRECATED_VALUE_DO_NOT_USE              = (1 << 4), */

    CUDBG_COREDUMP_SKIP_CONSTBANK_MEMORY        = (1 << 5),

    CUDBG_COREDUMP_LIGHTWEIGHT_FLAGS = CUDBG_COREDUMP_SKIP_NONRELOCATED_ELF_IMAGES
                                     | CUDBG_COREDUMP_SKIP_GLOBAL_MEMORY
                                     | CUDBG_COREDUMP_SKIP_SHARED_MEMORY
                                     | CUDBG_COREDUMP_SKIP_LOCAL_MEMORY
                                     | CUDBG_COREDUMP_SKIP_CONSTBANK_MEMORY
} CUDBGCoredumpGenerationFlags;

/*-------------------------------- CBU state -------------------------------*/

typedef enum {
     /* Force sizeof(CUDBGCbuThreadState)==4 */
    CUDBG_CBU_THREAD_STATE_INVALID = 0xFFFFFFFFU,
    CUDBG_CBU_THREAD_STATE_EXITED  = 0,
    CUDBG_CBU_THREAD_STATE_READY,
    CUDBG_CBU_THREAD_STATE_YIELDED,
    CUDBG_CBU_THREAD_STATE_SLEEP,
    CUDBG_CBU_THREAD_STATE_SLEEPYIELD,
    CUDBG_CBU_THREAD_STATE_READYATNEXT,
    CUDBG_CBU_THREAD_STATE_BLOCKEDPLUS,
    CUDBG_CBU_THREAD_STATE_BLOCKEDALL,
    CUDBG_CBU_THREAD_STATE_BLOCKEDCOLLECTIVE,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB0,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB1,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB2,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB3,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB4,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB5,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB6,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB7,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB8,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB9,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB10,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB11,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB12,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB13,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB14,
    CUDBG_CBU_THREAD_STATE_BLOCKEDB15,
} CUDBGCbuThreadState;
 
#pragma pack(push,1)
typedef struct
{
    uint32_t activeMask;
    uint32_t exitedMask;
    uint32_t collectiveMask;
    uint32_t barrierMasks[CUDBG_MAX_WARP_BARRIERS];
    CUDBGCbuThreadState threadState[CUDBG_MAX_LANES];
} CUDBGCbuWarpState;
#pragma pack(pop)

typedef enum {
    CUDBG_CUDA_LOG_LEVEL_INVALID = 0xFFFFFFFFU,
    CUDBG_CUDA_LOG_LEVEL_ERROR   = 0,
    CUDBG_CUDA_LOG_LEVEL_WARNING = 1,
} CUDBGCudaLogLevel;

#pragma pack(push,1)
typedef struct
{
    uint64_t unixTimestampNs;
    uint32_t osThreadId;
    CUDBGCudaLogLevel logLevel;
    char message[CUDBG_MAX_LOG_LEN];
} CUDBGCudaLogMessage;
#pragma pack(pop)

/*--------------------------------- Exports --------------------------------*/

typedef const struct CUDBGAPI_st *CUDBGAPI;

CUDBGResult cudbgGetAPI(uint32_t major, uint32_t minor, uint32_t rev, CUDBGAPI *api);
CUDBGResult cudbgGetAPIVersion(uint32_t *major, uint32_t *minor, uint32_t *rev);
CUDBGResult cudbgMain(int apiClientPid, uint32_t apiClientRevision, int sessionId, int attachState,
                      int attachEventInitialized, int writeFd, int detachFd, int attachStubInUse,
                      int enablePreemptionDebugging);
void cudbgApiInit(uint32_t arg);
void cudbgApiAttach(void);
void cudbgApiDetach(void);
void CUDBG_REPORT_DRIVER_API_ERROR(void);
void CUDBG_REPORT_DRIVER_INTERNAL_ERROR(void);

extern uint32_t CUDBG_IPC_FLAG_NAME;
extern uint32_t CUDBG_RPC_ENABLED;
extern uint32_t CUDBG_APICLIENT_PID;
extern uint32_t CUDBG_I_AM_DEBUGGER;
extern uint32_t CUDBG_DEBUGGER_INITIALIZED;
extern uint32_t CUDBG_APICLIENT_REVISION;
extern uint32_t CUDBG_SESSION_ID;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_CODE;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_FUNC_NAME_SIZE;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_FUNC_NAME_ADDR;
extern uint32_t CUDBG_REPORTED_DRIVER_API_ERROR_SOURCE;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_NAME_SIZE;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_NAME_ADDR;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_STRING_SIZE;
extern uint64_t CUDBG_REPORTED_DRIVER_API_ERROR_STRING_ADDR;
extern uint64_t CUDBG_REPORTED_DRIVER_INTERNAL_ERROR_CODE;
extern uint32_t CUDBG_ATTACH_HANDLER_AVAILABLE;
extern uint32_t CUDBG_ENABLE_LAUNCH_BLOCKING;
extern uint32_t CUDBG_ENABLE_PREEMPTION_DEBUGGING;
extern uint32_t CUDBG_RESUME_FOR_ATTACH_DETACH;
extern uint32_t CUDBG_REPORT_DRIVER_API_ERROR_FLAGS;
extern uint32_t CUDBG_DEBUGGER_CAPABILITIES;

/* Deprecated */
extern uint32_t CUDBG_DETACH_SUSPENDED_DEVICES_MASK;

/* Note this has no effect on virtual GPUs (such as NVIDIA GRID) */
extern uint32_t CUDBG_ENABLE_INTEGRATED_MEMCHECK;

struct CUDBGAPI_st {
    /* Initialization */
    CUDBGResult (*initialize)(void);
    CUDBGResult (*finalize)(void);

    /* Device Execution Control */
    CUDBGResult (*suspendDevice)(uint32_t dev);
    CUDBGResult (*resumeDevice)(uint32_t dev);
    CUDBGResult (*singleStepWarp40)(uint32_t dev, uint32_t sm, uint32_t wp);

    /* Breakpoints */
    CUDBGResult (*setBreakpoint31)(uint64_t addr);
    CUDBGResult (*unsetBreakpoint31)(uint64_t addr);

    /* Device State Inspection */
    CUDBGResult (*readGridId50)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t *gridId);
    CUDBGResult (*readBlockIdx32)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim2 *blockIdx);
    CUDBGResult (*readThreadIdx)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, CuDim3 *threadIdx);
    CUDBGResult (*readBrokenWarps)(uint32_t dev, uint32_t sm, uint64_t *brokenWarpsMask);
    CUDBGResult (*readValidWarps)(uint32_t dev, uint32_t sm, uint64_t *validWarpsMask);
    CUDBGResult (*readValidLanes)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t *validLanesMask);
    CUDBGResult (*readActiveLanes)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t *activeLanesMask);
    CUDBGResult (*readCodeMemory)(uint32_t dev, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readConstMemory)(uint32_t dev, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readGlobalMemory31)(uint32_t dev, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readParamMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readSharedMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readLocalMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*readRegister)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t regno, uint32_t *val);
    CUDBGResult (*readPC)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t *pc);
    CUDBGResult (*readVirtualPC)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t *pc);
    CUDBGResult (*readLaneStatus)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, bool *error);

    /* Device State Alteration */
    CUDBGResult (*writeGlobalMemory31)(uint32_t dev, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*writeParamMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*writeSharedMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*writeLocalMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*writeRegister)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t regno, uint32_t val);

    /* Grid Properties */
    CUDBGResult (*getGridDim32)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim2 *gridDim);
    CUDBGResult (*getBlockDim)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *blockDim);
    CUDBGResult (*getTID)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t *tid);
    CUDBGResult (*getElfImage32)(uint32_t dev, uint32_t sm, uint32_t wp, bool relocated, void **elfImage, uint32_t *size);

    /* Device Properties */
    CUDBGResult (*getDeviceType)(uint32_t dev, char *buf, uint32_t sz);
    CUDBGResult (*getSmType)(uint32_t dev, char *buf, uint32_t sz);
    CUDBGResult (*getNumDevices)(uint32_t *numDev);
    CUDBGResult (*getNumSMs)(uint32_t dev, uint32_t *numSMs);
    CUDBGResult (*getNumWarps)(uint32_t dev, uint32_t *numWarps);
    CUDBGResult (*getNumLanes)(uint32_t dev, uint32_t *numLanes);
    CUDBGResult (*getNumRegisters)(uint32_t dev, uint32_t *numRegs);

    /* DWARF-related routines */
    CUDBGResult (*getPhysicalRegister30)(uint64_t pc, char *reg, uint32_t *buf, uint32_t sz, uint32_t *numPhysRegs, CUDBGRegClass *regClass);
    CUDBGResult (*disassemble)(uint32_t dev, uint64_t addr, uint32_t *instSize, char *buf, uint32_t sz);
    CUDBGResult (*isDeviceCodeAddress55)(uintptr_t addr, bool *isDeviceAddress);
    CUDBGResult (*lookupDeviceCodeSymbol)(char *symName, bool *symFound, uintptr_t *symAddr);

    /* Events */
    CUDBGResult (*setNotifyNewEventCallback31)(CUDBGNotifyNewEventCallback31 callback, void *data);
    CUDBGResult (*getNextEvent30)(CUDBGEvent30 *event);
    CUDBGResult (*acknowledgeEvent30)(CUDBGEvent30 *event);

    /* 3.1 Extensions */
    CUDBGResult (*getGridAttribute)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGAttribute attr, uint64_t *value);
    CUDBGResult (*getGridAttributes)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGAttributeValuePair *pairs, uint32_t numPairs);
    CUDBGResult (*getPhysicalRegister40)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t pc, char *reg, uint32_t *buf, uint32_t sz, uint32_t *numPhysRegs, CUDBGRegClass *regClass);
    CUDBGResult (*readLaneException)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, CUDBGException_t *exception);
    CUDBGResult (*getNextEvent32)(CUDBGEvent32 *event);
    CUDBGResult (*acknowledgeEvents42)(void);

    /* 3.1 - ABI */
    CUDBGResult (*readCallDepth32)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t *depth);
    CUDBGResult (*readReturnAddress32)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t level, uint64_t *ra);
    CUDBGResult (*readVirtualReturnAddress32)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t level, uint64_t *ra);

    /* 3.2 Extensions */
    CUDBGResult (*readGlobalMemory55)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*writeGlobalMemory55)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*readPinnedMemory)(uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*writePinnedMemory)(uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*setBreakpoint)(uint32_t dev, uint64_t addr);
    CUDBGResult (*unsetBreakpoint)(uint32_t dev, uint64_t addr);
    CUDBGResult (*setNotifyNewEventCallback40)(CUDBGNotifyNewEventCallback40 callback);

    /* 4.0 Extensions */
    CUDBGResult (*getNextEvent42)(CUDBGEvent42 *event);
    CUDBGResult (*readTextureMemory)(uint32_t devId, uint32_t vsm, uint32_t wp, uint32_t id, uint32_t dim, uint32_t *coords, void *buf, uint32_t sz);
    CUDBGResult (*readBlockIdx)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *blockIdx);
    CUDBGResult (*getGridDim)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *gridDim);
    CUDBGResult (*readCallDepth)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t *depth);
    CUDBGResult (*readReturnAddress)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t level, uint64_t *ra);
    CUDBGResult (*readVirtualReturnAddress)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t level, uint64_t *ra);
    CUDBGResult (*getElfImage)(uint32_t dev, uint32_t sm, uint32_t wp, bool relocated, void **elfImage, uint64_t *size);

    /* 4.1 Extensions */
    CUDBGResult (*getHostAddrFromDeviceAddr)(uint32_t dev, uint64_t device_addr, uint64_t *host_addr);
    CUDBGResult (*singleStepWarp41)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t *warpMask);
    CUDBGResult (*setNotifyNewEventCallback)(CUDBGNotifyNewEventCallback callback);
    CUDBGResult (*readSyscallCallDepth)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t *depth);

    /* 4.2 Extensions */
    CUDBGResult (*readTextureMemoryBindless)(uint32_t devId, uint32_t vsm, uint32_t wp, uint32_t texSymtabIndex, uint32_t dim, uint32_t *coords, void *buf, uint32_t sz);

    /* 5.0 Extensions */
    CUDBGResult (*clearAttachState)(void);
    CUDBGResult (*getNextSyncEvent50)(CUDBGEvent50 *event);
    CUDBGResult (*memcheckReadErrorAddress)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t *address, ptxStorageKind *storage);
    CUDBGResult (*acknowledgeSyncEvents)(void);
    CUDBGResult (*getNextAsyncEvent50)(CUDBGEvent50 *event);
    CUDBGResult (*requestCleanupOnDetach55)(void);
    CUDBGResult (*initializeAttachStub)(void);
    CUDBGResult (*getGridStatus50)(uint32_t dev, uint32_t gridId, CUDBGGridStatus *status);

    /* 5.5 Extensions */
    CUDBGResult (*getNextSyncEvent55)(CUDBGEvent55 *event);
    CUDBGResult (*getNextAsyncEvent55)(CUDBGEvent55 *event);
    CUDBGResult (*getGridInfo55)(uint32_t dev, uint64_t gridId64, CUDBGGridInfo55 *gridInfo);
    CUDBGResult (*readGridId)(uint32_t dev, uint32_t sm, uint32_t wp, uint64_t *gridId64);
    CUDBGResult (*getGridStatus)(uint32_t dev, uint64_t gridId64, CUDBGGridStatus *status);
    CUDBGResult (*setKernelLaunchNotificationMode)(CUDBGKernelLaunchNotifyMode mode);
    CUDBGResult (*getDevicePCIBusInfo)(uint32_t devId, uint32_t *pciBusId, uint32_t *pciDevId);
    CUDBGResult (*readDeviceExceptionState80)(uint32_t devId, uint64_t *exceptionSMMask);

   /* 6.0 Extensions */
    CUDBGResult (*getAdjustedCodeAddress)(uint32_t devId, uint64_t address, uint64_t *adjustedAddress, CUDBGAdjAddrAction adjAction);
    CUDBGResult (*readErrorPC)(uint32_t devId, uint32_t sm, uint32_t wp, uint64_t *errorPC, bool *errorPCValid);
    CUDBGResult (*getNextEvent)(CUDBGEventQueueType type, CUDBGEvent  *event);
    CUDBGResult (*getElfImageByHandle)(uint32_t devId, uint64_t handle, CUDBGElfImageType type, void *elfImage, uint64_t size);
    CUDBGResult (*resumeWarpsUntilPC)(uint32_t devId, uint32_t sm, uint64_t warpMask, uint64_t virtPC);
    CUDBGResult (*readWarpState60)(uint32_t devId, uint32_t sm, uint32_t wp, CUDBGWarpState60 *state);
    CUDBGResult (*readRegisterRange)(uint32_t devId, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t index, uint32_t registers_size, uint32_t *registers);
    CUDBGResult (*readGenericMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*writeGenericMemory)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*readGlobalMemory)(uint64_t addr, void *buf, uint32_t sz);
    CUDBGResult (*writeGlobalMemory)(uint64_t addr, const void *buf, uint32_t sz);
    CUDBGResult (*getManagedMemoryRegionInfo)(uint64_t startAddress, CUDBGMemoryInfo *memoryInfo, uint32_t memoryInfo_size, uint32_t *numEntries);
    CUDBGResult (*isDeviceCodeAddress)(uintptr_t addr, bool *isDeviceAddress);
    CUDBGResult (*requestCleanupOnDetach)(uint32_t appResumeFlag);

   /* 6.5 Extensions */
    CUDBGResult (*readPredicates)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t predicates_size, uint32_t *predicates);
    CUDBGResult (*writePredicates)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t predicates_size, const uint32_t *predicates);
    CUDBGResult (*getNumPredicates)(uint32_t dev, uint32_t *numPredicates);
    CUDBGResult (*readCCRegister)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t *val);
    CUDBGResult (*writeCCRegister)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint32_t val);

    CUDBGResult (*getDeviceName)(uint32_t dev, char *buf, uint32_t sz);
    CUDBGResult (*singleStepWarp65)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t nsteps, uint64_t *warpMask);

    /* 9.0 Extensions */
    CUDBGResult (*readDeviceExceptionState)(uint32_t devId, uint64_t *mask, uint32_t numWords);

    /* 10.0 Extensions */
    CUDBGResult (*getNumUniformRegisters)(uint32_t dev, uint32_t *numRegs);
    CUDBGResult (*readUniformRegisterRange)(uint32_t devId, uint32_t sm, uint32_t wp, uint32_t regno, uint32_t registers_size, uint32_t *registers);
    CUDBGResult (*writeUniformRegister)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t regno, uint32_t val);
    CUDBGResult (*getNumUniformPredicates)(uint32_t dev, uint32_t *numPredicates);
    CUDBGResult (*readUniformPredicates)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t predicates_size, uint32_t *predicates);
    CUDBGResult (*writeUniformPredicates)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t predicates_size, const uint32_t *predicates);

    /* 11.8 Extensions */
    CUDBGResult (*getLoadedFunctionInfo118)(uint32_t devId, uint64_t handle, CUDBGLoadedFunctionInfo *info, uint32_t numEntries);

    /* 12.0 Extensions */
    CUDBGResult (*getGridInfo120)(uint32_t dev, uint64_t gridId64, CUDBGGridInfo120 *gridInfo);
    CUDBGResult (*getClusterDim120)(uint32_t dev, uint64_t gridId64, CuDim3 *clusterDim);
    CUDBGResult (*readWarpState120)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGWarpState120 *state);
    CUDBGResult (*readClusterIdx)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *clusterIdx);

    /* 12.2 Extensions */
    CUDBGResult (*getErrorStringEx)(char *buf, uint32_t bufSz, uint32_t *msgSz);

    /* 12.3 Extensions */
    CUDBGResult (*getLoadedFunctionInfo)(uint32_t devId, uint64_t handle, CUDBGLoadedFunctionInfo *info, uint32_t startIndex, uint32_t numEntries);
    CUDBGResult (*generateCoredump)(const char* filename, CUDBGCoredumpGenerationFlags flags);
    CUDBGResult (*getConstBankAddress123)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t bank, uint32_t offset, uint64_t* address);

    /* 12.4 Extensions */
    CUDBGResult (*getDeviceInfoSizes)(uint32_t dev, CUDBGDeviceInfoSizes* sizes);
    CUDBGResult (*getDeviceInfo)(uint32_t dev, CUDBGDeviceInfoQueryType_t type, void *buffer, uint32_t length, uint32_t *dataLength);
    CUDBGResult (*getConstBankAddress)(uint32_t dev, uint64_t gridId64, uint32_t bank, uint64_t* address, uint32_t* size);
    CUDBGResult (*singleStepWarp)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t laneHint, uint32_t nsteps, uint32_t flags, uint64_t *warpMask);

    /* 12.5 Extensions */
    CUDBGResult (*readAllVirtualReturnAddresses)(uint32_t dev, uint32_t sm, uint32_t wp, uint32_t ln, uint64_t *addrs, uint32_t numAddrs, uint32_t* callDepth, uint32_t* syscallCallDepth);
    CUDBGResult (*getSupportedDebuggerCapabilities)(CUDBGCapabilityFlags* capabilities);
    CUDBGResult (*readSmException)(uint32_t dev, uint32_t sm, CUDBGException_t *exception, uint64_t *errorPC, bool *errorPCValid);

    /* 12.6 Extensions */
    CUDBGResult (*executeInternalCommand)(const char* command, char* resultBuffer, uint32_t sizeInBytes);

    /* 12.7 Extensions */
    CUDBGResult (*getGridInfo)(uint32_t dev, uint64_t gridId64, CUDBGGridInfo *gridInfo);
    CUDBGResult (*getClusterDim)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *clusterDim);
    CUDBGResult (*readWarpState127)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGWarpState127 *state);
    CUDBGResult (*getClusterExceptionTargetBlock)(uint32_t dev, uint32_t sm, uint32_t wp, CuDim3 *blockIdx, bool *blockIdxValid);

    /* 12.8 Extensions */
    CUDBGResult (*readWarpResources)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGWarpResources *resources);

    /* 12.9 Extensions */
    CUDBGResult (*getCbuWarpState)(uint32_t dev, uint32_t sm, uint64_t warpMask, CUDBGCbuWarpState* warpStates, uint32_t numWarpStates);
    CUDBGResult (*readWarpState)(uint32_t dev, uint32_t sm, uint32_t wp, CUDBGWarpState *state);
    CUDBGResult (*consumeCudaLogs)(CUDBGCudaLogMessage* logMessages, uint32_t numMessages, uint32_t* numConsumed);
    CUDBGResult (*readCPUCallStack)(uint32_t dev, uint64_t gridId64, uint64_t *addrs, uint32_t numAddrs, uint32_t* totalNumAddrs);
};

#ifdef __cplusplus
}
#endif

#endif
