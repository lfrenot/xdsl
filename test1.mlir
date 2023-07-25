A !riscv.reg<> -> B !riscv.freg<> -> C f32 
  | -> riscv.freg<>


builtin.module {
  func.func @main() -> i32  attributes {"llvm.linkage" = #llvm.linkage<"external">}{
    %0 = "riscv.li"() {"immediate" = 1065353216 : si32} : () -> !riscv.reg<>
    %1 = "riscv.fcvt.s.w"(%0) : (!riscv.reg<>) -> !riscv.freg<>
    %2 = "builtin.unrealized_conversion_cast"(%1) : (!riscv.freg<>) -> f32
    %3 = "riscv.li"() {"immediate" = 1073741824 : si32} : () -> !riscv.reg<>
    %4 = "riscv.fcvt.s.w"(%3) : (!riscv.reg<>) -> !riscv.freg<>
    %5 = "builtin.unrealized_conversion_cast"(%4) : (!riscv.freg<>) -> f32
    %6 = "riscv.li"() {"immediate" = 1077936128 : si32} : () -> !riscv.reg<>
    %7 = "riscv.fcvt.s.w"(%6) : (!riscv.reg<>) -> !riscv.freg<>
    %8 = "builtin.unrealized_conversion_cast"(%7) : (!riscv.freg<>) -> f32
    %9 = "riscv.li"() {"immediate" = 0 : si32} : () -> !riscv.reg<>
    %10 = "riscv.fcvt.s.w"(%9) : (!riscv.reg<>) -> !riscv.freg<>
    %11 = "builtin.unrealized_conversion_cast"(%10) : (!riscv.freg<>) -> f32
    %12 = "riscv.get_register"() : () -> !riscv.reg<sp>
    %13 = "riscv.mv"(%12) : (!riscv.reg<sp>) -> !riscv.reg<>
    %14 = "riscv.addi"(%13) {"immediate" = -12 : si12} : (!riscv.reg<>) -> !riscv.reg<sp>
    %15 = "builtin.unrealized_conversion_cast"(%13) : (!riscv.reg<>) -> memref<3xf32>
    %16 = "riscv.get_register"() : () -> !riscv.reg<sp>
    %17 = "riscv.mv"(%16) : (!riscv.reg<sp>) -> !riscv.reg<>
    %18 = "riscv.addi"(%17) {"immediate" = -12 : si12} : (!riscv.reg<>) -> !riscv.reg<sp>
    %19 = "builtin.unrealized_conversion_cast"(%17) : (!riscv.reg<>) -> memref<3xf32>
    %20 = "riscv.li"() {"immediate" = 0 : si32} : () -> !riscv.reg<>
    %21 = "builtin.unrealized_conversion_cast"(%20) : (!riscv.reg<>) -> index
    %22, %23, %24 = "builtin.unrealized_conversion_cast"(%2, %19, %21) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %25 = "riscv.slli"(%24) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %26 = "riscv.add"(%23, %25) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%26, %22) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %27 = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    %28 = "builtin.unrealized_conversion_cast"(%27) : (!riscv.reg<>) -> index
    %29, %30, %31 = "builtin.unrealized_conversion_cast"(%5, %19, %28) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %32 = "riscv.slli"(%31) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %33 = "riscv.add"(%30, %32) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%33, %29) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %34 = "riscv.li"() {"immediate" = 2 : si32} : () -> !riscv.reg<>
    %35 = "builtin.unrealized_conversion_cast"(%34) : (!riscv.reg<>) -> index
    %36, %37, %38 = "builtin.unrealized_conversion_cast"(%8, %19, %35) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %39 = "riscv.slli"(%38) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %40 = "riscv.add"(%37, %39) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%40, %36) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %41 = "riscv.li"() {"immediate" = 0 : si32} : () -> !riscv.reg<>
    %42 = "builtin.unrealized_conversion_cast"(%41) : (!riscv.reg<>) -> index
    %43, %44, %45 = "builtin.unrealized_conversion_cast"(%2, %15, %42) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %46 = "riscv.slli"(%45) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %47 = "riscv.add"(%44, %46) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%47, %43) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %48 = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    %49 = "builtin.unrealized_conversion_cast"(%48) : (!riscv.reg<>) -> index
    %50, %51, %52 = "builtin.unrealized_conversion_cast"(%5, %15, %49) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %53 = "riscv.slli"(%52) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %54 = "riscv.add"(%51, %53) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%54, %50) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %55 = "riscv.li"() {"immediate" = 2 : si32} : () -> !riscv.reg<>
    %56 = "builtin.unrealized_conversion_cast"(%55) : (!riscv.reg<>) -> index
    %57, %58, %59 = "builtin.unrealized_conversion_cast"(%8, %15, %56) : (f32, memref<3xf32>, index) -> (!riscv.freg<>, !riscv.reg<>, !riscv.reg<>)
    %60 = "riscv.slli"(%59) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %61 = "riscv.add"(%58, %60) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    "riscv.fsw"(%61, %57) {"immediate" = 0 : si12, "comment" = "store value to memref of shape (3,)"} : (!riscv.reg<>, !riscv.freg<>) -> ()
    %62 = "riscv.li"() {"immediate" = 0 : si32} : () -> !riscv.reg<>
    %63 = "builtin.unrealized_conversion_cast"(%62) : (!riscv.reg<>) -> index
    %64 = "riscv.li"() {"immediate" = 3 : si32} : () -> !riscv.reg<>
    %65 = "builtin.unrealized_conversion_cast"(%64) : (!riscv.reg<>) -> index
    %66 = "riscv.li"() {"immediate" = 1 : si32} : () -> !riscv.reg<>
    %67 = "builtin.unrealized_conversion_cast"(%66) : (!riscv.reg<>) -> index
    "cf.br"(%63, %11) [^0] : (index, f32) -> ()
  ^0(%68 : index, %69 : f32):
    %70, %71 = "builtin.unrealized_conversion_cast"(%68, %65) : (index, index) -> (!riscv.reg<>, !riscv.reg<>)
    %72 = "riscv.slt"(%70, %71) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    %73 = "riscv.get_register"() : () -> !riscv.reg<zero>
    "riscv.beq"(%72, %73) {"offset" = #riscv.label<"bb3">} : (!riscv.reg<>, !riscv.reg<zero>) -> ()
  ^1:
    "riscv.label"() ({
    }) {"label" = #riscv.label<"bb2">} : () -> ()
    %74, %75 = "builtin.unrealized_conversion_cast"(%19, %68) : (memref<3xf32>, index) -> (!riscv.reg<>, !riscv.reg<>)
    %76 = "riscv.slli"(%75) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %77 = "riscv.add"(%74, %76) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    %78 = "riscv.flw"(%77) {"immediate" = 0 : si12, "comment" = "load value from memref of shape (3,)"} : (!riscv.reg<>) -> !riscv.freg<>
    %79 = "builtin.unrealized_conversion_cast"(%78) : (!riscv.freg<>) -> f32
    %80, %81 = "builtin.unrealized_conversion_cast"(%15, %68) : (memref<3xf32>, index) -> (!riscv.reg<>, !riscv.reg<>)
    %82 = "riscv.slli"(%81) {"immediate" = 2 : ui5} : (!riscv.reg<>) -> !riscv.reg<>
    %83 = "riscv.add"(%80, %82) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    %84 = "riscv.flw"(%83) {"immediate" = 0 : si12, "comment" = "load value from memref of shape (3,)"} : (!riscv.reg<>) -> !riscv.freg<>
    %85 = "builtin.unrealized_conversion_cast"(%84) : (!riscv.freg<>) -> f32
    %86, %87 = "builtin.unrealized_conversion_cast"(%79, %85) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    %88 = "riscv.fmul.s"(%86, %87) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    %89 = "builtin.unrealized_conversion_cast"(%88) : (!riscv.freg<>) -> f32
    %90, %91 = "builtin.unrealized_conversion_cast"(%69, %89) : (f32, f32) -> (!riscv.freg<>, !riscv.freg<>)
    %92 = "riscv.fadd.s"(%90, %91) : (!riscv.freg<>, !riscv.freg<>) -> !riscv.freg<>
    %93 = "builtin.unrealized_conversion_cast"(%92) : (!riscv.freg<>) -> f32
    %94, %95 = "builtin.unrealized_conversion_cast"(%68, %67) : (index, index) -> (!riscv.reg<>, !riscv.reg<>)
    %96 = "riscv.add"(%94, %95) : (!riscv.reg<>, !riscv.reg<>) -> !riscv.reg<>
    %97 = "builtin.unrealized_conversion_cast"(%96) : (!riscv.reg<>) -> index
    "cf.br"(%97, %93) [^0] : (index, f32) -> ()
  ^2:
    "riscv.j"() {"immediate" = #riscv.label<"bb3end">, "rd" = !riscv.reg<zero>} : () -> ()
  ^3:
    "riscv.label"() ({
    }) {"label" = #riscv.label<"bb3">} : () -> ()
    %98 = "builtin.unrealized_conversion_cast"(%69) : (f32) -> !riscv.freg<>
    %99 = "riscv.fcvt.w.s"(%98) : (!riscv.freg<>) -> !riscv.reg<>
    %100 = "builtin.unrealized_conversion_cast"(%99) : (!riscv.reg<>) -> i32
    func.return %100 : i32
  ^4:
    "riscv.label"() ({
    }) {"label" = #riscv.label<"bb3end">} : () -> ()
    "riscv.nop"() : () -> ()
  }
}

