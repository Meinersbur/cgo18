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
import tempfile


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


    persistentdir = os.environ.get('persistentdir')
    if persistentdir is None:
        persistentdir = tempfile.mkdtemp(prefix='persistent-')
    persistentdir = os.path.abspath(persistentdir)



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


    if config.polly_source_dir is None:
        config.polly_source_dir = workdir
    if config.llvm_source_dir is None and persistentdir is not None:
        config.llvm_source_dir = os.path.join(persistentdir, 'llvm')
    if config.llvm_build_dir is None and persistentdir is not None:
        config.llvm_build_dir = os.path.join(persistentdir, 'llvm-build')
    if config.suite_build_dir is None:
        config.suite_build_dir = os.path.join(workdir, 'run-test-suite')


    use_perf = config.suite_build_useperf
    has_perf = False
    try:
        invoke('perf', 'stat', 'ls')
        has_perf = True
    except:
        pass
    print("Has_perf result is {has_perf} (use_perf={use_perf})".format(has_perf=has_perf,use_perf=use_perf))

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
