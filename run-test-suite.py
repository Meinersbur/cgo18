#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import multiprocessing
import argparse
import configparser
import shlex
import shutil
import sys
from distutils.util import strtobool
from gittool import Repository2, Commit, Branch, Remote, invoke, checkout_sub, llvm, REVISION, revToStr, RuntestConfig, parseRev, shjoin
import gittool
import platform


def try_display(filename):
    try:
        with open(filename, 'r') as f:
            print("\n{filename}:".format(filename=filename))
            print(f.read())
    except:
        print("Could not access {filename}".format(filename=filename),file=sys.stderr)





def main(argv=sys.argv[1:]):
    hostname = platform.node()

    print("Running on:", hostname)

    parser = argparse.ArgumentParser()
    gittool.RuntestConfig.add_runtest_arguments(parser)

    print("job config:" , shjoin(argv))
    args = parser.parse_args(args=argv)
    config = RuntestConfig.from_cmdargs(args)
    print("Parsed config:", config.get_cmdline())
    #config.llvm_source_dir = args.llvm_source_dir

    workdir = '.'
    workdir = os.path.abspath(workdir)


    persistentdir = os.environ['persistentdir']
    persistentdir = os.path.abspath(persistentdir)

    #tmpdir = os.environ['tmpdir']
    #messsagefile = os.environ['messagefile']
    #use_perf = os.environ.get('use_perf',None)

    default_config = os.environ.get('RUNTEST_CONFIG_DEFAULT','')
    print("default config:" , default_config)
    default_config = shlex.split(default_config)
    default_config,_ = parser.parse_known_args(default_config)
    if _:
        print("Warning: unknown default args:",_)
    default_config = RuntestConfig.from_cmdargs(default_config)

    override_config = os.environ.get('RUNTEST_CONFIG_OVERRIDE','')
    print("override config:" , override_config)
    override_config = shlex.split(override_config)
    override_config,_ = parser.parse_known_args(override_config)
    if _:
        print("Warning: unknown default args:",_)
    override_config = RuntestConfig.from_cmdargs(override_config)

    config.merge(default_config)
    override_config.merge(config)
    config = override_config

    print("effective config:", config.get_cmdline())


    #slave_llvmcmake = shlex.split(os.environ.get('llvmcmake',''))
    #slave_llvmflags= shlex.split(os.environ.get('llvmflags',''))
    #slave_lntargs = shlex.split(os.environ.get('lntargs',''))
    #slave_testsuitecmakedefs = shlex.split(os.environ.get('testsuitecmake',''))
    #slave_testsuiteflags = shlex.split(os.environ.get('testsuiteflags',''))
    #slave_testsuitemllvm  = shlex.split(os.environ.get('testsuitemllvm',''))
    #exec_cpus = os.environ.get('exec_cpus', None)
    #if exec_cpus is not None:
    #    exec_cpus = int(exec_cpus)
    #compile_cpus = os.environ.get('compile_cpus', None)
    #if compile_cpus is not None:
    #    compile_cpus = int(compile_cpus)

    if config.polly_source_dir is None:
        config.polly_source_dir = workdir
    if config.llvm_source_dir is None:
        config.llvm_source_dir = os.path.join(persistentdir, 'llvm')
    if config.llvm_build_dir is None:
        config.llvm_build_dir = os.path.join(persistentdir, 'llvm-build')
    if config.suite_build_dir is None:
        config.suite_build_dir = os.path.join(workdir, 'run-test-suite')

    #messsagefile = os.path.abspath(messsagefile)

    #conffile = os.path.join(workdir, 'run-test-suite.ini')
    #pollysrcdir = workdir # os.path.join(workdir, 'polly')
    #testsuitesrcdir = os.path.join(llvm_source_dir, 'projects', 'test-suite')
    #lntbuilddir = os.path.join(persistentdir, 'lnt')
    #lntpython = os.path.join(lntbuilddir, 'bin','python')
    #lnt = os.path.join(lntbuilddir, 'bin','lnt')

    #config = configparser.ConfigParser()
    #config.read(conffile)

    #baserev = parseRev(config['llvm']['base'])
    #llvmrev = parseRev(config['llvm']['revision'])
    #llvmconfig = slave_llvmcmake + shlex.split(config['llvm']['cmake'])
    #llvmconfig = ['-D' + conf for conf in llvmconfig]
    #job_llvmflags =  shlex.split(config.get('llvm', 'flags', fallback=''))

    #lntargs = slave_lntargs + shlex.split(config['lnt']['args'])
    #lntrev = parseRev(config.get('lnt', 'revision', fallback=None), default=baserev)

    #testsuiterev =  parseRev( config.get('test-suite', 'revision', fallback=None), default=baserev)
    #testsuitecmakedefs = slave_testsuitecmakedefs + shlex.split(config['test-suite']['cmake'])
    #testsuiteflags = slave_testsuiteflags + shlex.split(config['test-suite']['flags'])
    #testsuitemllvm = slave_testsuitemllvm + shlex.split(config['test-suite']['mllvm'])
    #testsuitemultisample = config['test-suite']['multisample']
    #if len(testsuitemultisample) == 0 or testsuitemultisample.isspace():
    #    testsuitemultisample=1
    #else:
    #    testsuitemultisample=int(testsuitemultisample)
    #max_procs = config['test-suite']['max_procs']
    #testsuiteonly = shlex.split(config['test-suite']['only'])
    #if len(max_procs)==0 or max_procs.isspace():
    #    max_procs=None
    #else:
    #    max_procs = int(max_procs)
    #max_load = config['test-suite']['max_load']
    #if len(max_load)==0 or max_load.isspace():
    #    max_load=None
    #else:
    #    max_load = float(max_load)
    #testsuitetaskset = config['test-suite']['taskset'].lower() in  ['true', '1', 't', 'y', 'yes']

    #llvmflags = slave_llvmflags + job_llvmflags

    #if llvmrev is None:
    #    llvmrev = baserev

    use_perf = config.suite_build_useperf
    has_perf = False
    try:
         invoke('perf', 'stat', 'ls')
         has_perf = True
    except:
         pass
    print("Has_perf result is {has_perf} (use_perf={use_perf})".format(has_perf=has_perf,use_perf=use_perf))

    #with open(messsagefile, 'r+') as file:
    #    msg = file.read()
    #    msg = '[{rev}] {msg}'.format(rev= revToStr(baserev), msg=msg )
    #    file.seek(0)
    #    file.truncate()
    #    file.write(msg)



    try_display('/proc/cpuinfo')
    try_display('/proc/meminfo')
    try_display('/proc/loadavg')
    try_display('/proc/uptime')
    try_display('/proc/version')


    config.llvm_checkout = True
    config.llvm_configure = True

    gittool.runtest(config,print_logs=True,enable_svn=False)


if __name__ == '__main__':
    main()
