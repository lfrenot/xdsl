from dataclasses import dataclass, field

import pytest

from xdsl.dialects import builtin
from xdsl.ir import MLContext

from xdsl.passes import ModulePass
from xdsl.utils.parse_pipeline import PipelinePassSpec


@dataclass
class CustomPass(ModulePass):
    name = "custom-pass"

    number: int | float

    int_list: list[int]

    non_init_thing: int = field(init=False)

    str_thing: str

    optional: str | None

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        pass


@dataclass
class EmptyPass(ModulePass):
    name = "empty"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        pass


@dataclass
class SimplePass(ModulePass):
    name = "simple"

    a: int | float
    b: int | None

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        pass


def test_pass_instantiation():
    p = CustomPass.from_pass_spec(
        PipelinePassSpec(
            name="custom-pass",
            args={
                "number": [2],
                "int_list": [1, 2, 3],
                "str_thing": ["hello world"],
                # "optional" was left out here, as it is optional
            },
        )
    )

    assert p.number == 2
    assert p.int_list == [1, 2, 3]
    assert p.str_thing == "hello world"
    assert p.optional is None

    # this should just work
    EmptyPass.from_pass_spec(PipelinePassSpec("empty", dict()))


@pytest.mark.parametrize(
    "spec, error_msg",
    (
        (PipelinePassSpec("wrong", {"a": [1]}), "Wrong pass name"),
        (PipelinePassSpec("simple", {}), 'requires argument "a"'),
        (
            PipelinePassSpec("simple", {"a": [1], "no": []}),
            'Unrecognised pass argument "no"',
        ),
        (PipelinePassSpec("simple", {"a": []}), "Argument must contain a value"),
        (PipelinePassSpec("simple", {"a": ["test"]}), "Incompatible types"),
    ),
)
def test_pass_instantiation_error(spec: PipelinePassSpec, error_msg: str):
    """
    Test all possible failure modes in pass instantiation
    """
    with pytest.raises(Exception, match=error_msg):
        SimplePass.from_pass_spec(spec)
