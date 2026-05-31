# Restricted Python v1.0

import ast

class BreakException(Exception): __slots__ = ()
class ContinueException(Exception): __slots__ = ()

class RpyInterpreter(ast.NodeVisitor):
    __slots__ = (
        'env',
        'attrs_visit',
        'types_assign',
        'fns_call',
        'use_def',
        'use_lambda',
        'use_for',
        'use_while')

    VERSION = (1, 0, 0)
    VERSION_STR = '1.0'

    def init(self):
        self.env = {}
        self.attrs_visit = set()
        self.types_assign = None
        self.fns_call = None
        self.use_def = True
        self.use_lambda = True
        self.use_for = True
        self.use_while = True
        #|

    def visit_Import(self, node):
        raise RuntimeError("Import statements are not allowed")
        #|
    def visit_ImportFrom(self, node):
        raise RuntimeError("Import statements are not allowed")
        #|
    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            result = self.visit(node.values[0])
            for value in node.values[1:]:
                if not result:
                    return result
                result = self.visit(value)
            return result
        elif isinstance(node.op, ast.Or):
            result = self.visit(node.values[0])
            for value in node.values[1:]:
                if result:
                    return result
                result = self.visit(value)
            return result
        raise NotImplementedError(f"Unsupported BoolOp: {node.op}")
        #|
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        node_op = node.op

        if isinstance(node_op, ast.Add):
            return left + right
        elif isinstance(node_op, ast.Sub):
            return left - right
        elif isinstance(node_op, ast.Mult):
            return left * right
        elif isinstance(node_op, ast.Div):
            return left / right
        elif isinstance(node_op, ast.Mod):
            return left % right
        elif isinstance(node_op, ast.Pow):
            return left ** right
        elif isinstance(node_op, ast.LShift):
            return left << right
        elif isinstance(node_op, ast.RShift):
            return left >> right
        elif isinstance(node_op, ast.BitOr):
            return left | right
        elif isinstance(node_op, ast.BitXor):
            return left ^ right
        elif isinstance(node_op, ast.BitAnd):
            return left & right
        elif isinstance(node_op, ast.FloorDiv):
            return left // right
        else:
            raise NotImplementedError(f"Unsupported BinOp: {node_op}")
        #|
    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        node_op = node.op

        if isinstance(node_op, ast.Invert):
            return ~ operand
        if isinstance(node_op, ast.Not):
            return not operand
        if isinstance(node_op, ast.UAdd):
            return + operand
        if isinstance(node_op, ast.USub):
            return - operand

        raise NotImplementedError(f"Unsupported UnaryOp: {node_op}")
        #|
    def visit_Compare(self, node):
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Eq):
                if not (left == right):
                    return False
            elif isinstance(op, ast.NotEq):
                if not (left != right):
                    return False
            elif isinstance(op, ast.Lt):
                if not (left < right):
                    return False
            elif isinstance(op, ast.LtE):
                if not (left <= right):
                    return False
            elif isinstance(op, ast.Gt):
                if not (left > right):
                    return False
            elif isinstance(op, ast.GtE):
                if not (left >= right):
                    return False
            elif isinstance(op, ast.Is):
                if not (left is right):
                    return False
            elif isinstance(op, ast.IsNot):
                if not (left is not right):
                    return False
            elif isinstance(op, ast.In):
                if not (left in right):
                    return False
            elif isinstance(op, ast.NotIn):
                if not (left not in right):
                    return False
            else:
                raise NotImplementedError(f"Unsupported Compare: {op}")
            left = right
        return True
        #|

    def visit_NameConstant(self, node):
        return node.value
        #|
    def visit_Num(self, node):
        return node.n
        #|
    def visit_Str(self, node):
        return node.s
        #|
    def visit_List(self, node):
        return [self.visit(element) for element in node.elts]
        #|
    def visit_Tuple(self, node):
        return tuple(self.visit(element) for element in node.elts)
        #|
    def visit_Dict(self, node):
        return {self.visit(key): self.visit(value) for key, value in zip(node.keys, node.values)}
        #|
    def visit_Set(self, node):
        return {self.visit(element) for element in node.elts}
        #|
    def visit_Subscript(self, node):
        value = self.visit(node.value)
        key = self.visit(node.slice)
        return value[key]
        #|
    def visit_Index(self, node):
        return self.visit(node.value)
        #|
    def visit_Slice(self, node):
        return slice(
            self.visit(node.lower) if node.lower else None,
            self.visit(node.upper) if node.upper else None,
            self.visit(node.step) if node.step else None)
        #|
    def visit_Return(self, node):
        return self.visit(node.value)
        #|
    def visit_Constant(self, node):
        return node.value
        #|
    def visit_Name(self, node):
        if node.id in self.env:
            return self.env[node.id]
        raise NameError(f"Undefined variable '{node.id}'")
        #|
    def visit_Assign(self, node):
        value = self.visit(node.value)
        if self.types_assign is None or value.__class__ in self.types_assign: pass
        else:
            raise TypeError("Assigned value must be of a supported type")

        for target in node.targets:
            if isinstance(target, ast.Name):
                self.env[target.id] = value
            elif isinstance(target, (ast.Tuple, ast.List)):
                if isinstance(value, (tuple, list)):
                    if len(target.elts) != len(value):
                        raise ValueError("Mismatch in unpacking values")
                    for elt, val in zip(target.elts, value):
                        if isinstance(elt, ast.Name):
                            self.env[elt.id] = val
                        else:
                            raise NotImplementedError("Only simple variable targets are supported for unpacking")
        #|
    def visit_AugAssign(self, node):
        target = self.visit(node.target)
        value = self.visit(node.value)
        node_op = node.op

        if isinstance(node_op, ast.Add):
            result = target + value
        elif isinstance(node_op, ast.Sub):
            result = target - value
        elif isinstance(node_op, ast.Mult):
            result = target * value
        elif isinstance(node_op, ast.Div):
            result = target / value
        elif isinstance(node_op, ast.Mod):
            result = target % value
        elif isinstance(node_op, ast.Pow):
            result = target ** value
        elif isinstance(node_op, ast.LShift):
            result = target << value
        elif isinstance(node_op, ast.RShift):
            result = target >> value
        elif isinstance(node_op, ast.BitOr):
            result = target | value
        elif isinstance(node_op, ast.BitXor):
            result = target ^ value
        elif isinstance(node_op, ast.BitAnd):
            result = target & value
        elif isinstance(node_op, ast.FloorDiv):
            result = target // value
        else:
            raise NotImplementedError(f"Unsupported AugAssign: {node_op}")
        self.env[node.target.id] = result
        #|
    def visit_Expr(self, node):
        return self.visit(node.value)
        #|
    def visit_Lambda(self, node):
        if self.use_lambda is False:
            raise RuntimeError("Lambda are not allowed")

        defaults = {arg.arg: self.visit(d) for arg, d in zip(node.args.args[-len(node.args.defaults):], node.args.defaults)}
        return lambda *args, **kwargs: self.visit_Lambda_Function(node, args, kwargs, defaults)
        #|
    def visit_Lambda_Function(self, node, args, kwargs, defaults):
        env_backup = self.env.copy()
        for i, arg in enumerate(node.args.args):
            if i < len(args):
                self.env[arg.arg] = args[i]
            elif arg.arg in kwargs:
                self.env[arg.arg] = kwargs[arg.arg]
            elif arg.arg in defaults:
                self.env[arg.arg] = defaults[arg.arg]
            else:
                raise TypeError(f"{node.name}() missing required argument: '{arg.arg}'")
        result = self.visit(node.body)
        self.env = env_backup
        return result
        #|
    def visit_FunctionDef(self, node):
        if self.use_def is False:
            raise RuntimeError("FunctionDef are not allowed")

        defaults = {arg.arg: self.visit(d) for arg, d in zip(node.args.args[-len(node.args.defaults):], node.args.defaults)}
        def function(*args, **kwargs):
            return self.visit_Function(node, args, kwargs, defaults)
        self.env[node.name] = function
        #|
    def visit_Function(self, node, args, kwargs, defaults):
        env_backup = self.env.copy()
        for i, arg in enumerate(node.args.args):
            if i < len(args):
                self.env[arg.arg] = args[i]
            elif arg.arg in kwargs:
                self.env[arg.arg] = kwargs[arg.arg]
            elif arg.arg in defaults:
                self.env[arg.arg] = defaults[arg.arg]
            else:
                raise TypeError(f"{node.name}() missing required argument: '{arg.arg}'")
        result = None
        for stmt in node.body:
            result = self.visit(stmt)
        self.env = env_backup
        return result
        #|
    def visit_arguments(self, node):
        defaults = [self.visit(d) for d in node.defaults]
        return node.args, defaults
        #|
    def visit_keyword(self, node):
        return node.arg, self.visit(node.value)
        #|
    def visit_Call(self, node):
        func = self.visit(node.func)
        if self.fns_call is None or func in self.fns_call: pass
        else:
            raise RuntimeError(f"Function '{func.__name__}' is not allowed to be called")

        args = [self.visit(arg) for arg in node.args]
        keywords = {kw.arg: self.visit(kw.value) for kw in node.keywords}
        return func(*args, **keywords)
        #|
    def visit_Try(self, node):
        try:
            for stmt in node.body:
                self.visit(stmt)
        except Exception as e:
            for handler in node.handlers:
                if handler.type is None:  # Catch-all handler
                    for stmt in handler.body:
                        self.visit(stmt)
                elif isinstance(handler.type, ast.Tuple):
                    if any(isinstance(elt, ast.Name) and elt.id == e.__class__.__name__ for elt in handler.type.elts):
                        for stmt in handler.body:
                            self.visit(stmt)
                        break
                elif isinstance(handler.type, ast.Name) and handler.type.id == e.__class__.__name__:
                    for stmt in handler.body:
                        self.visit(stmt)
                    break
        else:
            for stmt in node.orelse:
                self.visit(stmt)
        finally:
            for stmt in node.finalbody:
                self.visit(stmt)
        #|
    def visit_If(self, node):
        if self.visit(node.test):
            for stmt in node.body:
                return self.visit(stmt)
        else:
            for stmt in node.orelse:
                return self.visit(stmt)
        #|
    def visit_For(self, node):
        if self.use_for is False:
            raise RuntimeError("'for' statement not allowed")

        targets = node.target
        iter_ = self.visit(node.iter)

        if isinstance(targets, ast.Tuple):
            for item in iter_:
                values = item
                for sub_target, value in zip(targets.elts, values):
                    if not isinstance(sub_target, ast.Name):
                        raise NotImplementedError("Only simple variable targets are supported for 'for' loops")
                    self.env[sub_target.id] = value
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except BreakException:
                    break
                except ContinueException:
                    continue
        else:
            if not isinstance(targets, ast.Name):
                raise NotImplementedError("Only simple variable targets are supported for 'for' loops")
            for item in iter_:
                self.env[targets.id] = item
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except BreakException:
                    break
                except ContinueException:
                    continue
        for stmt in node.orelse:
            return self.visit(stmt)
        #|
    def visit_While(self, node):
        if self.use_while is False:
            raise RuntimeError("'while' statement not allowed")

        while self.visit(node.test):
            try:
                for stmt in node.body:
                    self.visit(stmt)
            except BreakException:
                break
            except ContinueException:
                continue
        for stmt in node.orelse:
            return self.visit(stmt)
        #|
    def visit_Break(self, node):
        raise BreakException
        #|
    def visit_Continue(self, node):
        raise ContinueException
        #|
    def visit_Module(self, node):
        for n in node.body:
            self.visit(n)
        return self.env
        #|
    def visit_Attribute(self, node):
        value = self.visit(node.value)

        if hasattr(node, 'attr'):
            if node.attr.startswith('_'):
                raise RuntimeError("Accessing attributes starting with '_' is not allowed")

            if self.attrs_visit is None or value.__class__ in self.attrs_visit:
                return getattr(value, node.attr)

        return self.generic_visit(node)
        #|
    def visit(self, node, env=None):
        if env is None:
            return super().visit(node)

        old_env = self.env
        self.env = env
        result = super().visit(node)
        self.env = old_env
        return result
        #|


# if __name__ == "__main__":
#     from . _dev import _test_rpy
#     _test_rpy.main(ast, RpyInterpreter)