; RUN: opt %loadPolly -polly-optree-normalize-phi -polly-optree -S < %s
; Derived from C:\Users\Meinersbur\src\llvm\tools\polly\test\ackermann.c
; Original command: /root/build/llvm/release/bin/clang -DNDEBUG -mllvm -polly -mllvm -polly-process-unprofitable -mllvm -polly-optree-normalize-phi -O3 -DNDEBUG -w -Werror=date-time -MD -MT SingleSource/Benchmarks/Shootout/CMakeFiles/Shootout-ackermann.dir/ackermann.c.o -MF SingleSource/Benchmarks/Shootout/CMakeFiles/Shootout-ackermann.dir/ackermann.c.o.d -o SingleSource/Benchmarks/Shootout/CMakeFiles/Shootout-ackermann.dir/ackermann.c.o -c /root/src/llvm/projects/test-suite/SingleSource/Benchmarks/Shootout/ackermann.c

; ModuleID = 'C:\Users\MEINER~1\AppData\Local\Temp\reproduce-aatjwjwo\bugpoint-reduced-simplified.bc'
source_filename = "bugpoint-output-774dc39.bc"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: nounwind readnone uwtable
define void @Ack(i32 %M, i32 %N) local_unnamed_addr #0 {
entry:
  br label %if.end

if.then:                                          ; preds = %tailrecurse.backedge
  ret void

if.end:                                           ; preds = %tailrecurse.backedge, %entry
  %N.tr13 = phi i32 [ %N, %entry ], [ %N.tr.be, %tailrecurse.backedge ]
  %M.tr12 = phi i32 [ %M, %entry ], [ %sub, %tailrecurse.backedge ]
  %cmp1 = icmp eq i32 %N.tr13, 0
  %sub = add nsw i32 %M.tr12, -1
  br i1 %cmp1, label %tailrecurse.backedge, label %if.end3

tailrecurse.backedge:                             ; preds = %if.end3, %if.end
  %N.tr.be = phi i32 [ 0, %if.end3 ], [ 1, %if.end ]
  %cmp = icmp eq i32 %sub, 0
  br i1 %cmp, label %if.then, label %if.end

if.end3:                                          ; preds = %if.end
  br label %tailrecurse.backedge
}

attributes #0 = { nounwind readnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 6.0.0 "}
