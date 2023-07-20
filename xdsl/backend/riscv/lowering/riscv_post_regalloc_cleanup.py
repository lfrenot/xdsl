from xdsl.dialects import builtin, riscv
from xdsl.dialects.builtin import ModuleOp
from xdsl.ir.core import MLContext, OpResult
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)
from xdsl.transforms.dead_code_elimination import dce


class HomogenizeRegisterCasts(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: builtin.UnrealizedConversionCastOp, rewriter: PatternRewriter
    ):
        """
        Update the type of the result of a no-op cast to the type of the operand after register allocation

        %8 = "builtin.unrealized_conversion_cast"(%7) : (!riscv.freg<j5>) -> f32
        %35, %36, %37 = "builtin.unrealized_conversion_cast"(%8, %18, %34) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
        """
        for operand, result in zip(op.operands, op.results):
            # look for casts with unallocated registers
            if isinstance(
                result.type, riscv.IntRegisterType | riscv.FloatRegisterType
            ) and (not result.type.is_allocated):
                if isinstance(operand.owner, builtin.UnrealizedConversionCastOp):
                    assert isinstance(operand, OpResult)

                    defining_cast = operand.owner
                    # operands are in the same order as results in UnrealizedConversionCastOp
                    defining_operand_idx = defining_cast.results.index(operand)
                    defining_operand_type = defining_cast.operands[
                        defining_operand_idx
                    ].type

                    result.type = defining_operand_type


class RISCVPostRegallocCleanup(ModulePass):
    name = "riscv-post-regalloc-cleanup"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        PatternRewriteWalker(HomogenizeRegisterCasts()).rewrite_module(op)
        dce(op)
