// RUN: xdsl-run %s | filecheck %s
// RUN: xdsl-opt %s -p convert-linalg-to-stream | xdsl-run | filecheck %s
// RUN: xdsl-opt %s -p convert-linalg-to-stream,convert-stream-to-snitch-stream,convert-func-to-riscv-func,convert-memref-to-riscv,convert-arith-to-riscv,convert-scf-to-riscv-scf,dce,reconcile-unrealized-casts,snitch-allocate-registers | xdsl-run | filecheck %s

builtin.module {
    "memref.global"() {"sym_name" = "a", "type" = memref<2x3xf64>, "initial_value" = dense<[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]> : tensor<2x3xf64>, "sym_visibility" = "public"} : () -> ()
    "memref.global"() {"sym_name" = "b", "type" = memref<2x3xf64>, "initial_value" = dense<[[0.0, 0.25, 0.5], [0.75, 1.0, 1.25]]> : tensor<2x3xf64>, "sym_visibility" = "public"} : () -> ()
    "memref.global"() {"sym_name" = "c", "type" = memref<2x3xf64>, "initial_value" = dense<[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]> : tensor<2x3xf64>, "sym_visibility" = "public"} : () -> ()

    func.func @main() {
        %A = "memref.get_global"() {"name" = @a} : () -> memref<2x3xf64>
        %B = "memref.get_global"() {"name" = @b} : () -> memref<2x3xf64>
        %C = "memref.get_global"() {"name" = @c} : () -> memref<2x3xf64>
        "linalg.generic"(%A, %B, %C) ({
        ^bb0(%a: f64, %b: f64, %c: f64):
            %sum = arith.addf %a, %b : f64
            linalg.yield %sum : f64
        }) {indexing_maps = [affine_map<(d0, d1) -> (d0, d1)>, affine_map<(d0, d1) -> (d0, d1)>, affine_map<(d0, d1) -> (d0, d1)>], iterator_types = [#linalg.iterator_type<parallel>, #linalg.iterator_type<parallel>, #linalg.iterator_type<parallel>], operandSegmentSizes = array<i32: 2, 1>} : (memref<2x3xf64>, memref<2x3xf64>, memref<2x3xf64>) -> ()

        %c0 = arith.constant 0 : index
        %c1 = arith.constant 1 : index
        %c2 = arith.constant 2 : index
        %c3 = arith.constant 3 : index

        %v0 = memref.load %C[%c0, %c0] : memref<2x3xf64>
        %v1 = memref.load %C[%c0, %c1] : memref<2x3xf64>
        %v2 = memref.load %C[%c0, %c2] : memref<2x3xf64>
        %v3 = memref.load %C[%c1, %c0] : memref<2x3xf64>
        %v4 = memref.load %C[%c1, %c1] : memref<2x3xf64>
        %v5 = memref.load %C[%c1, %c2] : memref<2x3xf64>
        printf.print_format "[[{}, {}, {}], [{}, {}, {}]]", %v0 : f64, %v1 : f64, %v2 : f64, %v3 : f64, %v4 : f64, %v5 : f64

        func.return
    }
}

// CHECK: [[1.0, 2.25, 3.5], [4.75, 6.0, 7.25]]