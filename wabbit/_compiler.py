"""Compiles Wabbit code to LLVM IR.

Which then we can translate to machine code.
"""

import typing as t

from llvmlite import ir

from ._ast import *


_TInt = ir.IntType(32)
_TFloat = ir.DoubleType()
_TBool = ir.IntType(1)
_TChar = ir.IntType(8)
_TVoid = ir.VoidType()


# Note that compiler doesn't do any const, var definition, type checking, etc.
# This will be done earlier by another visitor - "type checker".
class Compiler(Visitor):
    def __init__(self) -> None:
        self._global_variables: dict[str, ir.AllocaInstr] = {}
        # Variables declared in the current context - changes when building a function.
        self._current_variables: dict[str, ir.AllocaInstr] = self._global_variables
        self._functions: dict[str, ir.Function] = {}

        self._mod = ir.Module("wabbit")
        self._main_func = ir.Function(
            self._mod, ir.FunctionType(_TInt, []), name="main"
        )
        block = self._main_func.append_basic_block("main")
        # IR builder for the `main` function block.
        self._main_builder = ir.IRBuilder(block)

        self._print_int = ir.Function(
            self._mod, ir.FunctionType(_TVoid, [_TInt]), name="__wabbit_print_int"
        )
        self._print_float = ir.Function(
            self._mod, ir.FunctionType(_TVoid, [_TFloat]), name="__wabbit_print_float"
        )
        self._print_bool = ir.Function(
            self._mod, ir.FunctionType(_TVoid, [_TBool]), name="__wabbit_print_bool"
        )
        self._print_char = ir.Function(
            self._mod, ir.FunctionType(_TVoid, [_TChar]), name="__wabbit_print_char"
        )

        self._blocks_nr = 0
        # When building a function, we will use a different IR builder.
        self._curr_builder = self._main_builder

    def to_llvm(self) -> str:
        self._main_builder.ret(ir.Constant(_TInt, 0))
        return str(self._mod)

    def visit_Integer(self, node: Integer) -> ir.Value:
        return ir.Constant(_TInt, node.value)

    def visit_Float(self, node: Float) -> ir.Value:
        return ir.Constant(_TFloat, node.value)

    def visit_Boolean(self, node: Boolean) -> ir.Value:
        return ir.Constant(_TBool, int(node.value))

    def visit_Character(self, node: Character) -> ir.Value:
        return ir.Constant(_TChar, ord(node.value[0]))

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        res = self.visit(node.value)
        if res.type == _TInt:
            self._curr_builder.call(self._print_int, [res])
        elif res.type == _TFloat:
            self._curr_builder.call(self._print_float, [res])
        elif res.type == _TBool:
            self._curr_builder.call(self._print_bool, [res])
        elif res.type == _TChar:
            self._curr_builder.call(self._print_char, [res])

    def visit_VarDecl(self, node: VarDecl) -> None:
        var_name = node.name.value
        if node.value:
            val = self.visit(node.value)
            if val.type == _TInt:
                var = self._curr_builder.alloca(_TInt, name=var_name)
            elif val.type == _TFloat:
                var = self._curr_builder.alloca(_TFloat, name=var_name)
            elif val.type == _TChar:
                var = self._curr_builder.alloca(_TChar, name=var_name)
            if val.type == _TBool:
                var = self._curr_builder.alloca(_TBool, name=var_name)
            else:
                assert False
        else:
            val = _default_var_type(node)
            match node.type_:
                case Type(name="int"):
                    var = self._curr_builder.alloca(_TInt, name=var_name)
                case Type(name="float"):
                    var = self._curr_builder.alloca(_TFloat, name=var_name)
                case Type(name="char"):
                    var = self._curr_builder.alloca(_TBool, name=var_name)
                case Type(name="bool"):
                    var = self._curr_builder.alloca(_TBool, name=var_name)
                case _:
                    assert False

        self._curr_builder.store(val, var)
        self._current_variables[var_name] = var

    def visit_ConstDecl(self, node: ConstDecl) -> None:
        var_name = node.name.value
        val = self.visit(node.value)

        if val.type == _TInt:
            var = self._curr_builder.alloca(_TInt, name=var_name)
        elif val.type == _TFloat:
            var = self._curr_builder.alloca(_TFloat, name=var_name)
        elif val.type == _TChar:
            var = self._curr_builder.alloca(_TChar, name=var_name)
        else:
            assert False

        self._curr_builder.store(val, var)
        self._current_variables[var_name] = var

    def visit_FuncDef(self, func_def: FuncDef) -> None:
        arg_types = [_var_type(a.type_) for a in func_def.args]
        ret_type = _var_type(func_def.return_type)
        func_name = func_def.name.value
        f = ir.Function(self._mod, ir.FunctionType(ret_type, arg_types), func_name)

        block = self._next_block(f)
        # So that other visitor methods would build IR instructions into this block.
        self._curr_builder = ir.IRBuilder(block)
        self._current_variables = {}

        for i, arg in enumerate(f.args):
            var_name = func_def.args[i].name.value
            var = self._curr_builder.alloca(arg.type, name=var_name)
            self._curr_builder.store(arg, var)
            self._current_variables[var_name] = var

        self.visit(func_def.body)
        self._functions[func_name] = f

        self._curr_builder = self._main_builder
        self._current_variables = self._global_variables

    def visit_Return(self, node: Return) -> t.Any:
        expr = self.visit(node.value)
        return self._curr_builder.ret(expr)

    def visit_FuncCall(self, node: FuncCall) -> t.Any:
        func = self._functions[node.name.value]
        args = [self.visit(a) for a in node.args]
        return self._curr_builder.call(func, args)

    def visit_Name(self, node: Name):
        return self._curr_builder.load(self._current_variables[node.value])

    def visit_BinOp(self, node: BinOp) -> t.Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        match node.operation:
            case "+":
                if left.type == _TFloat:
                    return self._curr_builder.fadd(left, right)
                else:
                    return self._curr_builder.add(left, right)
            case "-":
                if left.type == _TFloat:
                    return self._curr_builder.fsub(left, right)
                else:
                    return self._curr_builder.sub(left, right)
            case "*":
                if left.type == _TFloat:
                    return self._curr_builder.fmul(left, right)
                else:
                    return self._curr_builder.mul(left, right)
            case "/":
                if left.type == _TFloat:
                    return self._curr_builder.fdiv(left, right)
                else:
                    return self._curr_builder.sdiv(left, right)

    def visit_UnaryOp(self, node: UnaryOp) -> t.Any:
        match node.operation:
            case "-":
                val = self.visit(node.operand)
                if val.type == _TInt:
                    return self._curr_builder.neg(val)
                else:
                    return self._curr_builder.fneg(val)

            case "+":
                return self.visit(node.operand)

            case "!":
                val = self.visit(node.operand)
                return self._curr_builder.not_(val)

    def visit_LogicalOp(self, node: LogicalOp) -> t.Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        match node.operation:
            case "==":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered("==", left, right)
                else:
                    return self._curr_builder.icmp_signed("==", left, right)
            case "!=":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered("!=", left, right)
                else:
                    return self._curr_builder.icmp_signed("!=", left, right)
            case ">":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered(">", left, right)
                else:
                    return self._curr_builder.icmp_signed(">", left, right)
            case ">=":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered(">=", left, right)
                else:
                    return self._curr_builder.icmp_signed(">=", left, right)
            case "<":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered("<", left, right)
                else:
                    return self._curr_builder.icmp_signed("<", left, right)
            case "<=":
                if left.type == _TFloat:
                    return self._curr_builder.fcmp_ordered("<=", left, right)
                else:
                    return self._curr_builder.icmp_signed("<=", left, right)
            case "&&":
                return self._curr_builder.and_(left, right)
            case "||":
                return self._curr_builder.or_(left, right)
            case _:
                raise RuntimeError("not possible")

    def visit_Assignment(self, node: Assignment):
        assert isinstance(node.left, Name)
        var_name = node.left.value

        value = self.visit(node.right)
        var = self._current_variables[var_name]
        self._curr_builder.store(value, var)

        return value

    def visit_IfElse(self, node: IfElse) -> t.Any:
        test_res = self.visit(node.test)

        # TODO(povilas): self._curr_func()?
        then_block = self._next_block(self._main_func)
        else_block = self._next_block(self._main_func) if node.else_body else None
        merge_block = self._next_block(self._main_func)

        self._curr_builder.cbranch(test_res, then_block, else_block or merge_block)

        self._curr_builder.position_at_end(then_block)
        self.visit(node.body)
        self._curr_builder.branch(merge_block)

        if else_body := node.else_body:
            self._curr_builder.position_at_end(else_block)
            self.visit(else_body)
            self._curr_builder.branch(merge_block)

        self._curr_builder.position_at_end(merge_block)

    def visit_While(self, node: While) -> t.Any:
        """
        Generates code like this:

            while true {
                if test condition {
                    goto loop_body
                } else {
                    goto loop_exit
                }

                # loop_body
            }
            # loop_exit
        """
        loop_body_block = self._next_block(self._main_func)
        loop_exit_block = self._next_block(self._main_func)
        loop_test_block = self._next_block(self._main_func)

        # Seems like we always need to branch into the label.
        self._curr_builder.branch(loop_test_block)
        self._curr_builder.position_at_end(loop_test_block)
        test_res = self.visit(node.test)
        self._curr_builder.cbranch(test_res, loop_body_block, loop_exit_block)

        self._curr_builder.position_at_end(loop_body_block)
        self.visit(node.body)
        self._curr_builder.branch(loop_test_block)

        self._curr_builder.position_at_end(loop_exit_block)

    def visit_Statements(self, node: Statements) -> None:
        for n in node.nodes:
            self.visit(n)

    def visit_ExprAsStatement(self, node: ExprAsStatement) -> t.Any:
        self.visit(node.expr)

    def _next_block(self, func: ir.Function) -> ir.Block:
        return func.append_basic_block(self._next_block_name())

    def _next_block_name(self) -> str:
        self._blocks_nr += 1
        return f"block_{self._blocks_nr}"


def _default_var_type(node: VarDecl) -> ir.Value:
    match node.type_:
        case Type(name="int"):
            return ir.Constant(_TInt, "0")
        case Type(name="float"):
            return ir.Constant(_TFloat, "0.0")
        case Type(name="bool"):
            return ir.Constant(_TBool, "0")
        case Type(name="char"):
            return ir.Constant(_TChar, "0")
        case _:
            assert False, f"Unknown variable type: {node.type_}"


def _var_type(node: Type) -> ir.Type:
    match node:
        case Type(name="int"):
            return _TInt
        case Type(name="float"):
            return _TFloat
        case Type(name="bool"):
            return _TBool
        case Type(name="char"):
            return _TChar
        case _:
            assert False, f"Unknown variable type: {node}"
