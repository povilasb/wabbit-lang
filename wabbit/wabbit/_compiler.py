"""Compiles Wabbit code to LLVM IR.

Which then we can translate to machine code.
"""

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
        self._variables: dict[str, ir.AllocaInstr] = {}

        self._mod = ir.Module("wabbit")
        self._main_func = ir.Function(
            self._mod, ir.FunctionType(_TInt, []), name="main"
        )
        block = self._main_func.append_basic_block("entry")
        self._ir_builder = ir.IRBuilder(block)
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

    def to_llvm(self) -> str:
        self._ir_builder.ret(ir.Constant(_TInt, 0))
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
            self._ir_builder.call(self._print_int, [res])
        elif res.type == _TFloat:
            self._ir_builder.call(self._print_float, [res])
        elif res.type == _TBool:
            self._ir_builder.call(self._print_bool, [res])
        elif res.type == _TChar:
            self._ir_builder.call(self._print_char, [res])

    def visit_VarDecl(self, node: VarDecl) -> None:
        var_name = node.name.value
        if node.value:
            val = self.visit(node.value)
            if val.type == _TInt:
                var = self._ir_builder.alloca(_TInt, name=var_name)
            elif val.type == _TFloat:
                var = self._ir_builder.alloca(_TFloat, name=var_name)
            elif val.type == _TChar:
                var = self._ir_builder.alloca(_TChar, name=var_name)
            else:
                assert False
        else:
            val = _default_var_type(node)
            match node.type_:
                case Type(name="int"):
                    var = self._ir_builder.alloca(_TInt, name=var_name)
                case Type(name="float"):
                    var = self._ir_builder.alloca(_TFloat, name=var_name)
                case Type(name="char"):
                    var = self._ir_builder.alloca(_TBool, name=var_name)
                case Type(name="bool"):
                    var = self._ir_builder.alloca(_TBool, name=var_name)
                case _:
                    assert False

        self._ir_builder.store(val, var)
        self._variables[var_name] = var

    def visit_ConstDecl(self, node: ConstDecl) -> None:
        var_name = node.name.value
        val = self.visit(node.value)

        if val.type == _TInt:
            var = self._ir_builder.alloca(_TInt, name=var_name)
        elif val.type == _TFloat:
            var = self._ir_builder.alloca(_TFloat, name=var_name)
        elif val.type == _TChar:
            var = self._ir_builder.alloca(_TChar, name=var_name)
        else:
            assert False

        self._ir_builder.store(val, var)
        self._variables[var_name] = var

    def visit_Name(self, node: Name):
        return self._ir_builder.load(self._variables[node.value])

    def visit_BinOp(self, node: BinOp) -> t.Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        match node.operation:
            case "+":
                if left.type == _TFloat:
                    return self._ir_builder.fadd(left, right)
                else:
                    return self._ir_builder.add(left, right)
            case "-":
                if left.type == _TFloat:
                    return self._ir_builder.fsub(left, right)
                else:
                    return self._ir_builder.sub(left, right)
            case "*":
                if left.type == _TFloat:
                    return self._ir_builder.fmul(left, right)
                else:
                    return self._ir_builder.mul(left, right)
            case "/":
                if left.type == _TFloat:
                    return self._ir_builder.fdiv(left, right)
                else:
                    return self._ir_builder.sdiv(left, right)

    def visit_UnaryOp(self, node: UnaryOp) -> t.Any:
        match node.operation:
            case "-":
                val = self.visit(node.operand)
                if val.type == _TInt:
                    return self._ir_builder.neg(val)
                else:
                    return self._ir_builder.fneg(val)

            case "+":
                return self.visit(node.operand)

            case "!":
                val = self.visit(node.operand)
                return self._ir_builder.not_(val)

    def visit_LogicalOp(self, node: LogicalOp) -> t.Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        match node.operation:
            case "==":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered("==", left, right)
                else:
                    return self._ir_builder.icmp_signed("==", left, right)
            case "!=":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered("!=", left, right)
                else:
                    return self._ir_builder.icmp_signed("!=", left, right)
            case ">":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered(">", left, right)
                else:
                    return self._ir_builder.icmp_signed(">", left, right)
            case ">=":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered(">=", left, right)
                else:
                    return self._ir_builder.icmp_signed(">=", left, right)
            case "<":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered("<", left, right)
                else:
                    return self._ir_builder.icmp_signed("<", left, right)
            case "<=":
                if left.type == _TFloat:
                    return self._ir_builder.fcmp_ordered("<=", left, right)
                else:
                    return self._ir_builder.icmp_signed("<=", left, right)
            case "&&":
                return self._ir_builder.and_(left, right)
            case "||":
                return self._ir_builder.or_(left, right)
            case _:
                raise RuntimeError("not possible")

    def visit_Assignment(self, node: Assignment):
        assert isinstance(node.left, Name)
        var_name = node.left.value

        value = self.visit(node.right)
        var = self._variables[var_name]
        self._ir_builder.store(value, var)

        return value

    def visit_IfElse(self, node: IfElse) -> t.Any:
        test_res = self.visit(node.test)

        # TODO(povilas): self._curr_func()?
        then_block = self._next_block(self._main_func)
        else_block = self._next_block(self._main_func) if node.else_body else None
        merge_block = self._next_block(self._main_func)

        self._ir_builder.cbranch(test_res, then_block, else_block or merge_block)

        self._ir_builder.position_at_end(then_block)
        self.visit(node.body)
        self._ir_builder.branch(merge_block)

        if else_body := node.else_body:
            self._ir_builder.position_at_end(else_block)
            self.visit(else_body)
            self._ir_builder.branch(merge_block)

        self._ir_builder.position_at_end(merge_block)

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
        self._ir_builder.branch(loop_test_block)
        self._ir_builder.position_at_end(loop_test_block)
        test_res = self.visit(node.test)
        self._ir_builder.cbranch(test_res, loop_body_block, loop_exit_block)

        self._ir_builder.position_at_end(loop_body_block)
        self.visit(node.body)
        self._ir_builder.branch(loop_test_block)

        self._ir_builder.position_at_end(loop_exit_block)

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
