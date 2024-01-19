module @MyAdd {
  util.global private @_params.add_values {noinline} = dense_resource<from_py> : tensor<3xf64>
  func.func @main(%arg0: tensor<3xf64>) -> tensor<3xf64> attributes {torch.args_schema = "[1, {\22type\22: \22builtins.tuple\22, \22context\22: \22null\22, \22children_spec\22: [{\22type\22: \22builtins.list\22, \22context\22: \22null\22, \22children_spec\22: [{\22type\22: null, \22context\22: null, \22children_spec\22: []}]}, {\22type\22: \22builtins.dict\22, \22context\22: \22[]\22, \22children_spec\22: []}]}]", torch.return_schema = "[1, {\22type\22: null, \22context\22: null, \22children_spec\22: []}]"} {
    %0 = torch_c.from_builtin_tensor %arg0 : tensor<3xf64> -> !torch.vtensor<[3],f64>
    %1 = call @forward(%0) : (!torch.vtensor<[3],f64>) -> !torch.vtensor<[3],f64>
    %2 = torch_c.to_builtin_tensor %1 : !torch.vtensor<[3],f64> -> tensor<3xf64>
    return %2 : tensor<3xf64>
  }
  func.func private @forward(%arg0: !torch.vtensor<[3],f64>) -> !torch.vtensor<[3],f64> {
    %_params.add_values = util.global.load @_params.add_values : tensor<3xf64>
    %0 = torch_c.from_builtin_tensor %_params.add_values : tensor<3xf64> -> !torch.vtensor<[3],f64>
    %int1 = torch.constant.int 1
    %1 = torch.aten.add.Tensor %arg0, %0, %int1 : !torch.vtensor<[3],f64>, !torch.vtensor<[3],f64>, !torch.int -> !torch.vtensor<[3],f64>
    return %1 : !torch.vtensor<[3],f64>
  }
}

{-#
  dialect_resources: {
    builtin: {
      from_py: "0x08000000000000000000F03F00000000000000400000000000000840"
    }
  }
#-}
