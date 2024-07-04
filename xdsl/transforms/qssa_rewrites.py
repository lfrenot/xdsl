from xdsl.context import MLContext
from xdsl.dialects import builtin
from xdsl.dialects.qssa import CNotGateOp, HGateOp, RZGateOp, Unitary
from xdsl.dialects.quantum import AngleAttr
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)


class HadamardPhaseRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: HGateOp, rewriter: PatternRewriter):
        rot_gate = op.operands[0].owner
        if not isinstance(rot_gate, RZGateOp):
            return

        h_gate = rot_gate.operands[0].owner
        if not isinstance(h_gate, HGateOp):
            return

        if AngleAttr.from_fraction(1, 2) == rot_gate.angle:
            new_angle = AngleAttr.from_fraction(-1, 2)
        elif rot_gate.angle == AngleAttr.from_fraction(-1, 2):
            new_angle = AngleAttr.from_fraction(1, 2)
        else:
            return

        a = RZGateOp(new_angle, h_gate.operands[0])

        rewriter.replace_op(h_gate, a)

        b = HGateOp(a.results[0])

        rewriter.replace_op(rot_gate, b)

        c = RZGateOp(new_angle, b.results[0])

        rewriter.replace_matched_op(c)


class HadamardCNotRewriter(RewritePattern):
    # ----------before_1--o--after_1---------
    #                     |
    # --before--before_2--x--after_2--after--
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: CNotGateOp, rewriter: PatternRewriter):
        if not len(op.results[1].uses) == 1:
            return
        before_2 = op.operands[1].owner
        (after_2_use,) = op.results[1].uses
        after_2 = after_2_use.operation
        if isinstance(after_2, HGateOp) and isinstance(before_2, HGateOp):
            if not len(op.results[0].uses) == 1:
                return
            before_1 = op.operands[0].owner
            (after_1_use,) = op.results[0].uses
            after_1 = after_1_use.operation
            if isinstance(after_1, HGateOp) and isinstance(before_1, HGateOp):
                new_cnot = CNotGateOp(before_2.operands[0], before_1.operands[0])
                rewriter.replace_matched_op(new_cnot)
                rewriter.replace_op(after_1, (), (new_cnot.results[1],))
                rewriter.replace_op(after_2, (), (new_cnot.results[0],))
                rewriter.erase_op(before_1)
                rewriter.erase_op(before_2)

        elif isinstance(after_2, RZGateOp) and isinstance(before_2, RZGateOp):
            pi_by_2 = AngleAttr.from_fraction(1, 2)
            if not (
                before_2.angle == -after_2.angle
                and (pi_by_2 == before_2.angle or pi_by_2 == after_2.angle)
            ):
                return
            before = before_2.operands[0].owner
            if not len(after_2.results[0].uses) == 1:
                return
            (after_use,) = after_2.results[0].uses
            after = after_use.operation
            if isinstance(before, HGateOp) and isinstance(after, HGateOp):
                rewriter.replace_op(before, (), (before.operands[0],))
                rewriter.replace_op(after, (), (after.operands[0],))
                rewriter.replace_op(
                    before_2, RZGateOp(after_2.angle, before_2.operands[0])
                )
                rewriter.replace_op(
                    after_2, RZGateOp(before_2.angle, after_2.operands[0])
                )


class ReduceHadamardPass(ModulePass):
    name = "reduce-hadamard"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp):
        pattern = GreedyRewritePatternApplier(
            [HadamardCNotRewriter(), HadamardPhaseRewriter()]
        )
        PatternRewriteWalker(pattern).rewrite_op(op)


class MergeRZGateRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: RZGateOp, rewriter: PatternRewriter):
        before = op.operands[0].owner
        if not isinstance(before, RZGateOp):
            return
        rewriter.replace_matched_op(
            RZGateOp(op.angle + before.angle, before.operands[0])
        )
        rewriter.erase_op(before)


class RemoveZeroRZRewriter(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: RZGateOp, rewriter: PatternRewriter):
        if not op.angle == AngleAttr.from_fraction(0, 1):
            return

        rewriter.replace_matched_op((), new_results=op.operands)


class CancelUnitary(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: Unitary, rewriter: PatternRewriter):
        if not len(op.results[0].uses) == 1:
            return
        (first_use,) = op.results[0].uses
        if not first_use.index == 0 or not op.can_cancel(first_use.operation):
            return
        for i, result in enumerate(op.results[1:], 1):
            if not len(result.uses) == 1:
                return
            (use,) = result.uses
            if not (use.operation == first_use.operation and use.index == i):
                return

        rewriter.replace_op(first_use.operation, (), first_use.operation.operands)
        rewriter.replace_matched_op((), op.operands)


class GateCancellation(ModulePass):
    name = "gate-cancellation"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        pattern = GreedyRewritePatternApplier(
            [CancelUnitary(), MergeRZGateRewriter(), RemoveZeroRZRewriter()]
        )
        PatternRewriteWalker(pattern).rewrite_op(op)
