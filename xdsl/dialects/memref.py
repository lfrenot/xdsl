from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Generic, TypeAlias, TypeVar, cast

from typing_extensions import Self

from xdsl.dialects.builtin import (
    AnyIntegerAttr,
    ArrayAttr,
    ContainerType,
    DenseArrayBase,
    DenseIntOrFPElementsAttr,
    IndexType,
    IntAttr,
    IntegerAttr,
    IntegerType,
    NoneAttr,
    ShapedType,
    StridedLayoutAttr,
    StringAttr,
    SymbolRefAttr,
    UnitAttr,
    i32,
    i64,
)
from xdsl.ir import (
    Attribute,
    Dialect,
    Operation,
    OpResult,
    ParametrizedAttribute,
    SSAValue,
    TypeAttribute,
)
from xdsl.irdl import (
    AnyAttr,
    AttrSizedOperandSegments,
    IRDLOperation,
    Operand,
    ParameterDef,
    VarOperand,
    irdl_attr_definition,
    irdl_op_definition,
    operand_def,
    opt_prop_def,
    prop_def,
    region_def,
    result_def,
    var_operand_def,
    var_result_def,
)
from xdsl.pattern_rewriter import RewritePattern
from xdsl.traits import (
    HasCanonicalisationPatternsTrait,
    HasParent,
    IsTerminator,
    SymbolOpInterface,
)
from xdsl.utils.deprecation import deprecated_constructor
from xdsl.utils.exceptions import VerifyException
from xdsl.utils.hints import isa

if TYPE_CHECKING:
    from xdsl.parser import AttrParser, Parser
    from xdsl.printer import Printer


_MemRefTypeElement = TypeVar("_MemRefTypeElement", bound=Attribute)


@irdl_attr_definition
class MemRefType(
    Generic[_MemRefTypeElement],
    ParametrizedAttribute,
    TypeAttribute,
    ShapedType,
    ContainerType[_MemRefTypeElement],
):
    name = "memref"

    shape: ParameterDef[ArrayAttr[IntAttr]]
    element_type: ParameterDef[_MemRefTypeElement]
    layout: ParameterDef[Attribute]
    memory_space: ParameterDef[Attribute]

    def __init__(
        self: MemRefType[_MemRefTypeElement],
        element_type: _MemRefTypeElement,
        shape: Iterable[int | IntAttr],
        layout: Attribute = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ):
        shape = ArrayAttr(
            [IntAttr(dim) if isinstance(dim, int) else dim for dim in shape]
        )
        super().__init__(
            [
                shape,
                element_type,
                layout,
                memory_space,
            ]
        )

    def get_num_dims(self) -> int:
        return len(self.shape.data)

    def get_shape(self) -> tuple[int, ...]:
        return tuple(i.data for i in self.shape.data)

    def get_element_type(self) -> _MemRefTypeElement:
        return self.element_type

    @deprecated_constructor
    @staticmethod
    def from_element_type_and_shape(
        referenced_type: _MemRefTypeElement,
        shape: Iterable[int | AnyIntegerAttr],
        layout: Attribute = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ) -> MemRefType[_MemRefTypeElement]:
        shape_int = [i if isinstance(i, int) else i.value.data for i in shape]
        return MemRefType(referenced_type, shape_int, layout, memory_space)

    @deprecated_constructor
    @staticmethod
    def from_params(
        referenced_type: _MemRefTypeElement,
        shape: ArrayAttr[AnyIntegerAttr] = ArrayAttr(
            [IntegerAttr.from_int_and_width(1, 64)]
        ),
        layout: Attribute = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ) -> MemRefType[_MemRefTypeElement]:
        shape_int = [i.value.data for i in shape.data]
        return MemRefType(referenced_type, shape_int, layout, memory_space)

    @classmethod
    def parse_parameters(cls, parser: AttrParser) -> list[Attribute]:
        parser.parse_punctuation("<", " in memref attribute")
        shape = parser.parse_attribute()
        parser.parse_punctuation(",", " between shape and element type parameters")
        type = parser.parse_attribute()
        # If we have a layout or a memory space, parse both of them.
        if parser.parse_optional_punctuation(",") is None:
            parser.parse_punctuation(">", " at end of memref attribute")
            return [shape, type, NoneAttr(), NoneAttr()]
        layout = parser.parse_attribute()
        parser.parse_punctuation(",", " between layout and memory space")
        memory_space = parser.parse_attribute()
        parser.parse_punctuation(">", " at end of memref attribute")

        return [shape, type, layout, memory_space]

    def print_parameters(self, printer: Printer) -> None:
        printer.print("<", self.shape, ", ", self.element_type)
        if self.layout != NoneAttr() or self.memory_space != NoneAttr():
            printer.print(", ", self.layout, ", ", self.memory_space)
        printer.print(">")


_UnrankedMemrefTypeElems = TypeVar(
    "_UnrankedMemrefTypeElems", bound=Attribute, covariant=True
)
_UnrankedMemrefTypeElemsInit = TypeVar("_UnrankedMemrefTypeElemsInit", bound=Attribute)


@irdl_attr_definition
class UnrankedMemrefType(
    Generic[_UnrankedMemrefTypeElems], ParametrizedAttribute, TypeAttribute
):
    name = "unranked_memref"

    element_type: ParameterDef[_UnrankedMemrefTypeElems]
    memory_space: ParameterDef[Attribute]

    @staticmethod
    def from_type(
        referenced_type: _UnrankedMemrefTypeElemsInit,
        memory_space: Attribute = NoneAttr(),
    ) -> UnrankedMemrefType[_UnrankedMemrefTypeElemsInit]:
        return UnrankedMemrefType([referenced_type, memory_space])


AnyUnrankedMemrefType: TypeAlias = UnrankedMemrefType[Attribute]


@irdl_op_definition
class Load(IRDLOperation):
    name = "memref.load"
    memref: Operand = operand_def(MemRefType[Attribute])
    indices: VarOperand = var_operand_def(IndexType)
    res: OpResult = result_def(AnyAttr())

    # TODO varargs for indexing, which must match the memref dimensions
    # Problem: memref dimensions require variadic type parameters,
    # which is subject to change

    def verify_(self):
        memref_type = self.memref.type
        if not isinstance(memref_type, MemRefType):
            raise VerifyException("expected a memreftype")

        memref_type = cast(MemRefType[Attribute], memref_type)

        if memref_type.element_type != self.res.type:
            raise Exception("expected return type to match the MemRef element type")

        if memref_type.get_num_dims() != len(self.indices):
            raise Exception("expected an index for each dimension")

    @classmethod
    def get(
        cls, ref: SSAValue | Operation, indices: Sequence[SSAValue | Operation]
    ) -> Self:
        ssa_value = SSAValue.get(ref)
        ssa_value_type = ssa_value.type
        ssa_value_type = cast(MemRefType[Attribute], ssa_value_type)
        return cls(operands=[ref, indices], result_types=[ssa_value_type.element_type])

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        unresolved_ref = parser.parse_unresolved_operand()
        unresolved_indices = parser.parse_comma_separated_list(
            parser.Delimiter.SQUARE, parser.parse_unresolved_operand
        )
        attributes = parser.parse_optional_attr_dict()
        parser.parse_punctuation(":")
        ref_type = parser.parse_attribute()
        resolved_ref = parser.resolve_operand(unresolved_ref, ref_type)
        resolved_indices = [
            parser.resolve_operand(index, IndexType()) for index in unresolved_indices
        ]
        res = cls.get(resolved_ref, resolved_indices)
        res.attributes.update(attributes)
        return res

    def print(self, printer: Printer):
        printer.print_string(" ")
        printer.print(self.memref)
        printer.print_string("[")
        printer.print_list(self.indices, printer.print_operand)
        printer.print_string("]")
        printer.print_op_attributes(self.attributes)
        printer.print_string(" : ")
        printer.print_attribute(self.memref.type)


@irdl_op_definition
class Store(IRDLOperation):
    name = "memref.store"
    value: Operand = operand_def(AnyAttr())
    memref: Operand = operand_def(MemRefType[Attribute])
    indices: VarOperand = var_operand_def(IndexType)

    def verify_(self):
        if not isinstance(memref_type := self.memref.type, MemRefType):
            raise VerifyException("expected a memreftype")

        memref_type = cast(MemRefType[Attribute], memref_type)

        if memref_type.element_type != self.value.type:
            raise Exception("Expected value type to match the MemRef element type")

        if memref_type.get_num_dims() != len(self.indices):
            raise Exception("Expected an index for each dimension")

    @classmethod
    def get(
        cls,
        value: Operation | SSAValue,
        ref: Operation | SSAValue,
        indices: Sequence[Operation | SSAValue],
    ) -> Self:
        return cls(operands=[value, ref, indices])

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        value = parser.parse_operand()
        parser.parse_punctuation(",")
        unresolved_ref = parser.parse_unresolved_operand()
        unresolved_indices = parser.parse_comma_separated_list(
            parser.Delimiter.SQUARE, parser.parse_unresolved_operand
        )
        attributes = parser.parse_optional_attr_dict()
        parser.parse_punctuation(":")
        ref_type = parser.parse_attribute()
        resolved_ref = parser.resolve_operand(unresolved_ref, ref_type)
        resolved_indices = [
            parser.resolve_operand(index, IndexType()) for index in unresolved_indices
        ]
        res = cls.get(value, resolved_ref, resolved_indices)
        res.attributes.update(attributes)
        return res

    def print(self, printer: Printer):
        printer.print_string(" ")
        printer.print(self.value)
        printer.print_string(", ")
        printer.print(self.memref)
        printer.print_string("[")
        printer.print_list(self.indices, printer.print_operand)
        printer.print_string("]")
        printer.print_op_attributes(self.attributes)
        printer.print_string(" : ")
        printer.print_attribute(self.memref.type)


@irdl_op_definition
class Alloc(IRDLOperation):
    name = "memref.alloc"

    dynamic_sizes: VarOperand = var_operand_def(IndexType)
    symbol_operands: VarOperand = var_operand_def(IndexType)

    memref: OpResult = result_def(MemRefType[Attribute])

    # TODO how to constraint the IntegerAttr type?
    alignment: AnyIntegerAttr | None = opt_prop_def(AnyIntegerAttr)

    irdl_options = [AttrSizedOperandSegments(as_property=True)]

    @staticmethod
    def get(
        return_type: Attribute,
        alignment: int | AnyIntegerAttr | None = None,
        shape: Iterable[int | IntAttr] | None = None,
        dynamic_sizes: Sequence[SSAValue | Operation] | None = None,
        layout: Attribute = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ) -> Alloc:
        if shape is None:
            shape = [1]

        if dynamic_sizes is None:
            dynamic_sizes = []

        if isinstance(alignment, int):
            alignment = IntegerAttr.from_int_and_width(alignment, 64)

        return Alloc.build(
            operands=[dynamic_sizes, []],
            result_types=[MemRefType(return_type, shape, layout, memory_space)],
            properties={
                "alignment": alignment,
            },
        )

    def verify_(self) -> None:
        memref_type = self.memref.type
        if not isinstance(memref_type, MemRefType):
            raise VerifyException("expected result to be a memref")
        memref_type = cast(MemRefType[Attribute], memref_type)

        dyn_dims = [x for x in memref_type.shape.data if x.data == -1]
        if len(dyn_dims) != len(self.dynamic_sizes):
            raise VerifyException(
                "op dimension operand count does not equal memref dynamic dimension count."
            )


@irdl_op_definition
class AllocaScopeOp(IRDLOperation):
    name = "memref.alloca_scope"

    res = var_result_def()

    scope = region_def()


@irdl_op_definition
class AllocaScopeReturnOp(IRDLOperation):
    name = "memref.alloca_scope.return"

    ops = var_operand_def()

    traits = frozenset([IsTerminator(), HasParent(AllocaScopeOp)])

    def verify_(self) -> None:
        parent = cast(AllocaScopeOp, self.parent_op())
        if any(op.type != res.type for op, res in zip(self.ops, parent.results)):
            raise VerifyException(
                "Expected operand types to match parent's return types."
            )


@irdl_op_definition
class Alloca(IRDLOperation):
    name = "memref.alloca"

    dynamic_sizes: VarOperand = var_operand_def(IndexType)
    symbol_operands: VarOperand = var_operand_def(IndexType)

    memref: OpResult = result_def(MemRefType[Attribute])

    # TODO how to constraint the IntegerAttr type?
    alignment: AnyIntegerAttr | None = opt_prop_def(AnyIntegerAttr)

    irdl_options = [AttrSizedOperandSegments(as_property=True)]

    @staticmethod
    def get(
        return_type: Attribute,
        alignment: int | AnyIntegerAttr | None = None,
        shape: Iterable[int | IntAttr] | None = None,
        dynamic_sizes: Sequence[SSAValue | Operation] | None = None,
        layout: Attribute = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ) -> Alloca:
        if shape is None:
            shape = [1]

        if dynamic_sizes is None:
            dynamic_sizes = []

        if isinstance(alignment, int):
            alignment = IntegerAttr.from_int_and_width(alignment, 64)

        return Alloca.build(
            operands=[dynamic_sizes, []],
            result_types=[MemRefType(return_type, shape, layout, memory_space)],
            properties={
                "alignment": alignment,
            },
        )

    def verify_(self) -> None:
        memref_type = self.memref.type
        if not isinstance(memref_type, MemRefType):
            raise VerifyException("expected result to be a memref")
        memref_type = cast(MemRefType[Attribute], memref_type)

        dyn_dims = [x for x in memref_type.shape.data if x.data == -1]
        if len(dyn_dims) != len(self.dynamic_sizes):
            raise VerifyException(
                "op dimension operand count does not equal memref dynamic dimension count."
            )


@irdl_op_definition
class Dealloc(IRDLOperation):
    name = "memref.dealloc"
    memref: Operand = operand_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])

    @staticmethod
    def get(operand: Operation | SSAValue) -> Dealloc:
        return Dealloc.build(operands=[operand])


@irdl_op_definition
class GetGlobal(IRDLOperation):
    name = "memref.get_global"
    memref: OpResult = result_def(MemRefType[Attribute])
    name_: SymbolRefAttr = prop_def(SymbolRefAttr, prop_name="name")

    @staticmethod
    def get(name: str, return_type: Attribute) -> GetGlobal:
        return GetGlobal.build(
            result_types=[return_type], properties={"name": SymbolRefAttr(name)}
        )

    # TODO how to verify the types, as the global might be defined in another
    # compilation unit


@irdl_op_definition
class Global(IRDLOperation):
    name = "memref.global"

    sym_name = prop_def(StringAttr)
    sym_visibility = opt_prop_def(StringAttr)
    type = prop_def(Attribute)
    initial_value = prop_def(Attribute)

    traits = frozenset([SymbolOpInterface()])

    def verify_(self) -> None:
        if not isinstance(self.type, MemRefType):
            raise Exception("Global expects a MemRefType")

        if not isinstance(self.initial_value, UnitAttr | DenseIntOrFPElementsAttr):
            raise Exception(
                "Global initial value is expected to be a "
                "dense type or an unit attribute"
            )

    @staticmethod
    def get(
        sym_name: StringAttr,
        sym_type: Attribute,
        initial_value: Attribute | None,
        sym_visibility: StringAttr = StringAttr("private"),
    ) -> Global:
        return Global.build(
            attributes={
                "sym_name": sym_name,
                "type": sym_type,
                "initial_value": initial_value,
                "sym_visibility": sym_visibility,
            }
        )

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        visibility_str = parser.parse_optional_str_literal()
        visibility = (
            StringAttr("private")
            if visibility_str is None
            else StringAttr(visibility_str)
        )
        sym_name = parser.parse_symbol_name()
        parser.parse_punctuation(":")
        sym_type = parser.parse_attribute()
        if parser.parse_optional_punctuation("="):
            initial_value = parser.parse_attribute()
        else:
            initial_value = None
        attributes = parser.parse_optional_attr_dict_with_reserved_attr_names(
            ("sym_name", "type", "initial_value", "sym_visibility")
        )
        res = cls.get(sym_name, sym_type, initial_value, visibility)
        if attributes is not None:
            res.attributes.update(attributes.data)
        return res

    def print(self, printer: Printer):
        printer.print_string(" ")
        if self.sym_visibility is not None:
            assert False
        printer.print(self.value)
        printer.print_string(", ")
        printer.print(self.memref)
        printer.print_string("[")
        printer.print_list(self.indices, printer.print_operand)
        printer.print_string("]")
        printer.print_op_attributes(self.attributes)
        printer.print_string(" : ")
        printer.print_attribute(self.memref.type)


@irdl_op_definition
class Dim(IRDLOperation):
    name = "memref.dim"

    source: Operand = operand_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])
    index: Operand = operand_def(IndexType)

    result: OpResult = result_def(IndexType)

    @staticmethod
    def from_source_and_index(
        source: SSAValue | Operation, index: SSAValue | Operation
    ):
        return Dim.build(operands=[source, index], result_types=[IndexType()])


@irdl_op_definition
class Rank(IRDLOperation):
    name = "memref.rank"

    source: Operand = operand_def(MemRefType[Attribute])

    rank: OpResult = result_def(IndexType)

    @staticmethod
    def from_memref(memref: Operation | SSAValue):
        return Rank.build(operands=[memref], result_types=[IndexType()])


@irdl_op_definition
class ExtractAlignedPointerAsIndexOp(IRDLOperation):
    name = "memref.extract_aligned_pointer_as_index"

    source: Operand = operand_def(MemRefType)

    aligned_pointer: OpResult = result_def(IndexType)

    @staticmethod
    def get(source: SSAValue | Operation):
        return ExtractAlignedPointerAsIndexOp.build(
            operands=[source], result_types=[IndexType()]
        )


class MemrefHasCanonicalizationPatternsTrait(HasCanonicalisationPatternsTrait):
    @classmethod
    def get_canonicalization_patterns(cls) -> tuple[RewritePattern, ...]:
        from xdsl.transforms.canonicalization_patterns.memref import (
            MemrefSubviewOfSubviewFolding,
        )

        return (MemrefSubviewOfSubviewFolding(),)


@irdl_op_definition
class Subview(IRDLOperation):
    name = "memref.subview"

    source: Operand = operand_def(MemRefType)
    offsets: VarOperand = var_operand_def(IndexType)
    sizes: VarOperand = var_operand_def(IndexType)
    strides: VarOperand = var_operand_def(IndexType)
    static_offsets: DenseArrayBase = prop_def(DenseArrayBase)
    static_sizes: DenseArrayBase = prop_def(DenseArrayBase)
    static_strides: DenseArrayBase = prop_def(DenseArrayBase)
    result: OpResult = result_def(MemRefType)

    irdl_options = [AttrSizedOperandSegments(as_property=True)]

    traits = frozenset((MemrefHasCanonicalizationPatternsTrait(),))

    @staticmethod
    def from_static_parameters(
        source: SSAValue | Operation,
        source_type: MemRefType[Attribute],
        offsets: Sequence[int],
        sizes: Sequence[int],
        strides: Sequence[int],
        reduce_rank: bool = False,
    ) -> Subview:
        source = SSAValue.get(source)

        source_shape = source_type.get_shape()
        source_offset = 0
        source_strides = [1]
        for input_size in reversed(source_shape[1:]):
            source_strides.insert(0, source_strides[0] * input_size)
        if isinstance(source_type.layout, StridedLayoutAttr):
            if isinstance(source_type.layout.offset, IntAttr):
                source_offset = source_type.layout.offset.data
            if isa(source_type.layout.strides, ArrayAttr[IntAttr]):
                source_strides = [s.data for s in source_type.layout.strides]

        layout_strides = [a * b for (a, b) in zip(strides, source_strides)]

        layout_offset = (
            sum(stride * offset for stride, offset in zip(source_strides, offsets))
            + source_offset
        )

        if reduce_rank:
            composed_strides = layout_strides
            layout_strides: list[int] = []
            result_sizes: list[int] = []

            for stride, size in zip(composed_strides, sizes):
                if size == 1:
                    continue
                layout_strides.append(stride)
                result_sizes.append(size)

        else:
            result_sizes = list(sizes)

        layout = StridedLayoutAttr(layout_strides, layout_offset)

        return_type = MemRefType(
            source_type.element_type,
            result_sizes,
            layout,
            source_type.memory_space,
        )

        return Subview.build(
            operands=[source, [], [], []],
            result_types=[return_type],
            properties={
                "static_offsets": DenseArrayBase.from_list(i64, offsets),
                "static_sizes": DenseArrayBase.from_list(i64, sizes),
                "static_strides": DenseArrayBase.from_list(i64, strides),
            },
        )


@irdl_op_definition
class Cast(IRDLOperation):
    name = "memref.cast"

    source: Operand = operand_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])
    dest: OpResult = result_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])

    @staticmethod
    def get(
        source: SSAValue | Operation,
        type: MemRefType[Attribute] | UnrankedMemrefType[Attribute],
    ):
        return Cast.build(operands=[source], result_types=[type])


@irdl_op_definition
class MemorySpaceCast(IRDLOperation):
    name = "memref.memory_space_cast"

    source = operand_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])
    dest = result_def(MemRefType[Attribute] | UnrankedMemrefType[Attribute])

    def __init__(
        self,
        source: SSAValue | Operation,
        dest: MemRefType[Attribute] | UnrankedMemrefType[Attribute],
    ):
        super().__init__(operands=[source], result_types=[dest])

    @staticmethod
    def from_type_and_target_space(
        source: SSAValue | Operation,
        type: MemRefType[Attribute],
        dest_memory_space: Attribute,
    ) -> MemorySpaceCast:
        dest = MemRefType(
            type.get_element_type(),
            shape=type.get_shape(),
            layout=type.layout,
            memory_space=dest_memory_space,
        )
        return MemorySpaceCast(source, dest)

    def verify_(self) -> None:
        source = cast(MemRefType[Attribute], self.source.type)
        dest = cast(MemRefType[Attribute], self.dest.type)
        if source.get_shape() != dest.get_shape():
            raise VerifyException(
                "Expected source and destination to have the same shape."
            )
        if source.get_element_type() != dest.get_element_type():
            raise VerifyException(
                "Expected source and destination to have the same element type."
            )


@irdl_op_definition
class DmaStartOp(IRDLOperation):
    name = "memref.dma_start"

    src: Operand = operand_def(MemRefType)
    src_indices: VarOperand = var_operand_def(IndexType)

    dest: Operand = operand_def(MemRefType)
    dest_indices: VarOperand = var_operand_def(IndexType)

    num_elements: Operand = operand_def(IndexType)

    tag: Operand = operand_def(MemRefType[IntegerType])
    tag_indices: VarOperand = var_operand_def(IndexType)

    irdl_options = [AttrSizedOperandSegments()]

    @staticmethod
    def get(
        src: SSAValue | Operation,
        src_indices: Sequence[SSAValue | Operation],
        dest: SSAValue | Operation,
        dest_indices: Sequence[SSAValue | Operation],
        num_elements: SSAValue | Operation,
        tag: SSAValue | Operation,
        tag_indices: Sequence[SSAValue | Operation],
    ):
        return DmaStartOp.build(
            operands=[
                src,
                src_indices,
                dest,
                dest_indices,
                num_elements,
                tag,
                tag_indices,
            ]
        )

    def verify_(self) -> None:
        assert isa(self.src.type, MemRefType[Attribute])
        assert isa(self.dest.type, MemRefType[Attribute])
        assert isa(self.tag.type, MemRefType[IntegerType])

        if len(self.src.type.shape) != len(self.src_indices):
            raise VerifyException(
                f"Expected {len(self.src.type.shape)} source indices (because of shape of src memref)"
            )

        if len(self.dest.type.shape) != len(self.dest_indices):
            raise VerifyException(
                f"Expected {len(self.dest.type.shape)} dest indices (because of shape of dest memref)"
            )

        if len(self.tag.type.shape) != len(self.tag_indices):
            raise VerifyException(
                f"Expected {len(self.tag.type.shape)} tag indices (because of shape of tag memref)"
            )

        if self.tag.type.element_type != i32:
            raise VerifyException("Expected tag to be a memref of i32")

        if self.dest.type.memory_space == self.src.type.memory_space:
            raise VerifyException("Source and dest must have different memory spaces!")


@irdl_op_definition
class DmaWaitOp(IRDLOperation):
    name = "memref.dma_wait"

    tag: Operand = operand_def(MemRefType)
    tag_indices: VarOperand = var_operand_def(IndexType)

    num_elements: Operand = operand_def(IndexType)

    @staticmethod
    def get(
        tag: SSAValue | Operation,
        tag_indices: Sequence[SSAValue | Operation],
        num_elements: SSAValue | Operation,
    ):
        return DmaWaitOp.build(
            operands=[
                tag,
                tag_indices,
                num_elements,
            ]
        )

    def verify_(self) -> None:
        assert isa(self.tag.type, MemRefType[Attribute])

        if len(self.tag.type.shape) != len(self.tag_indices):
            raise VerifyException(
                f"Expected {len(self.tag.type.shape)} tag indices because of shape of tag memref"
            )

        if self.tag.type.element_type != i32:
            raise VerifyException("Expected tag to be a memref of i32")


@irdl_op_definition
class CopyOp(IRDLOperation):
    name = "memref.copy"
    source: Operand = operand_def(MemRefType)
    destination: Operand = operand_def(MemRefType)

    def __init__(self, source: SSAValue | Operation, destination: SSAValue | Operation):
        super().__init__(operands=[source, destination])

    def verify_(self) -> None:
        source = cast(MemRefType[Attribute], self.source.type)
        destination = cast(MemRefType[Attribute], self.destination.type)
        if source.get_shape() != destination.get_shape():
            raise VerifyException(
                "Expected source and destination to have the same shape."
            )
        if source.get_element_type() != destination.get_element_type():
            raise VerifyException(
                "Expected source and destination to have the same element type."
            )


MemRef = Dialect(
    "memref",
    [
        Load,
        Store,
        Alloc,
        Alloca,
        AllocaScopeOp,
        AllocaScopeReturnOp,
        CopyOp,
        Dealloc,
        GetGlobal,
        Global,
        Dim,
        ExtractAlignedPointerAsIndexOp,
        Subview,
        Cast,
        MemorySpaceCast,
        DmaStartOp,
        DmaWaitOp,
    ],
    [MemRefType, UnrankedMemrefType],
)
