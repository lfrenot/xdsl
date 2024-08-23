// RUN: XDSL_ROUNDTRIP

%t0 = "test.op"() : () -> tensor<i32>

// CHECK: %abs = "stablehlo.abs"(%t0) : (tensor<i32>) -> tensor<i32>
%abs = "stablehlo.abs"(%t0) : (tensor<i32>) -> tensor<i32>

// CHECK: %add = "stablehlo.add"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>
%add = "stablehlo.add"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>

// CHECK: %multiply = "stablehlo.multiply"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>
%multiply = "stablehlo.multiply"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>

// CHECK: %subtract = "stablehlo.subtract"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>
%subtract = "stablehlo.subtract"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>

%transpose_operand = "test.op"() : () -> tensor<2x3x2xi32>
// %operand: [
//            [[1,2], [3,4], [5,6]],
//            [[7,8], [9,10], [11,12]]
//           ]
// CHECK:  %transpose_result = "stablehlo.transpose"(%transpose_operand) {"permutation" = array<i64: 2, 1, 0>} : (tensor<2x3x2xi32>) -> tensor<2x3x2xi32>
%transpose_result = "stablehlo.transpose"(%transpose_operand) {
  permutation = array<i64: 2, 1, 0>
} : (tensor<2x3x2xi32>) -> tensor<2x3x2xi32>
// %result: [
//           [[1,7], [3,9], [5,11]],
//           [[2,8], [4,10], [6,12]]
//          ]

// CHECK: %and = "stablehlo.and"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>
%and = "stablehlo.and"(%t0, %t0) : (tensor<i32>, tensor<i32>) -> tensor<i32>

// CHECK-NEXT:    %dot_general_arg = "test.op"() : () -> tensor<2x2x2xi64>
%dot_general_arg = "test.op"() : () -> tensor<2x2x2xi64>

// CHECK-NEXT:    %dot_general = "stablehlo.dot_general"(%dot_general_arg, %dot_general_arg) {"dot_dimension_numbers" = #stablehlo.dot<
// CHECK-NEXT:      lhs_batching_dimensions = [0],
// CHECK-NEXT:      rhs_batching_dimensions = [0],
// CHECK-NEXT:      lhs_contracting_dimensions = [2],
// CHECK-NEXT:      rhs_contracting_dimensions = [1]
// CHECK-NEXT:    >, "precision_config" = [#stablehlo<precision DEFAULT>, #stablehlo<precision DEFAULT>]} : (tensor<2x2x2xi64>, tensor<2x2x2xi64>) -> tensor<2x2x2xi64>
// %lhs: [
//        [[1, 2],
//         [3, 4]],
//        [[5, 6],
//         [7, 8]]
//       ]
// %rhs: [
//        [[1, 0],
//         [0, 1]],
//        [[1, 0],
//         [0, 1]]
//       ]
%dot_general = "stablehlo.dot_general"(%dot_general_arg, %dot_general_arg) {
  dot_dimension_numbers = #stablehlo.dot<
    lhs_batching_dimensions = [0],
    rhs_batching_dimensions = [0],
    lhs_contracting_dimensions = [2],
    rhs_contracting_dimensions = [1]
  >,
  precision_config = [#stablehlo<precision DEFAULT>, #stablehlo<precision DEFAULT>]
  // algorithm = #stablehlo.dot_algorithm<
  //   lhs_precision_type = tf32,
  //   rhs_precision_type = tf32,
  //   accumulation_type = f32,
  //   lhs_component_count = 1,
  //   rhs_component_count = 1,
  //   num_primitive_operations = 1,
  //   allow_imprecise_accumulation = false
  // >
} : (tensor<2x2x2xi64>, tensor<2x2x2xi64>) -> tensor<2x2x2xi64>
// %result: [
//           [[1, 2],
//            [3, 4]],
//           [[5, 6],
//            [7, 8]]
//          ]

%reduce0, %reduce1 = "test.op"(): () -> (tensor<1x6xi64>, tensor<i64>)

// %input = [[0, 1, 2, 3, 4, 5]]
// %init_value = 0
%reduce_res = "stablehlo.reduce"(%reduce0, %reduce1) ({
  ^bb0(%arg0: tensor<i64>, %arg1: tensor<i64>):
    %0 = "stablehlo.add"(%arg0, %arg1) : (tensor<i64>, tensor<i64>) -> tensor<i64>
    "stablehlo.return"(%0) : (tensor<i64>) -> ()
}) {
  dimensions = array<i64: 1>
} : (tensor<1x6xi64>, tensor<i64>) -> tensor<1xi64>
// %result = [15]

// CHECK: "stablehlo.return"(%t0) : (tensor<i32>) -> ()
"stablehlo.return"(%t0) : (tensor<i32>) -> ()
