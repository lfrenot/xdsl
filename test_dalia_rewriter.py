from xdsl.dialects import builtin
from xdsl.ir.core import Operation
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
)
from xdsl.printer import Printer
from xdsl.xdsl_opt_main import xDSLOptMain


def get_all_possible_rewrites(self: PatternRewriteWalker, op: builtin.ModuleOp) -> None:
    if isinstance(self.pattern, GreedyRewritePatternApplier):
        patterns = self.pattern.rewrite_patterns
    else:
        patterns = [self.pattern]

    old_module = op.clone()
    num_ops = len(list(old_module.walk()))

    current_module = old_module.clone()

    res: dict[tuple[Operation, str], builtin.ModuleOp] = {}

    for op_idx in range(num_ops):
        matched_op = list(current_module.walk())[op_idx]
        for pattern in patterns:
            rewriter = PatternRewriter(matched_op)
            pattern.match_and_rewrite(matched_op, rewriter)
            if rewriter.has_done_action:
                res[(matched_op, pattern.__class__.__name__)] = current_module
                current_module = old_module.clone()
                matched_op = list(current_module.walk())[op_idx]

    for (operation, pattern_name), res_module in res.items():
        print(f"Rewrite pattern: {pattern_name}")
        printer = Printer()
        print("Matched operation: ")
        printer.print_op(operation)
        print("\nResulting module: ")
        printer.print_op(res_module)
        print()


PatternRewriteWalker.rewrite_module = get_all_possible_rewrites

xDSLOptMain().run()
