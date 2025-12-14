#!/usr/bin/env python3
# /qompassai/dotfiles/.config/pythonrc.py
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

import os
import sys

try:
    import atexit
    import readline
    import rlcompleter

    readline.parse_and_bind("tab: complete")

    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, histfile)

    print("✅ Enhanced interactive shell loaded (tab completion, history)")
except ImportError:
    print("⚠️  readline not available - basic shell mode")

import collections
import datetime
import functools
import inspect
import itertools
import json
import logging
import math
import pprint
import time
import traceback
import warnings
from pprint import pprint as pp
from typing import Any, Dict, List, Optional, Union


def info(obj):
    """Get detailed info about an object"""
    return {
        "type": type(obj).__name__,
        "module": getattr(type(obj), "__module__", "unknown"),
        "doc": obj.__doc__,
        "dir": [attr for attr in dir(obj) if not attr.startswith("_")],
    }


def timer(func):
    """Simple timing decorator"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result

    return wrapper


def clear():
    """Clear the screen"""
    os.system("cls" if os.name == "nt" else "clear")


def reload_module(module):
    """Reload a module for development"""
    import importlib

    return importlib.reload(module)


import builtins

builtins.info = info
builtins.pp = pp
builtins.clear = clear
builtins.timer = timer
builtins.reload_module = reload_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)


def show_env():
    """Display Python environment information"""
    import platform

    print(f"🐍 Python {sys.version}")
    print(f"💻 Platform: {platform.platform()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(
        f"🛠️  Available utility functions: info(), pp(), clear(), timer(), reload_module()"
    )


print("🚀 Welcome to the Qompass AI Python Environment!")
show_env()
print("\n" + "=" * 60)
