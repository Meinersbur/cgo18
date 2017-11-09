# CGO '18 Artifact for DeLICM

The repository contains tools and data to reproduce the measurements
in the paper.


## Content summary of master branch

 - README.md: This file.

 - cgo.py: Zero-option script for artifact evaluators that re-runs all
           experiments, compares with ours, and emits the data used in
           the paper.

 - gittool.py runtest: Run test-suite.

 - gittool.py execjob: Run experiment described in current HEAD commit.

 - execcmp.py: Show or compare experiment data.


## Desciption of this repository's branches

Each branch describes an experiment for running
[Polybench](http://web.cse.ohio-state.edu/~pouchet.2/software/polybench/)
compiled with clang/Polly.

 - A10_nopolly: Baseline compiled at -O3 without Polly.

 - A20_polly: Compile with Polly with default settings (late with DeLICM).

 - A30_polly_early: Compile with Polly at early position (early without DeLICM).

 - A40_polly_late: Compile with Polly at late position (late without DeLICM).

 - A50_polly_early_delicm: Compile with Polly at early position with DeLICM
                           enabled (early with DeLICM).

In addition, the repositories contain the results of the experiments
executed on the compute nodes of
[Monte Leone](http://www.cscs.ch/computers/monte_leone/index.html).

 - leone_A10_nopolly

 - leone_A20_polly

 - leone_A30_polly_early

 - leone_A40_polly_late

 - leone_A50_polly_early_delicm


## Requirements

In addition to the requirements to compile,
[Clang, LLVM](http://llvm.org/docs/GettingStarted.html#requirements),
[Polly](http://polly.llvm.org/get_started.html) and LLVM's
[test-suite](https://llvm.org/docs/TestingGuide.html)
the following software must be installed on the system:

 - [CMake](https://cmake.org) 3.4.3 or later

 - [Ninja](https://ninja-build.org)

 - [Python](https://www.python.org) 2.7 *and* 3.4 or later

 - [Git](https://git-scm.com) 2.5 or later


## Step descriptions of cgo.py

The script cgo.py executes all steps necessary to reproduce the paper's data.
In the following we describe the individual steps.

### Checkout experiment branch (cgo.py)

Checkout a new worktree in /tmp. This is necessary when executing the cgo.py
in the current checkout. Checking out another branch would delete the
currently executing script.

The directories in /tmp are not deleted by the scripts.

### Run gittool.py execjob (cgo.py)

The gittool.py execjob command executes the file run-test-suite.py using the
command line argumets from the Exec: line in the commit message.
run-test-suite.py collects the arguments to run the runtest function
from gittool.py (also invokable using "gittool.py runtest").

Some of the options can be changed using the
RUNTEST_CONFIG_DEFAULT and RUNTEST_CONFIG_OVERRIDE environment variables.
For instance, setting

   RUNTEST_CONFIG_OVERRIDE="--build-threads=2"

limits the number of build processes (compiling/linking) to two,
which is useful in case the host machine does not have enough main memory
for the default number of processes
(Ninja: 1.5 times the number of logical cores).

The stdin/stderr of the run-test-suite.py execution are written into
the files output.txt, stdout.exe, stderr.txt and report.txt in the worktree.

### Checkout LLVM repositories (gittool.py runtest)

This checks out the following repositories into the directory structure
intended for compilation.

 - https://git.llvm.org/git/llvm.git
   into /tmp/persistent/llvm

 - https://git.llvm.org/git/clang.git
   into /tmp/persistent/llvm/tools/clang

 - https://git.llvm.org/git/libcxx.git
   into /tmp/persistent/llvm/projects/libcxx

 - https://git.llvm.org/git/libcxxabi.git
   into /tmp/persistent/llvm/projects/libcxxabi

 - git@github.com:Meinersbur/test-suite.git
   into /tmp/persistent/llvm/projects/test-suite

Polly is not checkout-out but the experiment branches are forks of
https://git.llvm.org/git/polly.git with the run-test-suite.py file added.
This allows modifying the Polly's source code in experiments.

The directory /tmp/persistent is chosen by cgo.py such it can be reused by
multiple experiments. By default, the run-test-suite.py script uses a
unique folder in /tmp.

The repository addresses are hardcoded into gittool.py.
The test-suite is based on https://git.llvm.org/git/test-suite.git
to add Polybench 4.2.1 beta to it.

### Configure the LLVM build directory (gittool.py runtest)

Run CMake to create a build directory.
CMake will use the system's default compiler (likely /usr/bin/c++).
[Ninja](https://ninja-build.org/) is used as build system.

### Build clang (gittool.py runtest)

Compile and link clang and libcxx.so using Ninja.

### Configure the test-suite (gittool.py runtest)

Run CMake to create a build directory in a run-test-suite subdirectory
of the experiment's worktree as created by cgo.py. This folder is
not reused for multiple experiments since the binaries change with
the compiler options used. The bootstrapped compiler from the
previous step is used.

Only Polybench in the test-suite's "Performance" directory is compiled.

### Build the test-suite (gittool.py runtest)

Compile and link the Polybench benchmarks.

### Run the benchmarks (gittool.py runtest)

Invoke [llvm-lit](https://llvm.org/docs/CommandGuide/lit.html) on
the run-test-suite build.
Lit runs the compiled executables, verifies the correct output and
collects all measurements which are written into an output.json file
of the run-test-suite directory. With multiple executions, the output
files are "output-{num}.json", one for each execution.

To re-run this step using leone's precompiled binaries,
checkout one of its branches and run in the directory:

    $ /tmp/persistent/llvm-build/bin/llvm-lit -sv run-test-suite -o run-test-suite/output.json

### Commit the results (gittool.py execjob)

All files, including the output.txt and run-test-suite/output.json are
added to a new commit. From this commit a new
branch "{hostname}_{branchname}" is created.

The branches prefixed with "leone_" are also the result of this process.

### Compare results with results from leone (execcmp.py)

execmp.py is tool based on
[compare.py](http://lists.llvm.org/pipermail/llvm-dev/2016-October/105739.html).
Among the changes is the ability to extract the output.json when given a
branch name.

The output shows the execution time of the {hostname} run, the run on leone,
and the difference in percent. by default, multiple samples are summarized
using the median.

### Static evaluation (execcmp.py)

Prints the number of transformations performed by DeLICM in each configuration.

### Runtime evaluation (execcmp.py)

Prints the speedups of the Polly-compiled benchmarks relative to the baseline.


## Modifications to the original Polybench 4.2.1 beta.

The Polybench in the
[Github repository](https://github.com/Meinersbur/test-suite/tree/cgo18/Performance)
has been modified from the original obtainable at
[Sourceforge](https://sourceforge.net/projects/polybench/).
The modifications are as follows:

 - The build system has been changed to be compatible with LLVM's
   test-suite which uses CMake.

 - To avoid the problem in LLVM in which JumpThreading skips a loop's exit
   check condition has been avoided by peeling off the first loop iteration
   for which this occurs in some benchmarks.

 - "__attribute__((noinline))" has been added to the kernels to avoid mixing
   of the performance-critical code with control code.

 - Short-running kernels are executed multiple times. Polybench benchmark
   datasets are chosen to correspond to working set sizes, not runtime.
   For instance, gesummv iterates over each matrix element just once,
   such that it finishes quickly even with EXTRALARGE_DATASET.

Explanation of compiler options used in the experiments:

 - "-ffast-math" allows to assume that libm functions do not have global
   side-effects, e.g. set errno. For instance, "correlation" uses sqrt.
   Without this flag, Polly does not try to optimize it.

 - "-march=native", among other influences in the backend, allows the vectorizer
   to chose the host platform's vector width and vector instruction set.

 - -mllvm -inline-threshold=4096 increases the likelyhood of functions being inlined.
   This is necessary for the boost benchmarks, such that the kernel is
   collapsed into a single function.

 - "-fno-exceptions" disables exceptions for the boost benchmarks. Polly
   currently does not try to optimize code that could throw exceptions.

 - "-mllvm -polly-optree-normalize-phi" enables the forward operand-tree
   to look through PHI nodes. It currently causes a significant
   compile-time increases, so is not enabled by default.

 - "-mllvm -polly-optree-max-ops=0" disables a time-out for forward
   operand-tree cause by the aforementioned option.
