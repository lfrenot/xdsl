// RUN: xdsl-opt -p lower-arith-to-riscv %s | xdsl-opt --print-op-generic | filecheck %s
"builtin.module"() ({
    %lhsi32 = "arith.constant"() {value = 1 : i32} : () -> i32
    // CHECK: %{{.*}} = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%lhsi32) : (!riscv.reg<>) -> i32
    %rhsi32 = "arith.constant"() {value = 2 : i32} : () -> i32
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 2 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%rhsi32) : (!riscv.reg<>) -> i32
    %lhsindex = "arith.constant"() {value = 1 : index} : () -> index
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%lhsindex) : (!riscv.reg<>) -> index
    %rhsindex = "arith.constant"() {value = 2 : index} : () -> index
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 2 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%rhsindex) : (!riscv.reg<>) -> index
    %lhsf32 = "arith.constant"() {value = 1.000000e+00 : f32} : () -> f32
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 1065353216 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.fcvt.s.w"(%lhsf32) : (!riscv.reg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %rhsf32 = "arith.constant"() {value = 2.000000e+00 : f32} : () -> f32
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 1073741824 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.fcvt.s.w"(%rhsf32) : (!riscv.reg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32

    %addi32 = "arith.addi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.add"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %addindex = "arith.addi"(%lhsindex, %rhsindex) : (index, index) -> index
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (index, index) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.add"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> index

    %subi32 = "arith.subi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sub"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %subindex = "arith.subi"(%lhsindex, %rhsindex) : (index, index) -> index
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (index, index) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sub"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> index

    %muli32 = "arith.muli"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.mul"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %mulindex = "arith.muli"(%lhsindex, %rhsindex) : (index, index) -> index
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (index, index) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.mul"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> index

    %divui32 = "arith.divui"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.divu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %divsi32 = "arith.divsi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.div"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32

    %remui = "arith.remui"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.remu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %remsi = "arith.remsi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.rem"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32

    %andi32 = "arith.andi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.and"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %ori32 = "arith.ori"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.or"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %xori32 = "arith.xori"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.xor"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32

    %shli32 = "arith.shli"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sll"(%{{.*}}, %{{.*}} : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %shrui32 = "arith.shrui"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.srl"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32
    %shrsi32 = "arith.shrsi"(%lhsi32, %rhsi32) : (i32, i32) -> i32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sra"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32

    %cmpi0 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 0 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.xor"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.sltiu"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi1 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 1 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.get_register"() : () -> !riscv.reg<zero>
    // CHECK-NEXT: %{{.*}}= "riscv.xor"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.sltu"(%{{.*}}, %{{.*}}) : (!riscv.reg<zero>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi2 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 2 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.slt"(%{{.*}}, %{{.*}} : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi3 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 3 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.slt"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi4 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 4 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sltu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi5 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 5 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sltu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi6 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 6 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sltu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpi7 = "arith.cmpi"(%lhsi32, %rhsi32) {"predicate" = 7 : i32} : (i32, i32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (i32, i32) -> (!riscv.reg<>, !riscv.reg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.sltu"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1

    %addf32 = "arith.addf"(%lhsf32, %rhsf32) : (f32, f32) -> f32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fadd.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %subf32 = "arith.subf"(%lhsf32, %rhsf32) : (f32, f32) -> f32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fsub.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %mulf32 = "arith.mulf"(%lhsf32, %rhsf32) : (f32, f32) -> f32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fmul.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %divf32 = "arith.divf"(%lhsf32, %rhsf32) : (f32, f32) -> f32
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fdiv.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %negf32 = "arith.negf"(%rhsf32) : (f32) -> f32
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (f32) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "riscv.fsgnjn.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32

    %sitofp = "arith.sitofp"(%lhsi32) : (i32) -> f32
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (i32) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.fcvt.s.w"(%{{.*}}) : (!riscv.reg<>) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.freg<>) -> f32
    %fptosi = "arith.fptosi"(%lhsf32) : (f32) -> i32
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (f32) -> !riscv.freg<>
    // CHECK-NEXT: %{{.*}} = "riscv.fcvt.w.s"(%{{.*}}) : (!riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i32

    %cmpf0 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 0 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 0 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf1 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 1 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf2 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 2 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf3 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 3 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fle.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf4 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 4 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf5 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 5 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fle.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf6 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 6 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.or"(%cmpf6_1, %cmpf6) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf7 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 7 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.and"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf8 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 8 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.or"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf9 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 9 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fle.s"(%{{.*}}, %{{.*}} : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf10 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 10 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf11 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 11 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.fle.s"(%{{.*}}, %{{.*}} : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf12 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 12 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.flt.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf13 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 13 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf14 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 14 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.feq.s"(%{{.*}}, %{{.*}}) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.and"(%{{.*}}, %{{.*}}) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "riscv.xori"(%{{.*}}) {"immediate" = 1 : si12} : (!riscv.reg<>) -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %cmpf15 = "arith.cmpf"(%lhsf32, %rhsf32) {"predicate" = 15 : i32} : (f32, f32) -> i1
    // CHECK-NEXT: %{{.*}}, %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}, %{{.*}}) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    // CHECK-NEXT: %{{.*}} = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (!riscv.reg<>) -> i1
    %index_cast = "arith.index_cast"(%lhsindex) : (index) -> i32
    // CHECK-NEXT: %{{.*}} = "builtin.unrealized_conversion_cast"(%{{.*}}) : (index) -> i32
}) : () -> ()
