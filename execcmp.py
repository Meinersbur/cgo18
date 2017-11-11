#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

from gittool import Repository2, Commit, Branch, Remote, invoke, checkout_sub, llvm, REVISION, revToStr, TemporaryDirectory
import tarfile
import io

"""Tool to filter, organize, compare and display benchmarking results. Usefull
for smaller datasets. It works great with a few dozen runs it is not designed to
deal with hundreds.
Requires the pandas library to be installed."""
import pandas as pd
import sys
import os.path
import re
import numbers
import argparse
import six

def read_lit_json(filename, handle=None):
    import json
    jsondata = json.load(open(filename) if handle is None else handle)
    testnames = []
    columns = []
    columnindexes = {}
    info_columns = ['hash']
    for test in jsondata['tests']:
        if "name" not in test:
            print("Skipping unnamed test!")
            continue
        if "metrics" not in test:
            print("Warning: '%s' has No metrics!" % test['name'])
            continue
        for name in test["metrics"].keys():
            if name not in columnindexes:
                columnindexes[name] = len(columns)
                columns.append(name)
        for name in test.keys():
            if name not in columnindexes and name in info_columns:
                columnindexes[name] = len(columns)
                columns.append(name)

    nan = float('NaN')
    data = []
    for test in jsondata['tests']:
        if "name" not in test:
            print("Skipping unnamed test!")
            continue
        name = test['name']
        if 'shortname' in test:
            name = test['shortname']
        testnames.append(name)

        datarow = [nan] * len(columns)
        if "metrics" in test:
            for (metricname, value) in six.iteritems(test['metrics']):
                datarow[columnindexes[metricname]] = value
        for (name, value) in six.iteritems(test):
            index = columnindexes.get(name)
            if index is not None:
                datarow[index] = test[name]
        data.append(datarow)
    index = pd.Index(testnames, name='Program')
    return pd.DataFrame(data=data, index=index, columns=columns)

def read_report_simple_csv(filename):
    return pd.read_csv(filename, na_values=['*'], index_col=0, header=0)

def read(name, handle=None):
    if name.endswith(".json"):
        return read_lit_json(name, handle=handle)
    if name.endswith(".csv"):
        return read_report_simple_csv(name, handle=handle)
    raise Exception("Cannot determine file format");


def execcmp_cmp(lhs,rhs,config):
    with TemporaryDirectory(prefix='execcmp-') as tmpdir:
        lhsbot,lhsname = infer_branch(rep,lhs)
        rhsbot,rhsname = infer_branch(rep,rhs)

        lhstar = os.path.join(tmpdir, lhsname + '.tar')
        rhstar = os.path.join(tmpdir, rhsname + '.tar')

        rep.invoke_git('archive',  lhsbot , 'run-test-suite/build/output*.json', '-o', lhstar)
        rep.invoke_git('archive',  rhsbot , 'run-test-suite/build/output*.json', '-o', rhstar)

        lhs_d, lhs_merged = readtar(lhstar, config)
        rhs_d, rhs_merged = readtar(rhstar, config)
        data = pd.concat([lhs_merged, rhs_merged], names=['l/r'], keys=[lhsname, rhsname])

        if config.show_diff is None:
            config.show_diff = True

        return process_compate(data,config,nfiles=2)


rep = Repository2.from_directory('.')

def execcmp_show(lhs,config):
    with TemporaryDirectory(prefix='exec-') as tmpdir:
        lhsbot,lhsname = infer_branch(rep,lhs)
        lhstar = os.path.join(tmpdir, lhsname + '.tar')
        rep.invoke_git('archive',  lhsbot , 'run-test-suite/build/output*.json', '-o', lhstar)

        lhsdir = os.path.join(tmpdir, 'lhs')
        os.makedirs(lhsdir)
        rhsdir = os.path.join(tmpdir, 'rhs')
        os.makedirs(rhsdir)

        lhs_d, lhs_merged = readtar(lhstar, config)

        if config.show_diff is None:
            config.show_diff = False

        #return process_compate(lhs_d,config,nfiles=lhs_d.index.get_level_values(0).nunique())

        data = pd.concat([lhs_merged], names=['l/r'], keys=[lhsname])
        return process_compate(data,config,nfiles=1)





def readmulti(filenames,tmpdir):
    # Read datasets
    datasetnames = []
    uniquenames = set()
    datasets = []
    prev_index = None

    def readone(filename, handle=None,name=None):
        nonlocal prev_index,datasetnames,datasets,uniquenames

        data = read(filename,handle=handle)
        if name is None:
            name = os.path.basename(filename)
        # drop .json/.csv suffix; TODO: Should we rather do this in the printing
        # logic?
        for ext in ['.csv', '.json']:
            if name.endswith(ext):
                name = name[:-len(ext)]
        datasets.append(data)
        suffix = ""
        count = 0
        while True:
            if name+suffix not in datasetnames:
                break
            suffix = str(count)
            count +=1

        datasetnames.append(name+suffix)
        uniquenames |= {name}

        # Warn if index names are different
        if prev_index is not None and prev_index.name != data.index.name:
            sys.stderr.write("Warning: Mismatched index names: '%s' vs '%s'\n"
                             % (prev_index.name, data.index.name))
        prev_index = data.index

    def readtar(tar,name) :
        lhstar =  tarfile.open(tar)
        ljson = [ti for ti in lhstar.getmembers() if jsonnamerefes.match(ti.name)]
        for ti in ljson:
            filename = jsonnamerefes.match(ti.name).group('filename')
            handle = io.TextIOWrapper(lhstar.extractfile(ti),encoding='utf-8')
            readone(filename,handle,name=name)

    def readarg(arg):
        if os.path.isfile(arg):
            readone(filename=arg)
            return

        lhsbot,lhsname = infer_branch(rep,arg)
        if rep.has_branch(lhsbot):
            pass
        elif rep.has_branch(arg):
            lhsbot = arg
            lhsname = arg
        else:
            raise Exception("Input {arg} is no file and there is no branch {arg}".format(arg=arg,lhsbot=lhsbot) )

        lhstar = os.path.join(tmpdir, lhsname + '.tar')
        rep.invoke_git('archive',  lhsbot , 'run-test-suite/output*.json', '-o', lhstar)

        readtar(lhstar,lhsname)


    for filename in filenames:
        readarg(filename)

    # Merge datasets
    d = pd.concat(datasets, axis=0, names=['run'], keys=datasetnames)

    return d,datasetnames,uniquenames



def add_diff_column(d, absolute_diff=False, speedups=False):
    values = d.unstack(level=0)

    has_two_runs = d.index.get_level_values(0).nunique() == 2
    if has_two_runs:
        values0 = values.iloc[:,0]
        values1 = values.iloc[:,1]
    else:
        values0 = values.min(axis=1)
        values1 = values.max(axis=1)

    # Quotient or absolute difference?
    if absolute_diff:
        values['diff'] = values1 - values0
    else:
        if speedups:
            values['diff'] = values0 / values1
        else:
            values['diff'] = values1 / values0
            values['diff'] -= 1.0

    # unstack() gave us a complicated multiindex for the columns, simplify
    # things by renaming to a simple index.
    values.columns = [(c[1] if c[1] else c[0]) for c in values.columns.values]
    return values

def filter_failed(data, key='Exec'):
    return data.loc[data[key] == "pass"]

def filter_short(data, key='Exec_Time', threshold=0.2):
    return data.loc[data[key] >= threshold]

def filter_same_hash(data, key='hash'):
    assert key in data.columns
    assert data.index.get_level_values(0).nunique() > 1

    return data.groupby(level=1).filter(lambda x: x[key].nunique() != 1)

def filter_blacklist(data, blacklist):
    return data.loc[~(data.index.get_level_values(1).isin(blacklist))]

def filter_whitelist(data, whitelist):
    return data.loc[data.index.get_level_values(1).isin(whitelist)]

def print_filter_stats(reason, before, after):
    n_before = len(before.groupby(level=1))
    n_after = len(after.groupby(level=1))
    n_filtered = n_before - n_after
    if n_filtered != 0:
        print("%s: %s (filtered out)" % (reason, n_filtered))

# Truncate a string to a maximum length by keeping a prefix, a suffix and ...
# in the middle
def truncate(string, prefix_len, suffix_len):
    return re.sub("^(.{%d}).*(.{%d})$" % (prefix_len, suffix_len),
                  "\g<1>...\g<2>", string)

# Search for common prefixes and suffixes in a list of names and return
# a (prefix,suffix) tuple that specifies how many characters can be dropped
# for the prefix/suffix. The numbers will be small enough that no name will
# become shorter than min_len characters.
def determine_common_prefix_suffix(names, min_len=8):
    if len(names) <= 1:
        return (0,0)
    name0 = names[0]
    prefix = name0
    prefix_len = len(name0)
    suffix = name0
    suffix_len = len(name0)
    shortest_name = len(name0)
    for name in names:
        if len(name) < shortest_name:
            shortest_name = len(name)
        while prefix_len > 0 and name[:prefix_len] != prefix:
            prefix_len -= 1
            prefix = name0[:prefix_len]
        while suffix_len > 0 and name[-suffix_len:] != suffix:
            suffix_len -= 1
            suffix = name0[-suffix_len:]

    if suffix[0] != '.' and suffix[0] != '_':
        suffix_len = 0
    suffix_len = max(0, min(shortest_name - prefix_len - min_len, suffix_len))
    prefix_len = max(0, min(shortest_name - suffix_len, prefix_len))
    return (prefix_len, suffix_len)

def format_diff(value):
    if not isinstance(value, numbers.Integral):
        return "%6.1f%%" % (value * 100.)
    else:
        return "%-5d" % value

shortenre = re.compile(r'^.*\/(?P<abbrv>[^\/]+)\.test$')
def extract_abbrv(x):
    m = shortenre.match(x)
    if not m:
        return x
    return m.group('abbrv')

def print_result(d, limit_output=True, shorten_names=True,
                 show_diff_column=True, sortkey='diff',speedups=False,abbrv_names=False,nocolumns=False,aslist=False,absolute_diff=False):
    if sortkey is not None:
        # sort (TODO: is there a more elegant way than create+drop a column?)
        d['$sortkey'] = d[sortkey].abs()
        d = d.sort_values("$sortkey", ascending=False)
        del d['$sortkey']
    if not show_diff_column:
        del d['diff']

    dataout = d
    if limit_output:
        # Take 15 topmost elements
        dataout = dataout.head(30)

    if nocolumns:
        for c in dataout.columns:
            if c=='diff':
                continue
            del dataout[c]

    # Turn index into a column so we can format it...
    # TODO: Insert at end of it, how to determine the number of columns?
    dataout.insert(0, 'Program', dataout.index)

    formatters = dict()
    if speedups or absolute_diff:
        pass
    else:
        formatters['diff'] = format_diff

    formatters['Program'] = lambda x: x
    if abbrv_names:
        formatters['Program'] = extract_abbrv

    if shorten_names:
        nameformatter = formatters['Program']

        drop_prefix, drop_suffix = determine_common_prefix_suffix([nameformatter(p) for p in dataout.Program])
        def truncator(y):
            x = nameformatter(y)
            if drop_suffix > 0:
                x = x[drop_prefix:-drop_suffix]
            else:
                x = x[drop_prefix:]
            return "%-76s" % truncate(x, 1, 72)
        formatters['Program'] = truncator
        # TODO: it would be cool to drop prefixes/suffix common to all names

    float_format = lambda x: "%6.3f" % (x,)
    pd.set_option("display.max_colwidth", 0)
    out = dataout.to_string(index=False, justify='left',
                            float_format=float_format, formatters=formatters)

    if aslist:
        newout = []
        for line in out.splitlines(keepends=False):
            newout.append('(' +  ', '.join( line.split()) + ')')
        out = '\n'.join(newout)

    print(out)
    print(d.describe())


jsonnamerefes = re.compile(r'^run-test-suite/(?P<filename>output[^.]*\.json)$')



def infer_branch(rep, arg):
    remote = None
    if '/' in arg:
        remote,s = arg.split('/',1)
    else:
        s = arg

    bot,job = s.split('_',1)
    if remote is None:
        remote = bot
    for branch in rep.get_remote(remote).branches():
        basename = branch.get_basename()
        if basename.startswith(bot + '_'):
            basename = basename[len(bot)+1:]
        if basename.startswith(job):
            return branch,branch.get_basename()

    return arg,arg




def add_options(parser):
    parser.add_argument('-a', '--all', action='store_true', help="Show all programs")
    parser.add_argument('-f', '--full', action='store_true')
    parser.add_argument('--abbrv-names', action='store_true')
    parser.add_argument('-m', '--metric', action='append', dest='metrics',  default=[])
    parser.add_argument('--nodiff', action='store_false', dest='show_diff',  default=None)
    parser.add_argument('--diff', action='store_true', dest='show_diff')
    parser.add_argument('--absolute-diff', action='store_true')
    parser.add_argument('--nocolumns', action='store_true')
    parser.add_argument('--speedups', action='store_true')
    parser.add_argument('--filter-short', nargs='?', const=0.5, type=float, dest='filter_short')
    parser.add_argument('--no-filter-failed', action='store_false',
                        dest='filter_failed', default=True)
    parser.add_argument('--filter-hash', action='store_true',
                        dest='filter_hash', default=False)
    parser.add_argument('--filter-blacklist',
                        dest='filter_blacklist', default=None)
    parser.add_argument('--filter-whitelist',
                        dest='filter_whitelist', default=None)
    parser.add_argument('--filter-program', default=[], action='append', dest='filter_program')
    parser.add_argument('--merge-average', action='store_const',
                        dest='merge_function', const=pd.DataFrame.mean,
                        default=pd.DataFrame.median)
    parser.add_argument('--merge-min', action='store_const',
                        dest='merge_function', const=pd.DataFrame.min)
    parser.add_argument('--merge-max', action='store_const',
                        dest='merge_function', const=pd.DataFrame.max)
    parser.add_argument('--merge-median', action='store_const',
                        dest='merge_function', const=pd.DataFrame.median)
    parser.add_argument('--no-sort', '--nosort', action='store_true')
    parser.add_argument('--as-list', action='store_true')
    parser.add_argument('--integer', '--integers', action='store_true')



def main():
    parser = argparse.ArgumentParser(prog='execcmp.py')
    add_options(parser)
    parser.add_argument('files', metavar='FILE', nargs='+')

    config = parser.parse_args()

    with TemporaryDirectory(prefix='execcmp-') as tmpdir:
        return execcmp_compare(files=config.files,config=config,tmpdir=tmpdir)



def execcmp_compare(files,config,tmpdir):
    # Read inputs
    if "vs" in files:
        split = files.index("vs")
        lhs = files[0:split]
        rhs = files[split+1:]

        # Filter minimum of lhs and rhs
        lhs_d,lhs_datasetnames,lhs_uniquenames = readmulti(lhs,tmpdir=tmpdir)
        lhs_merged = config.merge_function(lhs_d, level=1)
        rhs_d,rhs_datasetnames,rhs_uniquenames = readmulti(rhs,tmpdir=tmpdir)
        rhs_merged = config.merge_function(rhs_d, level=1)

        lhsname = 'lhs'
        if len(lhs_uniquenames)==1:
            lhsname, = lhs_uniquenames
        rhsname = 'rhs'
        if len(rhs_uniquenames)==1:
            rhsname, = rhs_uniquenames

        # Combine to new dataframe
        data = pd.concat([lhs_merged, rhs_merged], names=['l/r'], keys=[lhsname, rhsname])
        nfiles = 2
    else:
        data,datasetnames,uniquenames = readmulti(files,tmpdir=tmpdir)
        nfiles = len(files)

    if config.show_diff is None:
        config.show_diff = nfiles > 1

    process_compate(data,config,nfiles)


def process_compate(data, config, nfiles):
    #assert(nfiles == data.index.get_level_values(0).nunique())


    # Decide which metric to display / what is our "main" metric
    metrics = config.metrics
    if len(metrics) == 0:
        defaults = [ 'Exec_Time', 'exec_time', 'Value', 'Runtime' ]
        for defkey in defaults:
            if defkey in data.columns:
                metrics = [defkey]
                break
    if len(metrics) == 0:
        sys.stderr.write("No default metric found and none specified\n")
        sys.stderr.write("Available metrics:\n")
        for column in data.columns:
            sys.stderr.write("\t%s\n" % column)
        sys.exit(1)
    for metric in metrics:
        problem = False
        for m in metric.split('+'):
            if m and m not in data.columns:
                sys.stderr.write("Unknown metric '%s'\n" % metric)
                sys.exit(1)



    # Filter data
    proggroup = data.groupby(level=1)
    initial_size = len(proggroup.indices)
    print("Tests: %s" % (initial_size,))
    if config.filter_failed and hasattr(data, 'Exec'):
        newdata = filter_failed(data)
        print_filter_stats("Failed", data, newdata)
        newdata = newdata.drop('Exec', 1)
        data = newdata
    if config.filter_short is not None:
        newdata = filter_short(data, metric, threshold=config.filter_short)
        print_filter_stats("Short Running", data, newdata)
        data = newdata
    if config.filter_hash and 'hash' in data.columns and nfiles > 1:
        newdata = filter_same_hash(data)
        print_filter_stats("Same hash", data, newdata)
        data = newdata
    if config.filter_blacklist:
        blacklist = open(config.filter_blacklist).readlines()
        blacklist = [line.strip() for line in blacklist]
        newdata = filter_blacklist(data, blacklist)
        print_filter_stats("In Blacklist", data, newdata)
        data = newdata
    if config.filter_whitelist:
        whitelist = open(config.filter_whitelist).readlines()
        whitelist = [line.strip() for line in whitelist]
        newdata = filter_whitelist(data, whitelist)
        print_filter_stats("In Whitelist", data, newdata)
        data = newdata
    for filter_program in config.filter_program:
        newdata = data.loc[data.index.get_level_values(1).str.contains(filter_program)]
        print_filter_stats("Program", data, newdata)
        data = newdata
    final_size = len(data.groupby(level=1))
    if final_size != initial_size:
        print("Remaining: %d" % (final_size,))

    # Reduce / add columns
    print("Metric: %s" % metric)
    if len(metric) > 0:
        for metric in metrics:
            summands = metric.split('+')
            if len(summands) > 1:
                colsum = None
                for summand in summands:
                    if not summand:
                        continue
                    negative = False
                    if summand[0]=='-':
                        summand = summand[1:]
                        negative = True
                    sumdata = data[summand].copy().fillna(value=0)
                    if colsum is None:
                        if negative:
                            data[metric] = sumdata.neg()
                        else:
                            data[metric] = sumdata
                        colsum = data[metric]
                        continue
                    if negative:
                        data[metric] -= sumdata
                    else:
                        data[metric] += sumdata
        data = data[metrics]
        if config.integer:
            data = data.astype('int')

    data = add_diff_column(data,absolute_diff=config.absolute_diff, speedups=config.speedups)

    if config.no_sort:
        sortkey = None
    elif nfiles == 1:
        sortkey = data.columns[0]
    else:
        sortkey = 'diff'

    # Print data
    print("")
    shorten_names = not config.full
    limit_output = not config.all
    print_result(data, limit_output, shorten_names, config.show_diff or config.speedups, sortkey,speedups=config.speedups,abbrv_names=config.abbrv_names,nocolumns=config.nocolumns,absolute_diff=config.absolute_diff,aslist=config.as_list)



if __name__ == '__main__':
    main()
