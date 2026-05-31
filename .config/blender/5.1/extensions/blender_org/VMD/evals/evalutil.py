import bpy, math
from ast import parse

from .. rpy import RpyInterpreter

interpreter = RpyInterpreter()
interpreter.init()
interpreter.attrs_visit = None

NAMESPACE = {
    'bpy': bpy,
    'math': math,

    'abs': abs,
    'all': all,
    'any': any,
    'ascii': ascii,
    'bin': bin,
    'callable': callable,
    'chr': chr,
    'dir': dir,
    'divmod': divmod,
    'format': format,
    'getattr': getattr,
    'hasattr': hasattr,
    'hash': hash,
    'hex': hex,
    'id': id,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'iter': iter,
    'len': len,
    'max': max,
    'min': min,
    'next': next,
    'oct': oct,
    'ord': ord,
    'pow': pow,
    'print': print,
    'repr': repr,
    'round': round,
    'setattr': setattr,
    'sorted': sorted,
    'sum': sum,
    'bool': bool,
    'memoryview': memoryview,
    'bytearray': bytearray,
    'bytes': bytes,
    'classmethod': classmethod,
    'complex': complex,
    'dict': dict,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'frozenset': frozenset,
    'property': property,
    'int': int,
    'list': list,
    'map': map,
    'object': object,
    'range': range,
    'reversed': reversed,
    'set': set,
    'slice': slice,
    'staticmethod': staticmethod,
    'str': str,
    'super': super,
    'tuple': tuple,
    'type': type,
    'zip': zip,
}

def r_exec(code, globals=None):
    interpreter.env = NAMESPACE.copy()  if globals is None else NAMESPACE | globals

    try:
        return True, interpreter.visit(parse(code))
    except Exception as exx:
        return False, str(exx)
    #|
