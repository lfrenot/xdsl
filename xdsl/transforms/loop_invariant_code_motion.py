from collections.abc import Iterator
from typing import Any, Sequence, cast
import re
import queue
from typing import Any, Callable, cast, Dict, List, Optional, Tuple, Union
from xdsl.context import MLContext
from xdsl.dialects import arith, builtin, scf, memref
from xdsl.ir import SSAValue, Operation, Block, Region
from xdsl.traits import IsTerminator, NoTerminator, OpTrait, OpTraitInvT
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

#  This pass hoists operation that are invariant to the loops.
#
#  Similar to MLIR's loop invariant code motion:
#  https://mlir.llvm.org/doxygen/LoopInvariantCodeMotion_8cpp_source.html
#
#  An operation is loop-invariant if it depends only of values defined outside of the loop. LICM moves these operations out of the loop body so that they are not computed more than once.
#
#    for i in range(x, N, M):                for i in range(x, N, M): 
#      for j in range(0, M, K):    ---->        c[i]= A[1] + b[1]
#        c[i]=A[1]+b[1]

#  Checks whether the given op can be hoisted by checking that
#  - the op and none of its contained operations depend on values inside of the
#    loop (by means of calling definedOutside).
#  - the op has no side-effects.
def canBeHoisted(op: Operation, condition: Callable[[SSAValue], bool]) -> bool | None:
    #   Do not move terminators.
    if op.has_trait(IsTerminator):
        return False

    # Walk the nested operations and check that all used values are either
    # defined outside of the loop or in a nested region, but not at the level of
    # the loop body.

    return any(
        op.is_ancestor(operand.owner) or condition(operand)
        for child in op.walk()
        for operand in child.operands
    )


def isDefinedOutsideOfRegoin(value: SSAValue, region: Region) -> bool | None:
    return not region.is_ancestor(value.owner)

def can_be_hoisted_with_value_check(op: Operation, defined_outside: Callable[[SSAValue], bool])-> bool | None:
    return canBeHoisted(op, defined_outside(op))

def moveLoopInvariantCode(
    regions : Sequence[Region],
    isDefinedOutsideRegion: Callable[[Region], bool], #function_ref<bool(Value, Region *)> isDefinedOutsideRegion
    shouldMoveOutofRegion: Callable[[Operation], bool], #function_ref<bool(Operation *, Region *)> shouldMoveOutOfRegion
    moveOutofRegion: Callable[[Operation], Region]) -> int | None: #function_ref<void(Operation *, Region *)> moveOutOfRegion
    
    numMoved = 0
    worklist : list[Operation] = []

    for region in regions: #iter thorugh the regions
        print("Original loop: ", region.parent_node)
        for op in region.block.ops:
            print("Operation: ", op)
            worklist.append(op)
        
            definedOutside = isDefinedOutsideRegion(region)

            while not worklist:
                oper = worklist.pop()
                #Skip ops that have already been moved. Check if the op can be hoisted.
                if oper.parent_region() != region:
                    continue
                print("Check op: ", oper)

                if not(shouldMoveOutofRegion(oper, region) or not(canBeHoisted(oper, definedOutside))):
                    continue
                print("Moving loop-invariant op: ", oper)
                moveOutofRegion(oper, region)
                numMoved = numMoved + 1

                for user in oper.results[0].uses:
                    if user.operation.parent_region is region:
                        worklist.append(user.operation)

    return numMoved

class LoopsInvariantCodeMotion(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: scf.For, rewriter: PatternRewriter) -> None:
        for region in op.regions:
            for block in region.blocks:
                for lp in block.walk():
                    for oper in lp.operands:
                        print("lp: ",lp)
                        print("region: ", region)
                        print("operands: ", oper._name)
                        print("isDefinedOutside: ", isDefinedOutsideOfRegoin(oper, region))

        #####################dumb implementation###################
        #works on only inner most scf.for loop for now but something that works
        #dependent_stack holds all the operations that dependent and only this instructions should be in the loop
        #hoistable instructions are temp_stack - dependent_stack
        temp_stack : list[Operation] = []
        dependent_stack : list[Operation] = []
        hoist_instruction : list[Operation] = []

        #walking to the inner most loop
        if any(isinstance(ha, scf.For) for ha in op.body.walk()):
            return
        print(op.parent_block())
        for i in op.parent_block().ops:
            if isinstance(i, scf.For):
                loop_variable_match = re.search(r'scf\.for\s+%(\w+)\s*=', str(i))
                loop_variable = loop_variable_match.group(1) if loop_variable_match else None
                print("loop variable: ", loop_variable)
            
        for iter in op.body.block.walk():
            if str(iter).__contains__(loop_variable):
                temp_stack.append(iter)
                dependent_stack.append(iter)

        while temp_stack:
            item = temp_stack.pop()
            if any(l is item for l in op.body.walk()):
                print("item: ", item)
                if isinstance(item, scf.Yield) or isinstance(item, scf.For) or isinstance(item, memref.Store):
                    continue
                for user in item.results[0].uses:
                    print("Dependent Instructions are used: ", user.operation)
                    temp_stack.append(user.operation)
                    if not dependent_stack.__contains__(user.operation):
                        dependent_stack.append(user.operation)

                for ins in dependent_stack:
                    print(ins)

class ScfForLoopInavarintCodeMotionPass(ModulePass):
    """
    Folds perfect loop nests if they can be represented with a single loop.
    Currently does this by matching the inner loop range with the outer loop step.
    If the inner iteration space fits perfectly in the outer iteration step, then merge.
    Other conditions:
     - the only use of the induction arguments must be an add operation, this op is fused
       into a single induction argument,
     - the lower bound of the inner loop must be 0,
     - the loops must have no iteration arguments.
    """

    name = "licm"

    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        PatternRewriteWalker(LoopsInvariantCodeMotion()).rewrite_module(op)
