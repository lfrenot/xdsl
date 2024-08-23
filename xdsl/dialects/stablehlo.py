"""
https://github.com/openxla/stablehlo/blob/main/docs/spec.md

StableHLO is an operation set for high-level operations (HLO) in machine learning (ML) models.
StableHLO works as a portability layer between different ML frameworks and ML compilers:
ML frameworks that produce StableHLO programs are compatible with ML compilers that consume StableHLO programs.
"""

import abc
from collections.abc import Sequence
from typing import Annotated, TypeAlias, cast

from xdsl.dialects.builtin import (
    I64,
    AnyTensorType,
    ArrayAttr,
    DenseArrayBase,
    IntegerAttr,
    IntegerType,
    TensorType,
    i64,
)
from xdsl.ir import (
    Attribute,
    Dialect,
    EnumAttribute,
    ParametrizedAttribute,
    Region,
    SpacedOpaqueSyntaxAttribute,
    SSAValue,
    StrEnum,
)
from xdsl.irdl import (
    ConstraintVar,
    IRDLOperation,
    ParameterDef,
    SameVariadicOperandSize,
    attr_def,
    irdl_attr_definition,
    irdl_op_definition,
    operand_def,
    region_def,
    result_def,
    var_operand_def,
    var_result_def,
)
from xdsl.parser import AttrParser
from xdsl.printer import Printer
from xdsl.traits import IsTerminator
from xdsl.utils.exceptions import VerifyException

# region Abstract Base Classes


class ElementwiseBinaryOperation(IRDLOperation, abc.ABC):
    # TODO: Remove this constraint for complex types.
    T = Annotated[AnyTensorType, ConstraintVar("T")]

    lhs = operand_def(T)
    rhs = operand_def(T)

    result = result_def(T)

    def __init__(
        self, lhs: SSAValue, rhs: SSAValue, result_type: Attribute | None = None
    ):
        if result_type is None:
            result_type = lhs.type
        super().__init__(operands=(lhs, rhs), result_types=(result_type,))


# endregion

# region Attributes


class Precision(StrEnum):
    """
    XLA precision for an operand. Has backend specific meaning.
    """

    DEFAULT = "DEFAULT"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"


@irdl_attr_definition
class PrecisionAttr(EnumAttribute[Precision], SpacedOpaqueSyntaxAttribute):
    """
    XLA precision for an operand. Has backend specific meaning.

    https://github.com/openxla/stablehlo/blob/b075e948092d8a27ed0be48f4f8dbaa6df7e2e3e/stablehlo/dialect/StablehloEnums.td#L46
    """

    name = "stablehlo.precision"


@irdl_attr_definition
class DotAttr(ParametrizedAttribute):
    """
    Attribute that models the dimension information for dot.

    https://github.com/openxla/stablehlo/blob/b075e948092d8a27ed0be48f4f8dbaa6df7e2e3e/stablehlo/dialect/StablehloAttrs.td#L82
    """

    name = "stablehlo.dot"

    lhs_batching_dimensions: ParameterDef[ArrayAttr[IntegerAttr[I64]]]
    rhs_batching_dimensions: ParameterDef[ArrayAttr[IntegerAttr[I64]]]
    lhs_contracting_dimensions: ParameterDef[ArrayAttr[IntegerAttr[I64]]]
    rhs_contracting_dimensions: ParameterDef[ArrayAttr[IntegerAttr[I64]]]

    def print_parameters(self, printer: Printer) -> None:
        with printer.in_angle_brackets():
            with printer.indented():
                printer.print_string("\nlhs_batching_dimensions = [")
                printer.print_list(
                    self.lhs_batching_dimensions.data,
                    lambda dim: printer.print_string(f"{dim.value.data}"),
                )
                printer.print_string("],")
                printer.print_string("\nrhs_batching_dimensions = [")
                printer.print_list(
                    self.rhs_batching_dimensions.data,
                    lambda dim: printer.print_string(f"{dim.value.data}"),
                )
                printer.print_string("],")
                printer.print_string("\nlhs_contracting_dimensions = [")
                printer.print_list(
                    self.lhs_contracting_dimensions.data,
                    lambda dim: printer.print_string(f"{dim.value.data}"),
                )
                printer.print_string("],")
                printer.print_string("\nrhs_contracting_dimensions = [")
                printer.print_list(
                    self.rhs_contracting_dimensions.data,
                    lambda dim: printer.print_string(f"{dim.value.data}"),
                )
            printer.print_string("]\n")

    @classmethod
    def parse_parameters(cls, parser: AttrParser) -> Sequence[Attribute]:
        with parser.in_angle_brackets():
            parser.parse_characters("lhs_batching_dimensions")
            parser.parse_punctuation("=")
            lhs_batching_dimensions = parser.parse_comma_separated_list(
                AttrParser.Delimiter.SQUARE,
                lambda: IntegerAttr(parser.parse_integer(), i64),
            )
            parser.parse_punctuation(",")
            parser.parse_characters("rhs_batching_dimensions")
            parser.parse_punctuation("=")
            rhs_batching_dimensions = parser.parse_comma_separated_list(
                AttrParser.Delimiter.SQUARE,
                lambda: IntegerAttr(parser.parse_integer(), i64),
            )
            parser.parse_punctuation(",")
            parser.parse_characters("lhs_contracting_dimensions")
            parser.parse_punctuation("=")
            lhs_contracting_dimensions = parser.parse_comma_separated_list(
                AttrParser.Delimiter.SQUARE,
                lambda: IntegerAttr(parser.parse_integer(), i64),
            )
            parser.parse_punctuation(",")
            parser.parse_characters("rhs_contracting_dimensions")
            parser.parse_punctuation("=")
            rhs_contracting_dimensions = parser.parse_comma_separated_list(
                AttrParser.Delimiter.SQUARE,
                lambda: IntegerAttr(parser.parse_integer(), i64),
            )

            return (
                ArrayAttr(lhs_batching_dimensions),
                ArrayAttr(rhs_batching_dimensions),
                ArrayAttr(lhs_contracting_dimensions),
                ArrayAttr(rhs_contracting_dimensions),
            )


# endregion


@irdl_op_definition
class AbsOp(IRDLOperation):
    """
    Performs element-wise abs operation on operand tensor and produces a result tensor.
    Depending on the element type, does the following:

    * For signed integers: integer modulus.
    * For floats: abs from IEEE-754.
    * For complex numbers: complex modulus.
    * For quantized types: dequantize_op_quantize(abs, operand, type(result)).

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#abs
    """

    name = "stablehlo.abs"

    # TODO: Remove this constraint for complex types.
    T = Annotated[AnyTensorType, ConstraintVar("T")]

    operand = operand_def(T)
    result = result_def(T)

    def __init__(self, operand: SSAValue, result_type: Attribute | None = None):
        if result_type is None:
            # TODO: Constraints for complex types.
            result_type = operand.type
        super().__init__(operands=(operand,), result_types=(result_type,))


@irdl_op_definition
class AddOp(ElementwiseBinaryOperation):
    """
    Performs element-wise addition of two tensors `lhs` and `rhs` and produces a
    `result` tensor. Depending on the element type, does the following:

    * For booleans: logical OR.
    * For integers: integer addition.
    * For floats: `addition` from IEEE-754.
    * For complex numbers: complex addition.
    * For quantized types: `dequantize_op_quantize(add, lhs, rhs, type(result))`.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#add
    """

    name = "stablehlo.add"


IntegerTensorType: TypeAlias = TensorType[IntegerType]


@irdl_op_definition
class AndOp(IRDLOperation):
    """
    Performs element-wise AND of two tensors lhs and rhs and produces a result tensor. Depending on the element type, does the following:

    For booleans: logical AND.
    For integers: bitwise AND.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#and
    """

    name = "stablehlo.and"

    T = Annotated[IntegerTensorType, ConstraintVar("T")]

    lhs = operand_def(T)
    rhs = operand_def(T)

    result = result_def(T)

    def __init__(
        self, lhs: SSAValue, rhs: SSAValue, result_type: Attribute | None = None
    ):
        if result_type is None:
            result_type = lhs.type
        super().__init__(operands=(lhs, rhs), result_types=(result_type,))


@irdl_op_definition
class DotGeneralOp(IRDLOperation):
    """
    #### Semantics

    Computes dot products between slices of `lhs` and slices of `rhs` and produces a
    `result` tensor.

    `precision_config` controls the tradeoff between speed and accuracy for
    computations on accelerator backends. This can be one of the following (at the
    moment, the semantics of these enum values is underspecified, but we are
    planning to address this in
    [#755](https://github.com/openxla/stablehlo/issues/755)):

    * `DEFAULT`: Fastest calculation, but least accurate approximation to the
    original number.
    * `HIGH`: Slower calculation, but more accurate approximation to the
    original number.
    * `HIGHEST`: Slowest calculation, but most accurate approximation to the
    original number.

    A `DotAlgorithm` defines the main properties of the algorithm used to implement
    the dot operation, which also defines the precision. If the algorithm attribute
    fields are set, then the `precision_config` must be `DEFAULT`. `DotAlgorithms`
    do not have a default value, as the default parameters are implementation
    defined. As such, all dot algorithm fields may be set to `None` to specify an
    empty dot algorithm, which will instead use the `precision_config` value.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#dot_general
    """

    name = "stablehlo.dot_general"

    T = Annotated[IntegerTensorType, ConstraintVar("T")]

    lhs = operand_def(T)
    rhs = operand_def(T)

    result = result_def(T)

    dot_dimension_numbers = attr_def(DotAttr)
    precision_config = attr_def(ArrayAttr[PrecisionAttr])

    # TODO: Algorithm

    def __init__(
        self,
        lhs: SSAValue,
        rhs: SSAValue,
        result_type: Attribute,
        dot_dimension_numbers: DotAttr,
        precision_config: PrecisionAttr,
    ):
        super().__init__(
            operands=(lhs, rhs),
            result_types=(result_type,),
            attributes={
                "dot_dimension_numbers": dot_dimension_numbers,
                "precision_config": precision_config,
            },
        )

    # TODO: verification


@irdl_op_definition
class MultiplyOp(ElementwiseBinaryOperation):
    """
    Performs element-wise product of two tensors `lhs` and `rhs` and produces a
    `result` tensor. Depending on the element type, does the following:

    * For booleans: logical AND.
    * For integers: integer multiplication.
    * For floats: `multiplication` from IEEE-754.
    * For complex numbers: complex multiplication.
    * For quantized types:
    * `dequantize_op_quantize(multiply, lhs, rhs, type(result))`.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#multiply
    """

    name = "stablehlo.multiply"


@irdl_op_definition
class SubtractOp(ElementwiseBinaryOperation):
    """
    Performs element-wise subtraction of two tensors `lhs` and `rhs` and produces a
    `result` tensor. Depending on the element type, does the following:

    * For integers: integer subtraction.
    * For floats: `subtraction` from IEEE-754.
    * For complex numbers: complex subtraction.
    * For quantized types:
    * `dequantize_op_quantize(subtract, lhs, rhs, type(result))`.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#subtract
    """

    name = "stablehlo.subtract"


@irdl_op_definition
class ReduceOp(IRDLOperation):
    """
    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#reduce
    """

    name = "stablehlo.reduce"

    inputs = var_operand_def(AnyTensorType)
    init_values = var_operand_def()
    dimensions = attr_def(DenseArrayBase)
    res = var_result_def(AnyTensorType)
    body = region_def()

    irdl_options = (SameVariadicOperandSize(),)

    def __init__(
        self,
        inputs: Sequence[SSAValue],
        init_values: Sequence[SSAValue],
        dimensions: DenseArrayBase | Sequence[int],
        body: Region,
    ):
        if not isinstance(dimensions, DenseArrayBase):
            dimensions = DenseArrayBase.from_list(i64, dimensions)
        super().__init__(
            operands=(inputs, init_values),
            regions=(body,),
            attributes={
                "dimensions": dimensions,
            },
            result_types=(tuple(arg.type for arg in init_values),),
        )


@irdl_op_definition
class ReturnOp(IRDLOperation):
    """This op is un-documented.

    StableHLO's return is used inside of the bodies of StableHLO ops.
    It behaves like func.return but for StableHLO ops.
    The func.return op is used inside of func.func op.

    https://discord.com/channels/999073994483433573/1259494021269688360/1259992088565645312
    """

    name = "stablehlo.return"

    input = var_operand_def(AnyTensorType)
    traits = frozenset([IsTerminator()])

    def __init__(self, input: list[SSAValue]):
        super().__init__(operands=(input,))


@irdl_op_definition
class TransposeOp(IRDLOperation):
    """
    Permutes the dimensions of `operand` tensor using `permutation` and produces a
    `result` tensor. More formally, `result[result_index] = operand[operand_index]`
    where `result_index[d] = operand_index[permutation[d]]`.

    https://github.com/openxla/stablehlo/blob/main/docs/spec.md#transpose
    """

    name = "stablehlo.transpose"

    ElementType = Annotated[Attribute, ConstraintVar("ElementType")]

    operand = operand_def(TensorType[ElementType])
    result = result_def(TensorType[ElementType])
    permutation = attr_def(DenseArrayBase)

    def __init__(
        self, operand: SSAValue, permutation: DenseArrayBase, result_type: Attribute
    ):
        super().__init__(
            operands=(operand,),
            result_types=(result_type,),
            attributes={"permutation": permutation},
        )

    def get_permutation(self) -> tuple[int, ...]:
        return cast(tuple[int, ...], self.permutation.as_tuple())

    def verify_(self) -> None:
        # Operand and result types are checked before the custom `verify_`
        o_type = cast(TensorType[Attribute], self.operand.type)
        r_type = cast(TensorType[Attribute], self.result.type)

        o_shape = o_type.get_shape()
        r_shape = r_type.get_shape()

        # TODO: Quantization constraints
        # `permutation` is a permutation of `range(rank(operand))`
        permutation = self.get_permutation()
        if sorted(permutation) != list(range(len(o_shape))):
            raise VerifyException(
                f"Permutation {permutation} of transpose must be a permutation of "
                f"range({len(o_shape)})"
            )

        # `shape(result) = dim(operand, permutation...)`
        for i, dim in enumerate(permutation):
            if r_shape[i] != o_shape[dim]:
                raise VerifyException(
                    f"Permutation mismatch at dimension {i}, expected {o_shape[dim]}"
                )


StableHLO = Dialect(
    "stablehlo",
    [
        AbsOp,
        AddOp,
        AndOp,
        DotGeneralOp,
        MultiplyOp,
        ReduceOp,
        ReturnOp,
        SubtractOp,
        TransposeOp,
    ],
    [
        DotAttr,
        PrecisionAttr,
    ],
)
