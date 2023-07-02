from io import StringIO
from pathlib import Path


from xdsl.ir import MLContext
from xdsl.dialects.builtin import ModuleOp, Builtin
from xdsl.transforms.dead_code_elimination import DeadCodeElimination
from xdsl.transforms.riscv_register_allocation import RISCVRegisterAllocation
from xdsl.transforms.lower_riscv_func import LowerRISCVFunc

from xdsl.interpreters.riscv_emulator import run_riscv

from .frontend.ir_gen import IRGen
from .frontend.parser import Parser

from .rewrites.optimise_toy import OptimiseToy
from .rewrites.shape_inference import ShapeInferencePass
from .rewrites.inline_toy import InlineToyPass
from .rewrites.lower_toy_affine import LowerToAffinePass
from .rewrites.lower_to_toy_accelerator import (
    LowerToToyAccelerator,
    LowerToyAccelerator,
)
from .rewrites.mlir_opt import MLIROptPass
from .rewrites.setup_riscv_pass import FinalizeRiscvPass, SetupRiscvPass
from .rewrites.lower_printf_riscv import LowerPrintfRiscvPass

from .rewrites.lower_riscv_cf import LowerCfRiscvCfPass

from .rewrites.lower_scf_riscv import LowerScfRiscvPass
from .rewrites.lower_arith_riscv import LowerArithRiscvPass
from .rewrites.lower_memref_riscv import LowerMemrefToRiscv
from .rewrites.lower_func_riscv_func import LowerFuncToRiscvFunc

from .emulator.toy_accelerator_instructions import ToyAccelerator

from .dialects import toy
from xdsl.dialects import riscv, riscv_func, cf, scf, printf


def context() -> MLContext:
    ctx = MLContext()
    ctx.register_dialect(Builtin)
    ctx.register_dialect(toy.Toy)
    ctx.register_dialect(riscv.RISCV)
    ctx.register_dialect(riscv_func.RISCV_Func)
    ctx.register_dialect(cf.Cf)
    ctx.register_dialect(scf.Scf)
    ctx.register_dialect(printf.Printf)
    return ctx


def parse_toy(program: str, ctx: MLContext | None = None) -> ModuleOp:
    mlir_gen = IRGen()
    module_ast = Parser(Path("in_memory"), program).parseModule()
    module_op = mlir_gen.ir_gen_module(module_ast)
    return module_op


def transform(
    ctx: MLContext,
    module_op: ModuleOp,
    *,
    emit: str = "riscv-assembly",
    accelerate: bool
):
    # TODO: rename emit to target
    if emit == "toy":
        return

    OptimiseToy().apply(ctx, module_op)

    if emit == "toy-opt":
        return

    InlineToyPass().apply(ctx, module_op)

    if emit == "toy-inline":
        return

    ShapeInferencePass().apply(ctx, module_op)

    if emit == "toy-infer-shapes":
        return

    LowerToAffinePass().apply(ctx, module_op)
    module_op.verify()

    if accelerate:
        LowerToToyAccelerator().apply(ctx, module_op)
        module_op.verify()

    if emit == "affine":
        return

    MLIROptPass(
        [
            "--allow-unregistered-dialect",
            "--canonicalize",
            "--cse",
            "--lower-affine",
            "--mlir-print-op-generic",
        ]
    ).apply(ctx, module_op)

    if emit == "scf":
        return

    MLIROptPass(
        [
            "--allow-unregistered-dialect",
            "--canonicalize",
            "--cse",
            "--convert-scf-to-cf",
            "--mlir-print-op-generic",
        ]
    ).apply(ctx, module_op)

    if emit == "cf":
        return

    SetupRiscvPass().apply(ctx, module_op)
    LowerFuncToRiscvFunc().apply(ctx, module_op)
    LowerCfRiscvCfPass().apply(ctx, module_op)
    LowerToyAccelerator().apply(ctx, module_op)
    LowerScfRiscvPass().apply(ctx, module_op)
    DeadCodeElimination().apply(ctx, module_op)
    LowerArithRiscvPass().apply(ctx, module_op)
    LowerPrintfRiscvPass().apply(ctx, module_op)
    LowerMemrefToRiscv().apply(ctx, module_op)
    FinalizeRiscvPass().apply(ctx, module_op)

    DeadCodeElimination().apply(ctx, module_op)

    module_op.verify()

    if emit == "riscv":
        return

    LowerRISCVFunc(insert_exit_syscall=True).apply(ctx, module_op)
    RISCVRegisterAllocation().apply(ctx, module_op)

    module_op.verify()


def compile(program: str, *, accelerate: bool) -> str:
    ctx = context()

    op = parse_toy(program)
    transform(ctx, op, emit="riscv-regalloc", accelerate=accelerate)

    io = StringIO()
    riscv.print_assembly(op, io)

    return io.getvalue()


def emulate_riscv(program: str):
    run_riscv(program, extensions=[ToyAccelerator], unlimited_regs=True, verbosity=0)
