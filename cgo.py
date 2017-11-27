#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

from gittool import *
import platform
import os
import tempfile

script = os.path.abspath(sys.argv[0])
scriptdir = os.path.dirname(script)


def main():
    hostname = platform.node()
    gittool = os.path.join(scriptdir, 'gittool.py')
    execcmp = os.path.join(scriptdir, 'execcmp.py')

    workdir = tempfile.mkdtemp(prefix='job-')
    invoke('git', 'worktree', 'add', workdir)
    rep = Repository2.from_directory(workdir)

    def exec_on_host(srcbranch):
        dstbranch = hostname + '_' + srcbranch
        refbranch = 'leone_' + srcbranch
        if rep.has_branch(dstbranch):
            print("Already executed " + srcbranch + ", delete branch " + dstbranch + " to rerun")
        else:
            if not rep.has_branch(srcbranch):
                rep.invoke_git('branch', srcbranch, 'origin/'+srcbranch)
            rep.checkout(srcbranch)
            invoke('python3',
                   gittool,'execjob',
                   '--persistentdir', os.path.join(tempfile.gettempdir(), 'persistent'),
                   '--dstname', dstbranch,
                   cwd=workdir)
        print("# Compare result to leone:")
        invoke('python3',
               execcmp, refbranch, 'vs', dstbranch,
               '-a',
               cwd=workdir)
        print()

    exec_on_host('A10_nopolly')
    exec_on_host('A20_polly')
    exec_on_host('A30_polly_early')
    exec_on_host('A40_polly_late')
    exec_on_host('A50_polly_early_delicm')
    print()

    print("## Static evaluation")
    def print_stats(branch, metric, desc):
        print("#",desc)
        try:
          invoke('python3', execcmp, branch, 'vs', '-a', '-f', '--no-sort', '--integer',  '-m', metric)
        except:
          print("Extracting data failed; The output 'Unknown metric <metric>' may also occur if all data points are zero.")
          print()

    def print_transformations(branch):
        print_stats(branch, 'polly-optree.TotalInstructionsCopied+', "Forwarded instructions")
        print_stats(branch, 'polly-optree.TotalReloads+polly-optree.TotalKnownLoadsForwarded', "Forwarded loads")
        print_stats(branch, 'polly-delicm.MappedValueScalars+', "Value mappings")
        print_stats(branch, 'polly-delicm.MappedPHIScalars+', "PHI mappings")

    print("# Early")
    print_transformations(hostname + '_A50_polly_early_delicm')
    print("# Late")
    print_transformations(hostname + '_A20_polly')

    def print_scalaropts_postops(branch):
        print_stats(branch, 'polly-simplify.NumValueWritesInLoops0+', "Value writes before DeLICM")
        print_stats(branch, 'polly-simplify.NumPHIWritesInLoops0+', "PHI writes before DeLICM")
        print_stats(branch, 'polly-simplify.NumValueWritesInLoops1+', "Value writes after DeLICM")
        print_stats(branch, 'polly-simplify.NumPHIWritesInLoops1+', "PHI writes after DeLICM")

    print("# Early")
    print_scalaropts_postops(hostname + '_A50_polly_early_delicm')
    print_stats(hostname + '_A30_polly_early', 'polly-opt-isl.FirstLevelTileOpts+', "Post-ops: Tilings (without DeLICM)")
    print_stats(hostname + '_A50_polly_early_delicm', 'polly-opt-isl.FirstLevelTileOpts+', "Post-ops: Tilings (with DeLICM)")
    print_stats(hostname + '_A30_polly_early', 'polly-opt-isl.MatMulOpts+', "Post-ops: Matrix-multiplications (without DeLICM)")
    print_stats(hostname + '_A50_polly_early_delicm', 'polly-opt-isl.MatMulOpts+', "Post-ops: Matrix-multiplications (with DeLICM)")

    print("# Late")
    print_scalaropts_postops(hostname + '_A20_polly')
    print_stats(hostname + '_A40_polly_late', 'polly-opt-isl.FirstLevelTileOpts+', "Post-ops: Tilings (without DeLICM)")
    print_stats(hostname + '_A20_polly', 'polly-opt-isl.FirstLevelTileOpts+', "Post-ops: Tilings (with DeLICM)")
    print_stats(hostname + '_A40_polly_late', 'polly-opt-isl.MatMulOpts+', "Post-ops: Matrix-multiplications (without DeLICM)")
    print_stats(hostname + '_A20_polly', 'polly-opt-isl.MatMulOpts+', "Post-ops: Matrix-multiplications (with DeLICM)")
    print()

    print("## Runtime evaluation")
    def print_speedup(config, desc):
        print("#",desc)
        invoke('python3',
           execcmp, hostname + '_A10_nopolly', 'vs', hostname + '_' + config, '-a', '--speedups', '--no-sort')

    print_speedup('A30_polly_early', "Early")
    print_speedup('A50_polly_early_delicm', "Early DeLICM")
    print_speedup('A40_polly_late', "Late")
    print_speedup('A20_polly', "Late DeLICM")


if __name__ == '__main__':
    main()

