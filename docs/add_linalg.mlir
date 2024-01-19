module @MyAdd {
  util.global private @_params.add_values {noinline} = dense_resource<from_py> : tensor<3xf64>
  func.func @main(%arg0: tensor<3xf64>) -> tensor<3xf64> attributes {torch.args_schema = "[1, {\22type\22: \22builtins.tuple\22, \22context\22: \22null\22, \22children_spec\22: [{\22type\22: \22builtins.list\22, \22context\22: \22null\22, \22children_spec\22: [{\22type\22: null, \22context\22: null, \22children_spec\22: []}]}, {\22type\22: \22builtins.dict\22, \22context\22: \22[]\22, \22children_spec\22: []}]}]", torch.assume_strict_symbolic_shapes, torch.return_schema = "[1, {\22type\22: null, \22context\22: null, \22children_spec\22: []}]"} {
    %0 = call @forward(%arg0) : (tensor<3xf64>) -> tensor<3xf64>
    return %0 : tensor<3xf64>
  }
  func.func private @forward(%arg0: tensor<3xf64>) -> tensor<3xf64> attributes {torch.assume_strict_symbolic_shapes} {
    %_params.add_values = util.global.load @_params.add_values : tensor<3xf64>
    %0 = tensor.empty() : tensor<3xf64>
    %1 = linalg.generic {indexing_maps = [affine_map<(d0) -> (d0)>, affine_map<(d0) -> (d0)>, affine_map<(d0) -> (d0)>], iterator_types = ["parallel"]} ins(%arg0, %_params.add_values : tensor<3xf64>, tensor<3xf64>) outs(%0 : tensor<3xf64>) {
    ^bb0(%in: f64, %in_0: f64, %out: f64):
      %2 = arith.addf %in, %in_0 : f64
      linalg.yield %2 : f64
    } -> tensor<3xf64>
    return %1 : tensor<3xf64>
  }
}