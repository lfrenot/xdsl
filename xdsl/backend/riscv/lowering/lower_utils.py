from typing import Sequence

from xdsl.dialects import builtin, riscv
from xdsl.dialects.builtin import AnyFloat
from xdsl.ir.core import Attribute, OpResult, SSAValue
from xdsl.pattern_rewriter import PatternRewriter


def cast_values_to_registers(
    operands: Sequence[SSAValue], rewriter: PatternRewriter
) -> list[OpResult]:
    if not operands:
        return []

    types: list[Attribute] = []
    for op in operands:
        if isinstance(op.type, AnyFloat):
            types.append(riscv.FloatRegisterType(riscv.Register()))
        elif isinstance(op.type, builtin.IntegerType | builtin.IndexType):
            types.append(riscv.RegisterType(riscv.Register()))
        elif isinstance(op.type, riscv.RegisterType | riscv.FloatRegisterType):
            types.append(op.type)
        else:
            types.append(riscv.RegisterType(riscv.Register()))

    cast = builtin.UnrealizedConversionCastOp.get(operands, types)
    rewriter.insert_op_before_matched_op(cast)
    return cast.results


def get_type_size(t: Attribute) -> int:
    if isinstance(t, builtin.Float32Type):
        return 4
    elif isinstance(t, builtin.IntegerType):
        return t.width.data // 8
    raise NotImplementedError(f"Type {t} is not supported")
