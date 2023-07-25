from abc import ABC
from typing import List

from xdsl.dialects import builtin, cf, riscv, riscv_func
from xdsl.dialects.builtin import AnyFloat, ModuleOp, UnrealizedConversionCastOp
from xdsl.ir import Block, MLContext, Operation
from xdsl.ir.core import Region
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)
from xdsl.rewriter import Rewriter


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
                reg_idx = hash(block) + i

                if isinstance(arg.type, AnyFloat):
                    rarg = riscv.GetFloatRegisterOp(
                        riscv.FloatRegisterType(f"jba{reg_idx}")
                    )
                else:
                    rarg = riscv.GetRegisterOp(riscv.IntRegisterType(f"jba{reg_idx}"))
                # arg.replace_by(rarg.res)

                for use in set(arg.uses):
                    if isinstance(
                        use.operation, builtin.UnrealizedConversionCastOp
                    ) and isinstance(
                        use.operation.results[0].type,
                        riscv.IntRegisterType | riscv.FloatRegisterType,
                    ):
                        for res in use.operation.results:
                            res.replace_by(rarg.res)
                        rewriter.erase_op(use.operation)
                    else:
                        use.operation.replace_operand(use.index, rarg.res)

                rewriter.erase_block_argument(arg)
                rewriter.insert_op_at_start(rarg, block)


class LowerConditionalBranchToRISCV(RewritePattern, ABC):
    """ """

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: cf.ConditionalBranch, rewriter: PatternRewriter, /):
        _ = label_block(op.then_block, rewriter)
        else_labels = label_block(op.else_block, rewriter, True, True)
        add_jump(op.then_block, else_labels[1])

        to_replace: List[Operation] = []

        for i, arg in enumerate(op.then_arguments):
            reg_idx = hash(op.then_block) + i

            new_block_arg = (
                riscv.FloatRegisterType(f"jba{reg_idx}")
                if isinstance(arg.type, AnyFloat)
                else riscv.IntRegisterType(f"jba{reg_idx}")
            )
            if isinstance(arg.type, AnyFloat):
                new_block_arg = riscv.FloatRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.FloatRegisterType.unallocated(),)
                    ),
                    n := riscv.FCvtWSOp(r.results[0]),
                    riscv.FMvWXOp(n.results[0], rd=new_block_arg),
                ]
            else:
                new_block_arg = riscv.IntRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.IntRegisterType.unallocated(),)
                    ),
                    riscv.MVOp(r.results[0], rd=new_block_arg),
                ]

            rewriter.insert_op_before_matched_op(cast)

            for c in cast:
                to_replace.append(c)

        for i, arg in enumerate(op.else_arguments):
            reg_idx = hash(op.else_block) + i
            if isinstance(arg.type, AnyFloat):
                new_block_arg = riscv.FloatRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.FloatRegisterType.unallocated(),)
                    ),
                    n := riscv.FCvtWSOp(r.results[0]),
                    riscv.FMvWXOp(n.results[0], rd=new_block_arg),
                ]
            else:
                new_block_arg = riscv.IntRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.IntRegisterType.unallocated(),)
                    ),
                    riscv.MVOp(r.results[0], rd=new_block_arg),
                ]

            rewriter.insert_op_before_matched_op(cast)
            for c in cast:
                to_replace.append(c)

        cond = UnrealizedConversionCastOp.get(
            [op.cond], [riscv.IntRegisterType.unallocated()]
        )
        zero = riscv.GetRegisterOp(riscv.Registers.ZERO)
        branch = riscv.BeqOp(cond.results[0], zero, else_labels[0].label)

        to_replace.append(cond)
        to_replace.append(zero)
        to_replace.append(branch)

        rewriter.replace_matched_op(to_replace)


class LowerUnconditionalBranchToRISCV(RewritePattern, ABC):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: cf.Branch, rewriter: PatternRewriter, /):
        succ_label = label_block(op.successor, rewriter, True, False)

        for i, arg in enumerate(op.arguments):
            assert isinstance(op.successor.parent, Region)
            reg_idx = hash(op.successor) + i
            print(f"{op.successor.parent} {reg_idx} {arg.type}")

            if isinstance(arg.type, AnyFloat):
                new_block_arg = riscv.FloatRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.FloatRegisterType.unallocated(),)
                    ),
                    n := riscv.FCvtWSOp(r.results[0]),
                    riscv.FMvWXOp(n.results[0], rd=new_block_arg),
                ]
            else:
                new_block_arg = riscv.IntRegisterType(f"jba{reg_idx}")
                cast = [
                    r := UnrealizedConversionCastOp.get(
                        [arg], (riscv.IntRegisterType.unallocated(),)
                    ),
                    riscv.MVOp(r.results[0], rd=new_block_arg),
                ]

            rewriter.insert_op_before_matched_op(cast)

        rewriter.replace_matched_op(riscv.JOp(succ_label[0].label))


class CfToRISCV(ModulePass):
    """ """

    name = "cf-to-riscv"

    # lower to func.call
    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [LowerConditionalBranchToRISCV(), LowerUnconditionalBranchToRISCV()]
            )
        ).rewrite_module(op)
        PatternRewriteWalker(LowerBlockArgs()).rewrite_module(op)
