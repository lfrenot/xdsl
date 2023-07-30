from xdsl.builder import Builder, ImplicitBuilder
from xdsl.dialects import arith, func
from xdsl.dialects.builtin import IntegerAttr, IntegerType, ModuleOp, i32
from xdsl.ir import Operation, OpResult
from xdsl.rewriting.query import (
    AttributeValueConstraint,
    AttributeVariable,
    EqConstraint,
    OperationAttributeConstraint,
    OperationOperandConstraint,
    OperationVariable,
    OpResultOpConstraint,
    OpResultVariable,
    Query,
    SSAValueVariable,
    TypeConstraint,
)
from xdsl.utils.hints import isa


@ModuleOp
@Builder.implicit_region
def module():
    with ImplicitBuilder(func.FuncOp("main", ((), ())).body):
        c0 = arith.Constant.from_int_and_width(0, i32).result
        c1 = arith.Constant.from_int_and_width(1, i32).result
        c2 = arith.Constant.from_int_and_width(2, i32).result
        c3 = arith.Constant.from_int_and_width(3, i32).result

        s0 = arith.Addi(c0, c1).result
        _s1 = arith.Addi(c1, c0).result
        _s2 = arith.Addi(c1, c1).result
        m0 = arith.Muli(s0, c3).result
        m1 = arith.Muli(c2, m0).result
        func.Call("func", ((m1,)), ())
        func.Return()


def test_match_all():
    query_all = Query.root(Operation)

    assert len(query_all.variables) == 1
    assert len(query_all.constraints) == 1

    assert list(module.walk()) == list(ctx["root"] for ctx in query_all.matches(module))


def test_match_constant():
    query_constant = Query.root(arith.Constant)

    for i, ctx in enumerate(query_constant.matches(module)):
        op = ctx["root"]
        assert isinstance(op, arith.Constant)
        assert isa(op.value, IntegerAttr[IntegerType])
        assert i == op.value.value.data


def test_match_constant_1():
    root_var = OperationVariable("root")
    constant_constr = TypeConstraint(root_var, arith.Constant)
    attr_var = AttributeVariable("attr")
    property_constraint = OperationAttributeConstraint(root_var, "value", attr_var)
    attribute_value_constraint = AttributeValueConstraint(
        attr_var, IntegerAttr.from_int_and_width(1, 32)
    )
    query_constant = Query(
        ("root", "attr"),
        [root_var, attr_var],
        [constant_constr, property_constraint, attribute_value_constraint],
    )

    matches = [ctx["root"] for ctx in query_constant.matches(module)]

    assert len(matches) == 1

    op = matches[0]
    assert isinstance(op, arith.Constant)
    assert isa(op.value, IntegerAttr[IntegerType])
    assert op.value.value.data == 1


def test_add_0():
    query_constant = Query(
        (
            "root",
            "rhs",
            "res",
            "zero",
            "attr",
        ),
        [
            root_var := OperationVariable("root"),
            rhs_var := SSAValueVariable("rhs"),
            res_var := OpResultVariable("res"),
            zero_var := OperationVariable("zero"),
            attr_var := AttributeVariable("attr"),
        ],
        [
            TypeConstraint(root_var, arith.Addi),
            OperationOperandConstraint(root_var, "rhs", rhs_var),
            EqConstraint(rhs_var, res_var),
            OpResultOpConstraint(res_var, zero_var),
            TypeConstraint(zero_var, arith.Constant),
            OperationAttributeConstraint(zero_var, "value", attr_var),
            AttributeValueConstraint(attr_var, IntegerAttr.from_int_and_width(0, 32)),
        ],
    )

    matches = [ctx["root"] for ctx in query_constant.matches(module)]

    assert len(matches) == 1

    op = matches[0]
    assert isinstance(op, arith.Addi)
    assert isinstance(op.rhs, OpResult)
    assert isinstance(op.rhs.op, arith.Constant)
    assert isa(op.rhs.op.value, IntegerAttr[IntegerType])
    assert op.rhs.op.value.value.data == 0
