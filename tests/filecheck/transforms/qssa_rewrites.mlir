// RUN: xdsl-opt -p reduce-hadamard,gate-cancellation %s | filecheck %s


%q0, %q1 = qssa.alloc<2>
%q1_1 = qssa.h %q1
%q1_2 = qssa.rz <pi:2> %q1_1
%q0_1, %q1_3 = qssa.cnot %q0, %q1_2
%q1_4 = qssa.h %q1_3
%q1_5 = qssa.rz <pi:2> %q1_4
%q1_6 = qssa.h %q1_5
%q0_2, %q1_7 = qssa.cnot %q0_1, %q1_6


// CHECK:         %{{.*}}, %{{.*}} = qssa.alloc<2>
// CHECK-NEXT:    %{{.*}} = qssa.rz <3pi:2> %{{.*}}