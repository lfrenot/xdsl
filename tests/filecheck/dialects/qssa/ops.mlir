// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP

%q0 = "test.op"() : () -> !qssa.qubit

// CHECK: %q0 = "test.op"() : () -> !qssa.qubit

%0 = qssa.h %q0

// CHECK-NEXT: %0 = qssa.h %q0

%q1 = "test.op"() : () -> !qssa.qubit

// CHECK-NEXT: %q1 = "test.op"() : () -> !qssa.qubit

%q2:2 = qssa.cz %q1 %0

// CHECK-NEXT: %q2, %q2_1 = qssa.cz %q1 %0

%q3, %q4 = qssa.cnot %q2#0 %q2#1

// CHECK-NEXT: %q3, %q4 = qssa.cnot %q2 %q2_1

%1 = qssa.measure %q3

// CHECK-NEXT: %1 = qssa.measure %q3

// CHECK-GENERIC: %q0 = "test.op"() : () -> !qssa.qubit
// CHECK-GENERIC-NEXT: %0 = "qssa.h"(%q0) : (!qssa.qubit) -> !qssa.qubit
// CHECK-GENERIC-NEXT: %q1 = "test.op"() : () -> !qssa.qubit
// CHECK-GENERIC-NEXT: %q2, %q2_1 = "qssa.cz"(%q1, %0) : (!qssa.qubit, !qssa.qubit) -> (!qssa.qubit, !qssa.qubit)
// CHECK-GENERIC-NEXT: %q3, %q4 = "qssa.cnot"(%q2, %q2_1) : (!qssa.qubit, !qssa.qubit) -> (!qssa.qubit, !qssa.qubit)
// CHECK-GENERIC-NEXT: %1 = "qssa.measure"(%q3) : (!qssa.qubit) -> i1
