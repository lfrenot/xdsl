from abc import ABC
from typing import List

from xdsl.dialects import cf, riscv, riscv_func
from xdsl.dialects.builtin import ModuleOp, UnrealizedConversionCastOp
from xdsl.ir import Block, MLContext, Operation
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)


def label_block(
    block: Block, rewriter: PatternRewriter, at_start: bool = True, at_end: bool = False
) -> List[riscv.LabelOp]:
    labels: List[riscv.LabelOp] = []

    if at_start and isinstance(block.ops.first, riscv.LabelOp):
        at_start = False
        labels.append(block.ops.first)

    if at_end and isinstance(block.ops.last, riscv.LabelOp):
        at_end = False
        labels.append(block.ops.last)

    if (at_start or at_end) and (parent_region := block.parent):
        block_idx = parent_region.get_block_index(block)

        if at_start:
            label_start = "bb" + str(block_idx)
            label_op = riscv.LabelOp(label_start)
            label_block = Block([label_op, riscv.TermOp()])
            parent_region.insert_block(label_block, block_idx)

            labels.append(label_op)

        if at_end:
            label_end = "bb" + str(block_idx) + "e"
            label_op = riscv.LabelOp(label_end)
            label_block = Block([label_op, riscv.TermOp()])
            parent_region.insert_block(label_block, block_idx + 1)

            labels.append(label_op)

    return labels


def add_jump(block: Block, label: riscv.LabelOp) -> None:
    if parent_region := block.parent:
        block_idx = parent_region.get_block_index(block)
        jmp = riscv.JOp(label.label)
        parent_region.insert_block(Block([jmp]), block_idx + 1)

    return None


class LowerBlockArgs(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: riscv_func.FuncOp, rewriter: PatternRewriter
    ) -> None:
        for block in op.func_body.blocks:
            for i, arg in enumerate(block.args):
                reg_idx = op.func_body.get_block_index(block) * 100 + i
                rarg = riscv.GetRegisterOp(riscv.IntRegisterType(f"jba{reg_idx}"))
                arg.replace_by(rarg.res)
                rewriter.erase_block_argument(arg)
                rewriter.insert_op_at_start(rarg, block)


class LowerConditionalBranchToRISCV(RewritePattern, ABC):
    """ """

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: cf.ConditionalBranch, rewriter: PatternRewriter, /):
        _ = label_block(op.then_block, rewriter)
        else_labels = label_block(op.else_block, rewriter, True, True)
        add_jump(op.then_block, else_labels[1])

        then_idx = 0
        else_idx = 0
        if parent := op.then_block.parent:
            then_idx = parent.get_block_index(op.then_block)
        if parent := op.else_block.parent:
            else_idx = parent.get_block_index(op.else_block)

        to_replace: List[Operation] = []

        for i, arg in enumerate(op.then_arguments):
            reg_idx = then_idx * 100 + i
            cast = UnrealizedConversionCastOp.get(
                [arg], [riscv.IntRegisterType(f"jba{reg_idx}")]
            )
            to_replace.append(cast)

        for i, arg in enumerate(op.else_arguments):
            reg_idx = else_idx * 100 + i
            cast = UnrealizedConversionCastOp.get(
                [arg], [riscv.IntRegisterType(f"jba{reg_idx}")]
            )
            to_replace.append(cast)

        cond = UnrealizedConversionCastOp.get(
            [op.cond], [riscv.IntRegisterType.unallocated()]
        )
        zero = riscv.GetRegisterOp(riscv.Registers.ZERO)
        branch = riscv.BeqOp(cond.results[0], zero, else_labels[0].label)

        to_replace.append(cond)
        to_replace.append(zero)
        to_replace.append(branch)

        rewriter.replace_matched_op(to_replace)


class CfToRISCV(ModulePass):
    """ """

    name = "cf-to-riscv"

    # lower to func.call
    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        PatternRewriteWalker(
            GreedyRewritePatternApplier([LowerConditionalBranchToRISCV()])
        ).rewrite_module(op)
        PatternRewriteWalker(LowerBlockArgs()).rewrite_module(op)
