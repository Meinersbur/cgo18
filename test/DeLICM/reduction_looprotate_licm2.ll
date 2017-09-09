; RUN: opt %loadPolly -polly-flatten-schedule -polly-delicm-overapproximate-writes=true -polly-delicm-compute-known=true -polly-delicm -analyze < %s | FileCheck %s
;
;    void func(double *A) {
;      for (int j = 0; j < 2; j += 1) { /* outer */
;        double phi = A[j];
;        for (int i = 0; i < 4; i += 1) /* reduction */
;          phi += 4.2;
;        A[j] = phi;
;      }
;    }
;
define void @func(double* noalias nonnull %A) {
entry:
  br label %outer.preheader

outer.preheader:
  br label %outer.for

outer.for:
  %j = phi i32 [0, %outer.preheader], [%j.inc, %outer.inc]
  %j.cmp = icmp slt i32 %j, 2
  br i1 %j.cmp, label %reduction.preheader, label %outer.exit


    reduction.preheader:
      %A_idx = getelementptr inbounds double, double* %A, i32 %j
      %init = load double, double* %A_idx
      br label %reduction.for

    reduction.for:
      %i = phi i32 [0, %reduction.preheader], [%i.inc, %reduction.inc]
      %phi = phi double [%init, %reduction.preheader], [%add, %reduction.inc]
      br label %body



        body:
          %add = fadd double %phi, 4.2
          br label %reduction.inc



    reduction.inc:
      %i.inc = add nuw nsw i32 %i, 1
      %i.cmp = icmp slt i32 %i.inc, 4
      br i1 %i.cmp, label %reduction.for, label %reduction.exit

    reduction.exit:
      store double %phi, double* %A_idx
      br label %outer.inc



outer.inc:
  %j.inc = add nuw nsw i32 %j, 1
  br label %outer.for

outer.exit:
  br label %return

return:
  ret void
}

