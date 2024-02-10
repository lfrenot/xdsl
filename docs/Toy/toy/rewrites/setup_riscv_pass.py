from xdsl.builder import Builder, ImplicitBuilder
from xdsl.dialects import riscv
from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Block, MLContext, Region
from xdsl.passes import ModulePass


class SetupRiscvPass(ModulePass):
    name = "setup-lowering-to-riscv"

    def apply(self, ctx: MLContext, op: ModuleOp) -> None:
        builder = Builder.at_start(op.body.block)
        with ImplicitBuilder(builder):

            @Builder.implicit_region
            def heap_region():
                riscv.LabelOp("heap")
                riscv.DirectiveOp(".space", f"{1024}")  # 1kb

            riscv.AssemblySectionOp(".bss", heap_region)
            riscv.AssemblySectionOp(".data", Region(Block()))
