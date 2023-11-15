builtin.module {
    %0 = arith.constant 0 : i32
    %1 = arith.constant 1 : i32
    %x = arith.addi %0, %1 : i32
    %y = arith.addi %1, %0 : i32
}