from abc import ABC

from xdsl.dialects.arith import signlessIntegerLike
from xdsl.ir import Attribute, Dialect, Operation, SSAValue
from xdsl.irdl import IRDLOperation, irdl_op_definition, operand_def, result_def
from xdsl.traits import Pure


class ModArithOp(IRDLOperation, ABC):
    pass


class BinaryOp(ModArithOp, ABC):
    lhs = operand_def(signlessIntegerLike)
    rhs = operand_def(signlessIntegerLike)
    output = result_def(signlessIntegerLike)
    # assemblyFormat ="$lhs $rhs attr-dict `:` type($output)"  # operands directive not in asm format
    traits = frozenset((Pure(),))

    def __init__(
        self,
        lhs: SSAValue | Operation,
        rhs: SSAValue | Operation,
        result_type: Attribute | None,
    ):
        if result_type is None:
            result_type = SSAValue.get(lhs).type

        super().__init__(operands=[lhs, rhs], result_types=[result_type])

    def verify_(self) -> None:
        # todo
        return super().verify_()


@irdl_op_definition
class AddOp(BinaryOp):
    name = "mod_arith.add"


ModArith = Dialect(
    "mod_arith",
    [AddOp],
)
