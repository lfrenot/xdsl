from typing import Sequence

from xdsl.dialects import builtin, riscv
from xdsl.dialects.builtin import AnyFloat
from xdsl.ir.core import Attribute, OpResult, SSAValue
from xdsl.pattern_rewriter import PatternRewriter


def cast_values_to_registers(
    operands: Sequence[SSAValue], rewriter: PatternRewriter
) -> list[OpResult]:
    results: list[OpResult] = []
    for op in operands:
        cast_type = riscv.RegisterType(riscv.Register())
        if isinstance(op.type, AnyFloat):
            cast_type = riscv.FloatRegisterType(riscv.Register())
        elif isinstance(op.type, builtin.IntegerType | builtin.IndexType):
            cast_type = riscv.RegisterType(riscv.Register())
        elif isinstance(op.type, riscv.RegisterType | riscv.FloatRegisterType):
            cast_type = op.type

        cast = builtin.UnrealizedConversionCastOp.get([op], (cast_type,))
        results.append(cast.results[0])
        rewriter.insert_op_before_matched_op(cast)
    return results


def get_type_size(t: Attribute) -> int:
    if isinstance(t, builtin.Float32Type):
        return 4
    elif isinstance(t, builtin.IntegerType):
        return t.width.data // 8
    raise NotImplementedError(f"Type {t} is not supported")
