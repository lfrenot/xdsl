from xdsl.dialects import builtin
from xdsl.dialects.builtin import IntegerAttr
from xdsl.dialects.qssa import IdOp, QubitBase
from xdsl.ir import MLContext
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)
from xdsl.rewriter import InsertPoint


class NoLayerException(Exception):
    pass


def iter_input_layers(op: QubitBase):
    for operand in op.operands:
        assert isinstance(operand.owner, QubitBase)
        if operand.owner.layer is None:
            raise NoLayerException()
        yield operand.owner.layer.value.data


class AssignLayerRewritePattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: QubitBase, rewriter: PatternRewriter):
        if op.layer is not None:
            return
        try:
            max_layer = max(iter_input_layers(op), default=-1)
        except NoLayerException:
            return
        op.layer = IntegerAttr(max_layer + 1, 64)


class AddIdRewritePattern(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: QubitBase, rewriter: PatternRewriter):
        if op.layer is None:
            return
        for j, operand in enumerate(op.operands):
            owner = operand.owner
            assert isinstance(owner, QubitBase)

            if owner.layer is None:
                continue

            new_operand = operand

            for i in range(owner.layer.value.data + 1, op.layer.value.data):
                id_op = IdOp(new_operand, i)
                new_operand = id_op.result
                rewriter.insert_op(id_op, InsertPoint.before(op))

            op.operands[j] = new_operand


class AssignLayerPass(ModulePass):
    name = "assign-layers"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        PatternRewriteWalker(AssignLayerRewritePattern()).rewrite_op(op)
        PatternRewriteWalker(AddIdRewritePattern()).rewrite_op(op)
