; RUN: opt %loadPolly -polly-optree -polly-delicm -polly-simplify -analyze < %s | FileCheck %s -match-full-lines

target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"


%struct._IO_FILE = type { i32, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, %struct._IO_marker*, %struct._IO_FILE*, i32, i32, i64, i16, i8, [1 x i8], i8*, i64, i8*, i8*, i8*, i8*, i64, i32, [20 x i8] }
%struct._IO_marker = type { %struct._IO_marker*, %struct._IO_FILE*, i32 }

@.str = private unnamed_addr constant [1 x i8] zeroinitializer, align 1
@stderr = external local_unnamed_addr global %struct._IO_FILE*, align 8
@.str.1 = private unnamed_addr constant [23 x i8] c"==BEGIN DUMP_ARRAYS==\0A\00", align 1
@.str.2 = private unnamed_addr constant [15 x i8] c"begin dump: %s\00", align 1
@.str.3 = private unnamed_addr constant [2 x i8] c"y\00", align 1
@.str.4 = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.5 = private unnamed_addr constant [8 x i8] c"%0.2lf \00", align 1
@.str.6 = private unnamed_addr constant [17 x i8] c"\0Aend   dump: %s\0A\00", align 1
@.str.7 = private unnamed_addr constant [23 x i8] c"==END   DUMP_ARRAYS==\0A\00", align 1



define internal fastcc void @kernel_atax([2100 x double]* nocapture readonly %A, double* nocapture readonly %x, double* nocapture %y, double* nocapture %tmp) unnamed_addr #2 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  %y15 = bitcast double* %y to i8*
  call void @llvm.memset.p0i8.i64(i8* %y15, i8 0, i64 16800, i32 8, i1 false)
  br label %for.body3

for.body3:                                        ; preds = %for.inc40, %entry.split
  %indvars.iv8 = phi i64 [ 0, %entry.split ], [ %indvars.iv.next9, %for.inc40 ]
  %arrayidx5 = getelementptr inbounds double, double* %tmp, i64 %indvars.iv8
  store double 0.000000e+00, double* %arrayidx5, align 8, !tbaa !6
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body3
  %0 = phi double [ 0.000000e+00, %for.body3 ], [ %add, %for.body8 ]
  %indvars.iv = phi i64 [ 0, %for.body3 ], [ %indvars.iv.next, %for.body8 ]
  %arrayidx14 = getelementptr inbounds [2100 x double], [2100 x double]* %A, i64 %indvars.iv8, i64 %indvars.iv
  %1 = load double, double* %arrayidx14, align 8, !tbaa !6
  %arrayidx16 = getelementptr inbounds double, double* %x, i64 %indvars.iv
  %2 = load double, double* %arrayidx16, align 8, !tbaa !6
  %mul = fmul double %1, %2
  %add = fadd double %0, %mul
  store double %add, double* %arrayidx5, align 8, !tbaa !6
  %indvars.iv.next = add nuw nsw i64 %indvars.iv, 1
  %exitcond = icmp eq i64 %indvars.iv.next, 2
  br i1 %exitcond, label %for.end21, label %for.body8

for.end21:                                        ; preds = %for.body8
  br label %for.body24

for.body24:                                       ; preds = %for.body24.for.body24_crit_edge, %for.end21
  %3 = phi double [ %add, %for.end21 ], [ %.pre, %for.body24.for.body24_crit_edge ]
  %indvars.iv5 = phi i64 [ 0, %for.end21 ], [ %indvars.iv.next6, %for.body24.for.body24_crit_edge ]
  %arrayidx26 = getelementptr inbounds double, double* %y, i64 %indvars.iv5
  %4 = load double, double* %arrayidx26, align 8, !tbaa !6
  %arrayidx30 = getelementptr inbounds [2100 x double], [2100 x double]* %A, i64 %indvars.iv8, i64 %indvars.iv5
  %5 = load double, double* %arrayidx30, align 8, !tbaa !6
  %mul33 = fmul double %5, %3
  %add34 = fadd double %4, %mul33
  store double %add34, double* %arrayidx26, align 8, !tbaa !6
  %indvars.iv.next6 = add nuw nsw i64 %indvars.iv5, 1
  %exitcond7 = icmp eq i64 %indvars.iv.next6, 2
  br i1 %exitcond7, label %for.inc40, label %for.body24.for.body24_crit_edge

for.body24.for.body24_crit_edge:                  ; preds = %for.body24
  %.pre = load double, double* %arrayidx5, align 8, !tbaa !6
  br label %for.body24

for.inc40:                                        ; preds = %for.body24
  %indvars.iv.next9 = add nuw nsw i64 %indvars.iv8, 1
  %exitcond10 = icmp eq i64 %indvars.iv.next9, 2
  br i1 %exitcond10, label %for.end42, label %for.body3

for.end42:                                        ; preds = %for.inc40
  ret void
}

; Function Attrs: nounwind readonly
declare i32 @strcmp(i8* nocapture, i8* nocapture) local_unnamed_addr #3


; Function Attrs: nounwind
declare void @free(i8* nocapture) local_unnamed_addr #4

; Function Attrs: nounwind
declare i32 @fprintf(%struct._IO_FILE* nocapture, i8* nocapture readonly, ...) local_unnamed_addr #4

; Function Attrs: nounwind
declare i64 @fwrite(i8* nocapture, i64, i64, %struct._IO_FILE* nocapture) #5

; Function Attrs: nounwind
declare i32 @fputc(i32, %struct._IO_FILE* nocapture) #5

; Function Attrs: argmemonly nounwind
declare void @llvm.memset.p0i8.i64(i8* nocapture writeonly, i8, i64, i32, i1) #6

attributes #0 = { noinline nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { noinline norecurse nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #3 = { nounwind readonly "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #4 = { nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #5 = { nounwind }
attributes #6 = { argmemonly nounwind }
attributes #7 = { cold }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 6.0.0 (trunk 312565) (llvm/trunk 312564)"}
!2 = !{!3, !3, i64 0}
!3 = !{!"any pointer", !4, i64 0}
!4 = !{!"omnipotent char", !5, i64 0}
!5 = !{!"Simple C/C++ TBAA"}
!6 = !{!7, !7, i64 0}
!7 = !{!"double", !4, i64 0}


; CHECK-LABEL: Printing analysis 'Polly - Simplify' for region: 'for.body3 => for.end42' in function 'kernel_atax':

; CHECK:      After accesses {
; CHECK-NEXT:     Stmt_for_body3
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body3[i0] -> MemRef1__phi[] };
; CHECK-NEXT:            new: { Stmt_for_body3[i0] -> MemRef_tmp[i0] };
; CHECK-NEXT:     Stmt_for_body8
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body8[i0, i1] -> MemRef1__phi[] };
; CHECK-NEXT:            new: { Stmt_for_body8[i0, i1] -> MemRef_tmp[i0] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body8[i0, i1] -> MemRef1__phi[] };
; CHECK-NEXT:            new: { Stmt_for_body8[i0, i1] -> MemRef_tmp[i0] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body8[i0, i1] -> MemRef_A[i0, i1] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body8[i0, i1] -> MemRef_x[i1] };
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body8[i0, i1] -> MemRef_add[] };
; CHECK-NEXT:     Stmt_for_end21
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_end21[i0] -> MemRef_add[] };
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_end21[i0] -> MemRef5__phi[] };
; CHECK-NEXT:     Stmt_for_body24
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body24[i0, i1] -> MemRef5__phi[] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body24[i0, i1] -> MemRef_y[i1] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body24[i0, i1] -> MemRef_A[i0, i1] };
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body24[i0, i1] -> MemRef_y[i1] };
; CHECK-NEXT:     Stmt_for_body24_for_body24_crit_edge
; CHECK-NEXT:             MustWriteAccess :=  [Reduction Type: NONE] [Scalar: 1]
; CHECK-NEXT:                 { Stmt_for_body24_for_body24_crit_edge[i0, i1] -> MemRef5__phi[] };
; CHECK-NEXT:             ReadAccess :=       [Reduction Type: NONE] [Scalar: 0]
; CHECK-NEXT:                 { Stmt_for_body24_for_body24_crit_edge[i0, i1] -> MemRef_tmp[i0] };
; CHECK-NEXT: }

;                                                 tmp[0]
; [ 0] Stmt_for_body3[0]
;                                                 Val_1 (0.0)
; [ 1] Stmt_for_body8[0]
;
; [ 2] Stmt_for_body8[1]
;
; [ 3] Stmt_for_end21[0]
;                                                 Val__add
; [ 4] Stmt_for_body24[0,0]
;
; [ 5] Stmt_for_body24_for_body24_crit_edge[0,0]
;
; [ 6] Stmt_for_body24[0,1]
;
; [ 7] Stmt_for_body3[1]
;
; [ 8] Stmt_for_body8[1,0]
;
; [ 9] Stmt_for_body8[1,0]
;
; [10] Stmt_for_end21[1]
;
; [11] Stmt_for_body24[1,0]
;
; [12] Stmt_for_body24_for_body24_crit_edge[1,0]
;
; [13] Stmt_for_body24[1,1]
