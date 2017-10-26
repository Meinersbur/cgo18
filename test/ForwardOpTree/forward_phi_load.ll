; RUN: opt %loadPolly -polly-optree-normalize-phi=true -polly-optree -analyze < %s | FileCheck %s -match-full-lines
;
; Rematerialize a load.
;
; for (int j = 0; j < n; j += 1) {
; bodyA:
;   double val = B[j];
;
; bodyB:
;   double phi = val;
;
; bodyC:
;   A[j] = phi;
; }
;
define void @func(i32 %n, double* noalias nonnull %A, double* noalias nonnull %B) {
entry:
  br label %for

for:
  %j = phi i32 [0, %entry], [%j.inc, %inc]
  %j.cmp = icmp slt i32 %j, %n
  br i1 %j.cmp, label %bodyA, label %exit

    bodyA:
      %B_idx = getelementptr inbounds double, double* %B, i32 %j
      %val = load double, double* %B_idx
      br label %bodyB

    bodyB:
      %phi = phi double [%val, %bodyA]
      br label %bodyC
      
    bodyC:
      %A_idx = getelementptr inbounds double, double* %A, i32 %j
      store double %phi, double* %A_idx
      br label %inc

inc:
  %j.inc = add nuw nsw i32 %j, 1
  br label %for

exit:
  br label %return

return:
  ret void
}

