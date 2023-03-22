from __future__ import annotations
from typing import TYPE_CHECKING, Annotated

from xdsl.dialects.builtin import (StringAttr, ArrayAttr, DenseArrayBase, i32,
                                   IntAttr, NoneAttr, IntegerType, IntegerAttr,
                                    i64,
                                   AnyIntegerAttr, IndexType, UnitAttr)
from xdsl.ir import (MLIRType, ParametrizedAttribute, Attribute, Dialect,
                     OpResult, Operation, SSAValue)


from xdsl.irdl import (OpAttr, Operand, ParameterDef, AnyAttr, OptOpAttr, VarOperand,
                       irdl_attr_definition, irdl_op_definition)


if TYPE_CHECKING:
    from xdsl.parser import BaseParser
    from xdsl.printer import Printer


@irdl_attr_definition
class LLVMStructType(ParametrizedAttribute, MLIRType):
    name = "llvm.struct"

    # An empty string refers to a struct without a name.
    struct_name: ParameterDef[StringAttr]
    types: ParameterDef[ArrayAttr[Attribute]]

    # TODO: Add this parameter once xDSL supports the necessary capabilities.
    #  bitmask = ParameterDef(StringAttr)

    @staticmethod
    def from_type_list(types: list[Attribute]) -> LLVMStructType:
        return LLVMStructType([StringAttr(""), ArrayAttr(types)])

    def print_parameters(self, printer: Printer) -> None:
        assert self.struct_name.data == ""
        printer.print("<(")
        printer.print_list(self.types.data, printer.print_attribute)
        printer.print(")>")

    @staticmethod
    def parse_parameters(parser: BaseParser) -> list[Attribute]:
        parser.parse_characters("<(", "LLVM Struct must start with `<(`")
        params = parser.parse_list_of(
            parser.try_parse_type,
            "Malformed LLVM struct, expected attribute definition here!")
        parser.parse_characters(
            ")>", "Unexpected input, expected end of LLVM struct!")
        return [StringAttr(""), ArrayAttr(params)]


@irdl_attr_definition
class LLVMPointerType(ParametrizedAttribute, MLIRType):
    name = "llvm.ptr"

    type: ParameterDef[Attribute | NoneAttr]
    addr_space: ParameterDef[IntAttr | NoneAttr]

    def print_parameters(self, printer: Printer) -> None:
        if isinstance(self.type, NoneAttr):
            return

        printer.print_string("<")
        printer.print_attribute(self.type)
        if not isinstance(self.addr_space, NoneAttr):
            printer.print_string(", ")
            printer.print_attribute(self.addr_space)

        printer.print_string(">")

    @staticmethod
    def parse_parameters(parser: BaseParser) -> list[Attribute]:
        if not parser.tokenizer.starts_with('<'):
            return [NoneAttr(), NoneAttr()]
        parser.parse_characters('<', "llvm.ptr parameters expected")
        type = parser.try_parse_type()
        if type is None:
            parser.raise_error(
                "Expected first parameter of llvm.ptr to be a type!")
        if not parser.tokenizer.starts_with(','):
            parser.parse_characters('>',
                                    "End of llvm.ptr parameters expected!")
            return [type, NoneAttr()]
        parser.parse_characters(',', "llvm.ptr args must be separated by `,`")
        addr_space = parser.parse_int_literal()
        parser.parse_characters('>', "End of llvm.ptr parameters expected!")
        return [type, IntegerAttr.from_params(addr_space, IndexType())]

    @staticmethod
    def opaque():
        return LLVMPointerType([NoneAttr(), NoneAttr()])

    @staticmethod
    def typed(type: Attribute):
        return LLVMPointerType([type, NoneAttr()])

    def is_typed(self) -> bool:
        return not isinstance(self.type, NoneAttr)


@irdl_op_definition
class GetElementPtrOp(Operation):
    name = "llvm.getelementptr"

    ptr: Annotated[Operand, LLVMPointerType]
    ssa_indices: Annotated[VarOperand, IntegerType]

    elem_type: OpAttr[Attribute]

    rawConstantIndices: OpAttr[DenseArrayBase]

    inbounds: OptOpAttr[UnitAttr]

    result: OpResult

    @staticmethod
    def get(
        ptr: SSAValue | Operation,
        indices: list[int] | None = None,
        ssa_indices: list[SSAValue | Operation] | None = None,
        result_type: Attribute | None = None, 
        inbounds: bool = False,
    ):  
        # construct default mutable argument here:
        if indices is None:
            indices = []

        indices_attr = DenseArrayBase.create_dense_int_or_index(
            i32, indices
        )

        # construct default mutable argument here:
        if ssa_indices is None:
            ssa_indices = []

        # convert a potential Operation into an SSAValue
        ptr = SSAValue.get(ptr)

        # if no result type was give, infer from pointer type
        if result_type is None:
            # ptr is an SSAValue
            # ptr.typ is the type of the SSAValue (so the LLVMPointerType)
            assert isinstance(ptr.typ, LLVMPointerType)
            # ptr.typ.type is the wrapped type of the pointer
            if isinstance(ptr.typ.type, NoneAttr):
                raise ValueError("...")
            # use that as the result type
            result_type = LLVMPointerType.typed(ptr.typ.type)
        
        attrs: dict[str, Attribute] = {
            'rawConstantIndices': indices_attr,
            'elem_type': result_type
        }

        assert isinstance(ptr.typ, LLVMPointerType)
        if ptr.typ.is_typed():
            attrs.pop('elem_type')

        if not isinstance(result_type, LLVMPointerType):
            result_type = LLVMPointerType.typed(result_type)

        if inbounds:
            attrs['inbounds'] = UnitAttr()

        return GetElementPtrOp.build(
            operands=[ptr, ssa_indices],
            result_types=[result_type],
            attributes=attrs
        )


@irdl_op_definition
class AllocaOp(Operation):
    name = "llvm.alloca"

    size: Annotated[Operand, IntegerType]

    alignment: OpAttr[AnyIntegerAttr]

    res: OpResult

    @staticmethod
    def get(size: SSAValue | Operation,
            elem_type: Attribute,
            alignment: int = 32,
            as_untyped_ptr: bool = False):
        attrs: dict[str, Attribute] = {
            'alignment': IntegerAttr.from_int_and_width(alignment, 64)
        }
        if as_untyped_ptr:
            ptr_type = LLVMPointerType.opaque()
            attrs['elem_type'] = elem_type
        else:
            ptr_type = LLVMPointerType.typed(elem_type)

        return AllocaOp.build(operands=[size],
                              attributes=attrs,
                              result_types=[ptr_type])


@irdl_op_definition
class IntToPtrOp(Operation):
    name = "llvm.inttoptr"

    input: Annotated[Operand, IntegerType]

    output: Annotated[OpResult, LLVMPointerType]

    @staticmethod
    def get(input: SSAValue | Operation, ptr_type: Attribute | None = None):
        if ptr_type is None:
            ptr_type = LLVMPointerType.opaque()
        else:
            ptr_type = LLVMPointerType.typed(ptr_type)
        return IntToPtrOp.build(operands=[input], result_types=[ptr_type])


@irdl_op_definition
class PtrToIntOp(Operation):
    name = "llvm.ptrtoint"

    input: Annotated[Operand, LLVMPointerType]

    output: Annotated[OpResult, IntegerType]

    @staticmethod
    def get(arg: SSAValue | Operation, int_type: Attribute = i64):
        return PtrToIntOp.build(operands=[arg], result_types=[int_type])


@irdl_op_definition
class LoadOp(Operation):
    name = "llvm.load"

    ptr: Annotated[Operand, LLVMPointerType]

    dereferenced_value: OpResult

    @staticmethod
    def get(ptr: SSAValue | Operation, result_type: Attribute | None = None):
        if result_type is None:
            ptr = SSAValue.get(ptr)
            assert isinstance(ptr.typ, LLVMPointerType)

            if isinstance(ptr.typ.type, NoneAttr):
                raise ValueError(
                    "llvm.load requires either a result type or a typed pointer!"
                )
            result_type = ptr.typ.type

        return LoadOp.build(operands=[ptr], result_types=[result_type])


@irdl_op_definition
class StoreOp(Operation):
    name = "llvm.store"

    value: Operand
    ptr: Annotated[Operand, LLVMPointerType]

    alignment: OptOpAttr[IntegerAttr[IntegerType]]
    ordering: OptOpAttr[IntegerAttr[IntegerType]]
    volatile_: OptOpAttr[UnitAttr]
    nontemporal: OptOpAttr[UnitAttr]

    @staticmethod
    def get(value: SSAValue | Operation,
            ptr: SSAValue | Operation,
            alignment: int | None = None,
            ordering: int = 0,
            volatile: bool = False,
            nontemporal: bool = False):
        attrs: dict[str, Attribute] = {
            'ordering': IntegerAttr(ordering, i64),
        }

        if alignment is not None:
            attrs['alignment'] = IntegerAttr[IntegerType](alignment, i64)
        if volatile:
            attrs['volatile_'] = UnitAttr()
        if nontemporal:
            attrs['nontemporal'] = UnitAttr()

        return StoreOp.build(
            operands=[value, ptr],
            attributes=attrs,
            result_types=[],
        )


@irdl_op_definition
class NullOp(Operation):
    name = "llvm.mlir.null"

    nullptr: Annotated[OpResult, LLVMPointerType]

    @classmethod
    def get(cls, ptr_type: LLVMPointerType | None = None):
        if ptr_type is None:
            ptr_type = LLVMPointerType.opaque()
        assert isinstance(ptr_type, LLVMPointerType)

        return cls.build(result_types=[ptr_type])


@irdl_op_definition
class LLVMExtractValue(Operation):
    name = "llvm.extractvalue"

    position: OpAttr[DenseArrayBase]
    container: Annotated[Operand, AnyAttr()]

    res: Annotated[OpResult, AnyAttr()]


@irdl_op_definition
class LLVMInsertValue(Operation):
    name = "llvm.insertvalue"

    position: OpAttr[DenseArrayBase]
    container: Annotated[Operand, AnyAttr()]
    value: Annotated[Operand, AnyAttr()]

    res: Annotated[OpResult, AnyAttr()]


@irdl_op_definition
class LLVMMLIRUndef(Operation):
    name = "llvm.mlir.undef"

    res: Annotated[OpResult, AnyAttr()]


LLVM = Dialect([
    LLVMExtractValue,
    LLVMInsertValue,
    LLVMMLIRUndef,
    AllocaOp,
    GetElementPtrOp,
    IntToPtrOp,
    NullOp,
    LoadOp,
    StoreOp,
], [LLVMStructType, LLVMPointerType])
