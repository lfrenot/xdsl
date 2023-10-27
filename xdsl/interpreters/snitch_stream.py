from collections.abc import Sequence
from dataclasses import dataclass
from functools import reduce
from itertools import accumulate
from operator import mul
from typing import Any

from xdsl.dialects import snitch_stream
from xdsl.interpreter import (
    Interpreter,
    InterpreterFunctions,
    PythonValues,
    ReturnedValues,
    impl,
    impl_terminator,
    register_impls,
)
from xdsl.interpreters.riscv import RawPtr, RiscvFunctions
from xdsl.interpreters.stream import (
    ReadableStream,
    WritableStream,
)
from xdsl.ir.affine import AffineExpr, AffineMap


def indexing_map_from_bounds(bounds: Sequence[int]) -> AffineMap:
    divs = tuple(accumulate(reversed(bounds), mul, initial=1))[-2::-1]
    return AffineMap(
        1,
        0,
        tuple(
            AffineExpr.dimension(0).floor_div(div) % bound
            if div != 1
            else AffineExpr.dimension(0) % bound
            for bound, div in zip(bounds, divs)
        ),
    )


def offset_map_from_strides(strides: Sequence[int]) -> AffineMap:
    if not strides:
        # Return empty map to avoid reducing over an empty sequence
        return AffineMap(1, 0, ())

    return AffineMap(
        len(strides),
        0,
        (
            reduce(
                lambda acc, m: acc + m,
                (AffineExpr.dimension(i) * stride for i, stride in enumerate(strides)),
            ),
        ),
    )


@dataclass
class StridePattern:
    ub: list[int]
    strides: list[int]

    @property
    def offset_expr(self) -> AffineExpr:
        indexing_map = indexing_map_from_bounds(self.ub)
        offset_map = offset_map_from_strides(self.strides)
        result_map = offset_map.compose(indexing_map)
        return result_map.results[0]


@dataclass
class StridedPointerInputStream(ReadableStream[float]):
    offset_expr: AffineExpr
    pointer: RawPtr
    index = -1

    def read(self) -> float:
        self.index += 1
        offset = self.offset_expr.eval((self.index,), ())
        return (self.pointer + offset).float64[0]


@dataclass
class StridedPointerOutputStream(WritableStream[float]):
    index = -1
    offset_expr: AffineExpr
    pointer: RawPtr

    def write(self, value: float) -> None:
        self.index += 1
        offset = self.offset_expr.eval((self.index,), ())
        (self.pointer + offset).float64[0] = value


@register_impls
class SnitchStreamFunctions(InterpreterFunctions):
    @impl(snitch_stream.GenericOp)
    def run_generic(
        self,
        interpreter: Interpreter,
        op: snitch_stream.GenericOp,
        args: tuple[Any, ...],
    ) -> PythonValues:
        repeat_count = args[0]
        input_streams: tuple[ReadableStream[Any], ...] = interpreter.get_values(
            op.inputs
        )
        output_streams: tuple[WritableStream[Any], ...] = interpreter.get_values(
            op.outputs
        )

        for _ in range(repeat_count):
            loop_args = tuple(i.read() for i in input_streams)
            loop_args = RiscvFunctions.set_reg_values(
                interpreter, op.body.block.args, loop_args
            )
            loop_results = interpreter.run_ssacfg_region(op.body, loop_args, "for_loop")
            for o, r in zip(output_streams, loop_results):
                o.write(r)

        return ()

    @impl(snitch_stream.StridePatternOp)
    def run_stride_pattern(
        self,
        interpreter: Interpreter,
        op: snitch_stream.StridePatternOp,
        args: PythonValues,
    ) -> PythonValues:
        return (StridePattern([b.data for b in op.ub], [s.data for s in op.strides]),)

    @impl(snitch_stream.StridedReadOp)
    def run_strided_read(
        self,
        interpreter: Interpreter,
        op: snitch_stream.StridedReadOp,
        args: tuple[Any, ...],
    ) -> PythonValues:
        (memref, pattern) = args
        memref: RawPtr = memref
        pattern: StridePattern = pattern

        input_stream_factory = StridedPointerInputStream(
            pattern.offset_expr,
            memref,
        )
        return (input_stream_factory,)

    @impl(snitch_stream.StridedWriteOp)
    def run_strided_write(
        self,
        interpreter: Interpreter,
        op: snitch_stream.StridedWriteOp,
        args: tuple[Any, ...],
    ) -> PythonValues:
        (memref, pattern) = args
        memref: RawPtr = memref
        pattern: StridePattern = pattern

        output_stream_factory = StridedPointerOutputStream(
            pattern.offset_expr,
            memref,
        )
        return (output_stream_factory,)

    @impl_terminator(snitch_stream.YieldOp)
    def run_br(
        self, interpreter: Interpreter, op: snitch_stream.YieldOp, args: tuple[Any, ...]
    ):
        return ReturnedValues(args), ()
