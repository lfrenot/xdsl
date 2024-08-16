// RUN: xdsl-opt %s --split-input-file -p loop-hoist-memref | filecheck %s

func.func public @ddot(%arg0: memref<8xf64>, %arg1: memref<8xf64>, %arg2: memref<f64>) -> memref<f64> {
  %c0 = arith.constant 0 : index
  %c8 = arith.constant 8 : index
  %c1 = arith.constant 1 : index
  scf.for %arg3 = %c0 to %c8 step %c1 {
    %a0 = memref.load %arg0[%arg3] : memref<8xf64>
    %a1 = memref.load %arg1[%arg3] : memref<8xf64>
    %a2 = memref.load %arg2[] : memref<f64>
    %a3 = arith.mulf %a0, %a1 : f64
    %a4 = arith.addf %a2, %a3 : f64
    memref.store %a4, %arg2[] : memref<f64>
  }
  return %arg2 : memref<f64>
}

// CHECK:         func.func public @ddot(%arg0 : memref<8xf64>, %arg1 : memref<8xf64>, %arg2 : memref<f64>) -> memref<f64> {
// CHECK-NEXT:      %c0 = arith.constant 0 : index
// CHECK-NEXT:      %c8 = arith.constant 8 : index
// CHECK-NEXT:      %c1 = arith.constant 1 : index
// CHECK-NEXT:      %0 = memref.load %arg2[] : memref<f64>
// CHECK-NEXT:      %1 = scf.for %arg3 = %c0 to %c8 step %c1 iter_args(%2 = %0) -> (f64) {
// CHECK-NEXT:        %3 = memref.load %arg0[%arg3] : memref<8xf64>
// CHECK-NEXT:        %4 = memref.load %arg1[%arg3] : memref<8xf64>
// CHECK-NEXT:        %5 = arith.mulf %3, %4 : f64
// CHECK-NEXT:        %6 = arith.addf %2, %5 : f64
// CHECK-NEXT:        scf.yield %6 : f64
// CHECK-NEXT:      }
// CHECK-NEXT:      memref.store %1, %arg2[] : memref<f64>
// CHECK-NEXT:      func.return %arg2 : memref<f64>
// CHECK-NEXT:    }

// -----

//func.func public @repeat_ddot(%arg0: memref<8xf64>, %arg1: memref<8xf64>, %arg2: memref<f64>) -> memref<f64> {
//  %c0 = arith.constant 0 : index
//  %c8 = arith.constant 8 : index
// %c1 = arith.constant 1 : index
 // scf.for %arg3 = %c0 to %c8 step %c1 {
//    scf.for %arg4 = %c0 to %c8 step %c1 {
//      %0 = memref.load %arg0[%arg3] : memref<8xf64>
//     %1 = memref.load %arg1[%arg3] : memref<8xf64>
//      %2 = memref.load %arg2[] : memref<f64>
//      %3 = arith.mulf %0, %1 : f64
//      %4 = arith.addf %2, %3 : f64
//      memref.store %4, %arg2[] : memref<f64>
//    }
//  }
//  return %arg2 : memref<f64>
//}

// CHECK:         func.func public @repeat_ddot(%arg0 : memref<8xf64>, %arg1 : memref<8xf64>, %arg2 : memref<f64>) -> memref<f64> {
// CHECK-NEXT:      %c0 = arith.constant 0 : index
// CHECK-NEXT:      %c8 = arith.constant 8 : index
// CHECK-NEXT:      %c1 = arith.constant 1 : index
// CHECK-NEXT:      %0 = memref.load %arg2[] : memref<f64>
// CHECK-NEXT:      %1 = scf.for %arg3 = %c0 to %c8 step %c1 iter_args(%2 = %0) -> (f64) {
// CHECK-NEXT:        %3 = scf.for %arg4 = %c0 to %c8 step %c1 iter_args(%4 = %2) -> (f64) {
// CHECK-NEXT:          %5 = memref.load %arg0[%arg3] : memref<8xf64>
// CHECK-NEXT:          %6 = memref.load %arg1[%arg3] : memref<8xf64>
// CHECK-NEXT:          %7 = arith.mulf %5, %6 : f64
// CHECK-NEXT:          %8 = arith.addf %4, %7 : f64
// CHECK-NEXT:          scf.yield %8 : f64
// CHECK-NEXT:        }
// CHECK-NEXT:        scf.yield %3 : f64
// CHECK-NEXT:      }
// CHECK-NEXT:      memref.store %1, %arg2[] : memref<f64>
// CHECK-NEXT:      func.return %arg2 : memref<f64>
// CHECK-NEXT:    }

// -----

//func.func public @matmul(%arg0: memref<8x8xf64> {llvm.noalias}, %arg1: memref<8x8xf64> {llvm.noalias}, %arg2: memref<8x8xf64> {llvm.noalias}) -> memref<8x8xf64> {
//  %c0 = arith.constant 0 : index
//  %c8 = arith.constant 8 : index
//  %c1 = arith.constant 1 : index
//  scf.for %arg3 = %c0 to %c8 step %c1 {
//    scf.for %arg4 = %c0 to %c8 step %c1 {
//      scf.for %arg5 = %c0 to %c8 step %c1 {
//        %0 = memref.load %arg0[%arg3, %arg5] : memref<8x8xf64>
//        %1 = memref.load %arg1[%arg5, %arg4] : memref<8x8xf64>
//        %2 = memref.load %arg2[%arg3, %arg4] : memref<8x8xf64>
//        %3 = arith.mulf %0, %1 : f64
//        %4 = arith.addf %2, %3 : f64
//        memref.store %4, %arg2[%arg3, %arg4] : memref<8x8xf64>
//      }
//    }
//  }
//  return %arg2 : memref<8x8xf64>
//}

// CHECK:         func.func public @matmul(%arg0 : memref<8x8xf64> {"llvm.noalias"}, %arg1 : memref<8x8xf64> {"llvm.noalias"}, %arg2 : memref<8x8xf64> {"llvm.noalias"}) -> memref<8x8xf64> {
// CHECK-NEXT:      %c0 = arith.constant 0 : index
// CHECK-NEXT:      %c8 = arith.constant 8 : index
// CHECK-NEXT:      %c1 = arith.constant 1 : index
// CHECK-NEXT:      scf.for %arg3 = %c0 to %c8 step %c1 {
// CHECK-NEXT:        scf.for %arg4 = %c0 to %c8 step %c1 {
// CHECK-NEXT:          %0 = memref.load %arg2[%arg3, %arg4] : memref<8x8xf64>
// CHECK-NEXT:          %1 = scf.for %arg5 = %c0 to %c8 step %c1 iter_args(%2 = %0) -> (f64) {
// CHECK-NEXT:            %3 = memref.load %arg0[%arg3, %arg5] : memref<8x8xf64>
// CHECK-NEXT:            %4 = memref.load %arg1[%arg5, %arg4] : memref<8x8xf64>
// CHECK-NEXT:            %5 = arith.mulf %3, %4 : f64
// CHECK-NEXT:            %6 = arith.addf %2, %5 : f64
// CHECK-NEXT:            scf.yield %6 : f64
// CHECK-NEXT:          }
// CHECK-NEXT:          memref.store %1, %arg2[%arg3, %arg4] : memref<8x8xf64>
// CHECK-NEXT:        }
// CHECK-NEXT:      }
// CHECK-NEXT:      func.return %arg2 : memref<8x8xf64>
// CHECK-NEXT:    }

func.func @invariant_loop_dialect() {
  %ci0 = arith.constant 0 : index
  %ci10 = arith.constant 10 : index
  %ci1 = arith.constant 1 : index
  %m = memref.alloc() : memref<10xf32>
  %cf7 = arith.constant 7.0 : f32
  %cf8 = arith.constant 8.0 : f32
  scf.for %arg0 = %ci0 to %ci10 step %ci1 {
    scf.for %arg1 = %ci0 to %ci10 step %ci1 {
      %v0 = arith.addf %cf7, %cf8 : f32
    }
  }

  // CHECK: memref.alloc() : memref<10xf32>
  // CHECK-NEXT: arith.constant 7.000000e+00 : f32
  // CHECK-NEXT: arith.constant 8.000000e+00 : f32
  // CHECK-NEXT: arith.addf

  return
}

func.func @speculate_tensor_dim_unknown_rank_known_dim(
// CHECK-LABEL: @speculate_tensor_dim_unknown_rank_known_dim
    %t: tensor<*xf32>, %dim_idx: index, %lb: index, %ub: index, %step: index) {
  %c0 = arith.constant 0 : index
  // CHECK: scf.for
  // CHECK-NEXT: tensor.dim
  scf.for %i = %lb to %ub step %step {
    %val = tensor.dim %t, %c0 : tensor<*xf32>
  }

  return
}