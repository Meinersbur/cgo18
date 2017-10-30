; RUN: opt %loadPolly -polly-optree-normalize-phi -polly-optree-max-ops=0 -debug-only=polly-optree,polly-ast -domtree -loops -scalar-evolution -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -basicaa -aa -postdomtree -domfrontier -regions -polly-detect -polly-scops -polly-simplify -polly-optree -polly-delicm -polly-simplify -polly-prune-unprofitable -polly-dependences -polly-opt-isl -polly-ast -polly-codegen -barrier -polly-cleanup -domtree -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -loop-rotate -loop-accesses -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -loop-distribute -branch-prob -block-freq -scalar-evolution -basicaa -aa -loop-accesses -demanded-bits -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -loop-vectorize -loop-simplify -scalar-evolution -aa -loop-accesses -loop-load-elim -basicaa -aa -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -scalar-evolution -demanded-bits -opt-remark-emitter -slp-vectorizer -simplifycfg -domtree -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -loop-simplify -lcssa-verification -lcssa -scalar-evolution -loop-unroll -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -loop-simplify -lcssa-verification -lcssa -scalar-evolution -licm -alignment-from-assumptions -strip-dead-prototypes -globaldce -constmerge -domtree -loops -branch-prob -block-freq -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -branch-prob -block-freq -loop-sink -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instsimplify -div-rem-pairs -simplifycfg -barrier -domtree -barrier -domtree -barrier -scoped-noalias -tbaa -assumption-cache-tracker -targetlibinfo -tti -domtree -basicaa -aa -simplifycfg -domtree -sroa -early-cse -mem2reg -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -simplifycfg -domtree -sroa -basicaa -aa -memoryssa -early-cse-memssa -domtree -basicaa -aa -lazy-value-info -jump-threading -lazy-value-info -correlated-propagation -simplifycfg -domtree -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -libcalls-shrinkwrap -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -tailcallelim -simplifycfg -reassociate -domtree -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -loop-rotate -memdep -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -gvn -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -licm -loop-unswitch -simplifycfg -domtree -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -loop-simplify -lcssa-verification -lcssa -scalar-evolution -indvars -loop-idiom -loop-deletion -simplifycfg -domtree -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -loop-unroll -mldst-motion -aa -memdep -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -gvn -basicaa -aa -memdep -memcpyopt -sccp -domtree -demanded-bits -bdce -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -lazy-value-info -jump-threading -lazy-value-info -correlated-propagation -domtree -basicaa -aa -memdep -dse -loops -loop-simplify -lcssa-verification -lcssa -aa -scalar-evolution -licm -postdomtree -adce -simplifycfg -domtree -basicaa -aa -loops -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instcombine -float2int -barrier -S < %s
; Derived from C:\Users\Meinersbur\src\llvm\tools\polly\test\jacobi-1d_0.c
; Original command: /root/build/llvm/release/bin/clang -DNDEBUG -mllvm -polly -mllvm -polly-process-unprofitable -mllvm -polly-optree-normalize-phi -mllvm -polly-optree-max-ops=0 -mllvm -debug-only=polly-optree,polly-ast -O3 -DNDEBUG -w -Werror=date-time -save-stats=obj -save-stats=obj -I /root/src/llvm/projects/test-suite/Performance/Polybench-421/utilities -DLARGE_DATASET -ffast-math -DPOLYBENCH_USE_RESTRICT -save-stats=obj -MD -MT Performance/Polybench-421/stencils/jacobi-1d/CMakeFiles/Pb421-perf-restrict_jacobi-1d.dir/jacobi-1d.c.o -MF Performance/Polybench-421/stencils/jacobi-1d/CMakeFiles/Pb421-perf-restrict_jacobi-1d.dir/jacobi-1d.c.o.d -o Performance/Polybench-421/stencils/jacobi-1d/CMakeFiles/Pb421-perf-restrict_jacobi-1d.dir/jacobi-1d.c.o -c /root/src/llvm/projects/test-suite/Performance/Polybench-421/stencils/jacobi-1d/jacobi-1d.c

; ModuleID = 'C:\Users\Meinersbur\src\llvm\tools\polly\test\jacobi-1d_0.c'
source_filename = "C:\5CUsers\5CMeinersbur\5Csrc\5Cllvm\5Ctools\5Cpolly\5Ctest\5Cjacobi-1d_0.c"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

%struct._IO_FILE = type { i32, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, i8*, %struct._IO_marker*, %struct._IO_FILE*, i32, i32, i64, i16, i8, [1 x i8], i8*, i64, i8*, i8*, i8*, i8*, i64, i32, [20 x i8] }
%struct._IO_marker = type { %struct._IO_marker*, %struct._IO_FILE*, i32 }

@polybench_papi_counters_threadid = local_unnamed_addr global i32 0, align 4
@polybench_program_total_flops = local_unnamed_addr global double 0.000000e+00, align 8
@polybench_t_start = common local_unnamed_addr global double 0.000000e+00, align 8
@polybench_t_end = common local_unnamed_addr global double 0.000000e+00, align 8
@.str = private unnamed_addr constant [7 x i8] c"%0.6f\0A\00", align 1
@polybench_c_start = common local_unnamed_addr global i64 0, align 8
@polybench_c_end = common local_unnamed_addr global i64 0, align 8
@stderr = external local_unnamed_addr global %struct._IO_FILE*, align 8
@.str.2 = private unnamed_addr constant [51 x i8] c"[PolyBench] posix_memalign: cannot allocate memory\00", align 1
@.str.3 = private unnamed_addr constant [23 x i8] c"==BEGIN DUMP_ARRAYS==\0A\00", align 1
@.str.4 = private unnamed_addr constant [15 x i8] c"begin dump: %s\00", align 1
@.str.5 = private unnamed_addr constant [2 x i8] c"A\00", align 1
@.str.7 = private unnamed_addr constant [8 x i8] c"%0.2lf \00", align 1
@.str.8 = private unnamed_addr constant [17 x i8] c"\0Aend   dump: %s\0A\00", align 1
@.str.9 = private unnamed_addr constant [23 x i8] c"==END   DUMP_ARRAYS==\0A\00", align 1

; Function Attrs: norecurse nounwind readnone uwtable
define void @polybench_flush_cache() local_unnamed_addr #0 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  ret void
}

; Function Attrs: argmemonly nounwind
declare void @llvm.lifetime.start.p0i8(i64, i8* nocapture) #1

; Function Attrs: nounwind
declare void @free(i8* nocapture) local_unnamed_addr #2

; Function Attrs: argmemonly nounwind
declare void @llvm.lifetime.end.p0i8(i64, i8* nocapture) #1

; Function Attrs: norecurse nounwind readnone uwtable
define void @polybench_prepare_instruments() local_unnamed_addr #0 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  ret void
}

; Function Attrs: norecurse nounwind uwtable
define void @polybench_timer_start() local_unnamed_addr #3 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  store double 0.000000e+00, double* @polybench_t_start, align 8, !tbaa !2
  ret void
}

; Function Attrs: norecurse nounwind uwtable
define void @polybench_timer_stop() local_unnamed_addr #3 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  store double 0.000000e+00, double* @polybench_t_end, align 8, !tbaa !2
  ret void
}

; Function Attrs: nounwind uwtable
define void @polybench_timer_print() local_unnamed_addr #4 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  %0 = load double, double* @polybench_t_end, align 8, !tbaa !2
  %1 = load double, double* @polybench_t_start, align 8, !tbaa !2
  %sub = fsub fast double %0, %1
  %call = tail call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([7 x i8], [7 x i8]* @.str, i64 0, i64 0), double %sub)
  ret void
}

; Function Attrs: nounwind
declare i32 @printf(i8* nocapture readonly, ...) local_unnamed_addr #2

; Function Attrs: nounwind uwtable
define void @polybench_free_data(i8* nocapture %ptr) local_unnamed_addr #4 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  tail call void @free(i8* %ptr) #7
  ret void
}

; Function Attrs: nounwind uwtable
define i8* @polybench_alloc_data(i64 %n, i32 %elt_size) local_unnamed_addr #4 {
entry:
  %ret.i = alloca i8*, align 8
  br label %entry.split

entry.split:                                      ; preds = %entry
  %conv = sext i32 %elt_size to i64
  %mul = mul i64 %conv, %n
  %0 = bitcast i8** %ret.i to i8*
  call void @llvm.lifetime.start.p0i8(i64 8, i8* nonnull %0) #7
  store i8* null, i8** %ret.i, align 8, !tbaa !6
  %call.i = call i32 @posix_memalign(i8** nonnull %ret.i, i64 4096, i64 %mul) #7
  %1 = load i8*, i8** %ret.i, align 8, !tbaa !6
  %tobool.i = icmp eq i8* %1, null
  %tobool2.i = icmp ne i32 %call.i, 0
  %or.cond.i = or i1 %tobool2.i, %tobool.i
  br i1 %or.cond.i, label %if.then.i, label %xmalloc.exit

if.then.i:                                        ; preds = %entry.split
  %2 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6
  %3 = call i64 @fwrite(i8* getelementptr inbounds ([51 x i8], [51 x i8]* @.str.2, i64 0, i64 0), i64 50, i64 1, %struct._IO_FILE* %2) #8
  call void @exit(i32 1) #9
  unreachable

xmalloc.exit:                                     ; preds = %entry.split
  call void @llvm.lifetime.end.p0i8(i64 8, i8* nonnull %0) #7
  ret i8* %1
}

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** nocapture readonly %argv) local_unnamed_addr #4 {
entry:
  %ret.i.i74 = alloca i8*, align 8
  %ret.i.i = alloca i8*, align 8
  br label %entry.split

entry.split:                                      ; preds = %entry
  %0 = bitcast i8** %ret.i.i to i8*
  call void @llvm.lifetime.start.p0i8(i64 8, i8* nonnull %0) #7
  store i8* null, i8** %ret.i.i, align 8, !tbaa !6
  %call.i.i = call i32 @posix_memalign(i8** nonnull %ret.i.i, i64 4096, i64 16000) #7
  %1 = load i8*, i8** %ret.i.i, align 8, !tbaa !6
  %tobool.i.i = icmp eq i8* %1, null
  %tobool2.i.i = icmp ne i32 %call.i.i, 0
  %or.cond.i.i = or i1 %tobool2.i.i, %tobool.i.i
  br i1 %or.cond.i.i, label %if.then.i.i, label %polybench_alloc_data.exit

if.then.i.i:                                      ; preds = %entry.split
  %2 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6
  %3 = call i64 @fwrite(i8* getelementptr inbounds ([51 x i8], [51 x i8]* @.str.2, i64 0, i64 0), i64 50, i64 1, %struct._IO_FILE* %2) #8
  call void @exit(i32 1) #9
  unreachable

polybench_alloc_data.exit:                        ; preds = %entry.split
  call void @llvm.lifetime.end.p0i8(i64 8, i8* nonnull %0) #7
  %4 = bitcast i8** %ret.i.i74 to i8*
  call void @llvm.lifetime.start.p0i8(i64 8, i8* nonnull %4) #7
  store i8* null, i8** %ret.i.i74, align 8, !tbaa !6
  %call.i.i75 = call i32 @posix_memalign(i8** nonnull %ret.i.i74, i64 4096, i64 16000) #7
  %5 = load i8*, i8** %ret.i.i74, align 8, !tbaa !6
  %tobool.i.i76 = icmp eq i8* %5, null
  %tobool2.i.i77 = icmp ne i32 %call.i.i75, 0
  %or.cond.i.i78 = or i1 %tobool2.i.i77, %tobool.i.i76
  br i1 %or.cond.i.i78, label %if.then.i.i79, label %polybench_alloc_data.exit80

if.then.i.i79:                                    ; preds = %polybench_alloc_data.exit
  %6 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6
  %7 = call i64 @fwrite(i8* getelementptr inbounds ([51 x i8], [51 x i8]* @.str.2, i64 0, i64 0), i64 50, i64 1, %struct._IO_FILE* %6) #8
  call void @exit(i32 1) #9
  unreachable

polybench_alloc_data.exit80:                      ; preds = %polybench_alloc_data.exit
  call void @llvm.lifetime.end.p0i8(i64 8, i8* nonnull %4) #7
  %arraydecay = bitcast i8* %1 to double*
  %arraydecay2 = bitcast i8* %5 to double*
  br label %for.body.i

for.body.i:                                       ; preds = %for.body.i, %polybench_alloc_data.exit80
  %indvars.iv.i = phi i64 [ 0, %polybench_alloc_data.exit80 ], [ %indvars.iv.next.i, %for.body.i ]
  %8 = trunc i64 %indvars.iv.i to i32
  %conv.i = sitofp i32 %8 to double
  %add.i = fadd fast double %conv.i, 2.000000e+00
  %div.i = fmul fast double %add.i, 5.000000e-04
  %arrayidx.i = getelementptr inbounds double, double* %arraydecay, i64 %indvars.iv.i
  store double %div.i, double* %arrayidx.i, align 8, !tbaa !2, !alias.scope !8, !noalias !11
  %add3.i = fadd fast double %conv.i, 3.000000e+00
  %div5.i = fmul fast double %add3.i, 5.000000e-04
  %arrayidx7.i = getelementptr inbounds double, double* %arraydecay2, i64 %indvars.iv.i
  store double %div5.i, double* %arrayidx7.i, align 8, !tbaa !2, !alias.scope !11, !noalias !8
  %indvars.iv.next.i = add nuw nsw i64 %indvars.iv.i, 1
  %exitcond.i = icmp eq i64 %indvars.iv.next.i, 2000
  br i1 %exitcond.i, label %init_array.exit, label %for.body.i

init_array.exit:                                  ; preds = %for.body.i
  call fastcc void @kernel_jacobi_1d(double* nonnull %arraydecay, double* nonnull %arraydecay2)
  %cmp = icmp sgt i32 %argc, 42
  br i1 %cmp, label %if.end39, label %if.end46

if.end39:                                         ; preds = %init_array.exit
  %9 = load i8*, i8** %argv, align 8, !tbaa !6
  %10 = load i8, i8* %9, align 1, !tbaa !13
  %phitmp = icmp eq i8 %10, 0
  br i1 %phitmp, label %if.then44, label %if.end46

if.then44:                                        ; preds = %if.end39
  %11 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %12 = call i64 @fwrite(i8* getelementptr inbounds ([23 x i8], [23 x i8]* @.str.3, i64 0, i64 0), i64 22, i64 1, %struct._IO_FILE* %11) #8, !noalias !14
  %13 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %call1.i = call i32 (%struct._IO_FILE*, i8*, ...) @fprintf(%struct._IO_FILE* %13, i8* getelementptr inbounds ([15 x i8], [15 x i8]* @.str.4, i64 0, i64 0), i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.5, i64 0, i64 0)) #8, !noalias !14
  br label %for.body.i82

for.body.i82:                                     ; preds = %if.end.i, %if.then44
  %indvars.iv.i81 = phi i64 [ 0, %if.then44 ], [ %indvars.iv.next.i84, %if.end.i ]
  %14 = trunc i64 %indvars.iv.i81 to i32
  %rem.i = urem i32 %14, 20
  %cmp2.i = icmp eq i32 %rem.i, 0
  br i1 %cmp2.i, label %if.then.i, label %if.end.i

if.then.i:                                        ; preds = %for.body.i82
  %15 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %fputc.i = call i32 @fputc(i32 10, %struct._IO_FILE* %15) #8, !noalias !14
  br label %if.end.i

if.end.i:                                         ; preds = %if.then.i, %for.body.i82
  %16 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %arrayidx.i83 = getelementptr inbounds double, double* %arraydecay, i64 %indvars.iv.i81
  %17 = load double, double* %arrayidx.i83, align 8, !tbaa !2, !alias.scope !14
  %call4.i = call i32 (%struct._IO_FILE*, i8*, ...) @fprintf(%struct._IO_FILE* %16, i8* getelementptr inbounds ([8 x i8], [8 x i8]* @.str.7, i64 0, i64 0), double %17) #8, !noalias !14
  %indvars.iv.next.i84 = add nuw nsw i64 %indvars.iv.i81, 1
  %exitcond.i85 = icmp eq i64 %indvars.iv.next.i84, 2000
  br i1 %exitcond.i85, label %print_array.exit, label %for.body.i82

print_array.exit:                                 ; preds = %if.end.i
  %18 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %call5.i = call i32 (%struct._IO_FILE*, i8*, ...) @fprintf(%struct._IO_FILE* %18, i8* getelementptr inbounds ([17 x i8], [17 x i8]* @.str.8, i64 0, i64 0), i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.5, i64 0, i64 0)) #8, !noalias !14
  %19 = load %struct._IO_FILE*, %struct._IO_FILE** @stderr, align 8, !tbaa !6, !noalias !14
  %20 = call i64 @fwrite(i8* getelementptr inbounds ([23 x i8], [23 x i8]* @.str.9, i64 0, i64 0), i64 22, i64 1, %struct._IO_FILE* %19) #8, !noalias !14
  br label %if.end46

if.end46:                                         ; preds = %if.end39, %print_array.exit, %init_array.exit
  call void @free(i8* nonnull %1) #7
  call void @free(i8* %5) #7
  ret i32 0
}

; Function Attrs: noinline norecurse nounwind uwtable
define internal fastcc void @kernel_jacobi_1d(double* noalias nocapture %A, double* noalias nocapture %B) unnamed_addr #5 {
entry:
  br label %entry.split

entry.split:                                      ; preds = %entry
  %arrayidx6.phi.trans.insert = getelementptr inbounds double, double* %A, i64 1
  %arrayidx21.phi.trans.insert = getelementptr inbounds double, double* %B, i64 1
  br label %for.body

for.body:                                         ; preds = %for.inc33, %entry.split
  %t.03 = phi i32 [ 0, %entry.split ], [ %inc34, %for.inc33 ]
  %.pre = load double, double* %A, align 8, !tbaa !2
  %.pre10 = load double, double* %arrayidx6.phi.trans.insert, align 8, !tbaa !2
  br label %for.body3

for.body3:                                        ; preds = %for.body3, %for.body
  %0 = phi double [ %.pre10, %for.body ], [ %2, %for.body3 ]
  %1 = phi double [ %.pre, %for.body ], [ %0, %for.body3 ]
  %indvars.iv = phi i64 [ 1, %for.body ], [ %indvars.iv.next, %for.body3 ]
  %add = fadd fast double %0, %1
  %indvars.iv.next = add nuw nsw i64 %indvars.iv, 1
  %arrayidx9 = getelementptr inbounds double, double* %A, i64 %indvars.iv.next
  %2 = load double, double* %arrayidx9, align 8, !tbaa !2
  %add10 = fadd fast double %add, %2
  %mul = fmul fast double %add10, 3.333300e-01
  %arrayidx12 = getelementptr inbounds double, double* %B, i64 %indvars.iv
  store double %mul, double* %arrayidx12, align 8, !tbaa !2
  %exitcond = icmp eq i64 %indvars.iv.next, 1999
  br i1 %exitcond, label %for.end, label %for.body3

for.end:                                          ; preds = %for.body3
  %.pre11 = load double, double* %B, align 8, !tbaa !2
  %.pre12 = load double, double* %arrayidx21.phi.trans.insert, align 8, !tbaa !2
  br label %for.body16

for.body16:                                       ; preds = %for.body16, %for.end
  %3 = phi double [ %.pre12, %for.end ], [ %5, %for.body16 ]
  %4 = phi double [ %.pre11, %for.end ], [ %3, %for.body16 ]
  %indvars.iv5 = phi i64 [ 1, %for.end ], [ %indvars.iv.next6, %for.body16 ]
  %add22 = fadd fast double %3, %4
  %indvars.iv.next6 = add nuw nsw i64 %indvars.iv5, 1
  %arrayidx25 = getelementptr inbounds double, double* %B, i64 %indvars.iv.next6
  %5 = load double, double* %arrayidx25, align 8, !tbaa !2
  %add26 = fadd fast double %add22, %5
  %mul27 = fmul fast double %add26, 3.333300e-01
  %arrayidx29 = getelementptr inbounds double, double* %A, i64 %indvars.iv5
  store double %mul27, double* %arrayidx29, align 8, !tbaa !2
  %exitcond8 = icmp eq i64 %indvars.iv.next6, 1999
  br i1 %exitcond8, label %for.inc33, label %for.body16

for.inc33:                                        ; preds = %for.body16
  %inc34 = add nuw nsw i32 %t.03, 1
  %exitcond9 = icmp eq i32 %inc34, 500
  br i1 %exitcond9, label %for.end35, label %for.body

for.end35:                                        ; preds = %for.inc33
  ret void
}

; Function Attrs: nounwind
declare i32 @posix_memalign(i8**, i64, i64) local_unnamed_addr #2

; Function Attrs: nounwind
declare i32 @fprintf(%struct._IO_FILE* nocapture, i8* nocapture readonly, ...) local_unnamed_addr #2

; Function Attrs: noreturn nounwind
declare void @exit(i32) local_unnamed_addr #6

; Function Attrs: nounwind
declare i64 @fwrite(i8* nocapture, i64, i64, %struct._IO_FILE* nocapture) local_unnamed_addr #7

; Function Attrs: nounwind
declare i32 @fputc(i32, %struct._IO_FILE* nocapture) local_unnamed_addr #7

attributes #0 = { norecurse nounwind readnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #1 = { argmemonly nounwind }
attributes #2 = { nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #3 = { norecurse nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #4 = { nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #5 = { noinline norecurse nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #6 = { noreturn nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #7 = { nounwind }
attributes #8 = { cold nounwind }
attributes #9 = { noreturn nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 6.0.0 "}
!2 = !{!3, !3, i64 0}
!3 = !{!"double", !4, i64 0}
!4 = !{!"omnipotent char", !5, i64 0}
!5 = !{!"Simple C/C++ TBAA"}
!6 = !{!7, !7, i64 0}
!7 = !{!"any pointer", !4, i64 0}
!8 = !{!9}
!9 = distinct !{!9, !10, !"init_array: %A"}
!10 = distinct !{!10, !"init_array"}
!11 = !{!12}
!12 = distinct !{!12, !10, !"init_array: %B"}
!13 = !{!4, !4, i64 0}
!14 = !{!15}
!15 = distinct !{!15, !16, !"print_array: %A"}
!16 = distinct !{!16, !"print_array"}
