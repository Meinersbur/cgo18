#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

#import git
import argparse
import os
import subprocess
import shlex
import tempfile
import sys
import copy
import shutil
import re
import time
import stat
import weakref
#import pygit2
import platform
import datetime
import threading
from distutils.util import strtobool
import multiprocessing
import io
import importlib
import queue
import contextlib

script = os.path.abspath(sys.argv[0])
thisscript = __file__
homedir = os.path.expanduser('~')


def shsplit(str):
    return shlex.split(str)

def shlist(list):
    return ' '.join([shlex.quote(l) for l in list])

def shquote(args):
    return ' '.join([shlex.quote(str(arg)) for arg in args])

def shjoin(args):
    return ' '.join([shlex.quote(str(arg)) for arg in args])




print_commands = True
print_commands_baseonly = False

def print_command(cmd,*args,cwd=None,addenv=None,appendenv=None,force=False,prefix='$ '):
    if print_commands or force:
        shortcmd = os.path.basename(cmd) if print_commands_baseonly else shlex.quote(cmd)
        setenvs = []
        if addenv is not None:
            for envkey,envval in addenv.items():
                setenvs += [envkey + '=' + shlex.quote(envval)]
        if appendenv is not None:
            for envkey,envval in appendenv.items():
                if not envval:
                    continue
                setenvs += [envkey + '=${' + envkey + '}:' + shlex.quote(envval)]
        setenv = ''
        for elt in setenvs:
            setenv += elt + ' '
        if cwd is None:
            print(prefix + setenv + shortcmd + ' ' + shquote(args),file=sys.stderr)
        else:
            print(prefix + '(cd ' + shlex.quote(cwd) + ' && ' + setenv + shortcmd + ' ' + shquote(args) + ')',file=sys.stderr)


def assemble_env(addenv=None,appendenv=None):
    env = None
    if addenv is not None or appendenv is not None:
        env = dict(os.environ)
    if addenv is not None:
        for key,val in addenv.items():
            env[str(key)] = str(val)
    if appendenv is not None:
        for key,val in appendenv.items():
            if not val:
                continue
            oldval = env.get(key)
            if oldval:
                env[key] = oldval + ':' + val
            else:
                env[key] = val
    return env


def invoke(cmd, *args,cwd=None,addenv=None,appendenv=None,showonly=False,stdout=None,stderr=None,resumeonerror=False,stdin=None,return_stdout=False,return_stderr=False,print_stdout=None,print_stderr=None):
    print_command(cmd, *args,cwd=cwd,addenv=addenv,appendenv=appendenv)
    if showonly:
        return
    env = assemble_env(addenv=addenv,appendenv=appendenv)

    stdoutthread = False
    stderrthread = False
    popenmode = False

    stdouthandles = []
    stderrhandles = []

    handlestoclose = []

    if isinstance(stdout, str):
        stdout = [stdout]
    if isinstance(stdout, list):
        for file in stdout:
            if isinstance(file,str):
                h = open(file, 'w')
                handlestoclose.append(h)
                stdouthandles.append(h)
            else:
                stdouthandles.append(file)
    if print_stdout==True:
        stdouthandles.append(sys.stdout)

    if isinstance(stderr, str):
        stderr = [stderr]
    if isinstance(stderr, list):
        for file in stderr:
            if isinstance(file,str):
                h = open(file, 'w')
                handlestoclose.append(h)
                stderrhandles.append(h)
            else:
                stderrhandles.append(file)
    if print_stderr==True:
        stderrhandles.append(sys.stderr)

    # TODO: if only result_stdout or result_stderr are given, do not use popenmode

    result_stdout = None
    if return_stdout:
        result_stdout = io.StringIO()
        stdouthandles.append(result_stdout)
        popenmode = True

    result_stderr = None
    if return_stderr:
        result_stderr = io.StringIO()
        stderrhandles.append(result_stderr)
        popenmode = True

    if len(stdouthandles) == 1:
        stdout = stdouthandles[0]
    elif len(stdouthandles) > 1:
        stdout = subprocess.PIPE
        stdoutthread = True
        popenmode = True

    if len(stderrhandles) == 1:
        stderr = stderrhandles[0]
    elif len(stderrhandles) > 1:
        stderr = subprocess.PIPE
        stderrthread = True
        popenmode = True

    if isinstance(stdin, str):
        popenmode = True

    if stdout is not None and stdout == result_stdout:
        stdout = subprocess.PIPE

    if stderr is not None and stderr == result_stderr:
        stderr = subprocess.PIPE

    #TODO: Maybe just patternmatch known configs and use popenmode as fallback

    sys.stdout.flush()
    sys.stderr.flush()
    if popenmode:
        p = subprocess.Popen([cmd] + [str(s) for s in args],cwd=cwd,env=env,stdout=stdout,stderr=stderr,stdin=subprocess.PIPE,universal_newlines=True)

        def catch_std(out, outhandles):
            while True:
                try:
                    line = out.readline()
                except ValueError as e:
                    # TODO: Handle properly
                    print("Input prematurely closed")
                    break

                if line is None or len(line) == 0:
                    break
                for h in outhandles:
                    h.write(line)

        if stdoutthread:
            tout = threading.Thread(target=catch_std, args=(p.stdout, stdouthandles))
            tout.daemon = True
            tout.start()

        if stderrthread:
            terr = threading.Thread(target=catch_std, args=(p.stderr, stderrhandles))
            terr.daemon = True
            terr.start()

        if return_stderr or return_stdout:
            tmp_stdout,tmp_stderr = p.communicate(input=stdin)
            if tmp_stdout is not None:
                result_stdout = tmp_stdout
            if tmp_stderr is not None:
                result_stderr = tmp_stderr
        elif stdin and (stdoutthread or stderrthread):
            if isinstance(stdin,str):
                infile = open(stdin,'r')
                p.stdin.write(infile)
                close(infile)
            else:
                p.stdin.write(stdin)
        elif stdin:
            p.communicate(input=stdin)
        rtncode = p.wait()

        if stdoutthread:
            tout.join()
            p.stdout.close()

        if stderrthread:
            terr.join()
            p.stderr.close()

    else:
        rtncode = subprocess.call([cmd] + [str(s) for s in args],cwd=cwd,env=env,stdout=stdout,stderr=stderr,stdin=stdin)
    success = rtncode == 0

    for h in handlestoclose:
        h.close()

    if not resumeonerror and not success:
        exit(rtncode)

    if isinstance(result_stdout , io.StringIO):
        result_stdout = result_stdout.getvalue()
    if isinstance(result_stderr, io.StringIO):
        result_stderr = result_stderr.getvalue()

    if return_stdout or return_stderr:
        return success,rtncode,result_stdout,result_stderr
    return success,rtncode


class prepare_invoke:
    def __init__(self,cmd,*args,cwd=None,addenv=None,appendenv=None):
        self.cmd = cmd
        self.args = args
        self.cwd = cwd
        self.addenv = None
        self.appendenv = None

    def getCmdline(self,baseonly=False):
        shortcmd = os.path.basename(self.cmd) if baseonly else shlex.quote(self.cmd)
        setenvs = []
        if self.addenv is not None:
            for envkey,envval in self. addenv.items():
                setenvs += [envkey + '=' + shlex.quote(envval)]
        if self. appendenv is not None:
            for envkey,envval in self. appendenv.items():
                if not envval:
                    continue
                setenvs += [envkey + '=${' + envkey + '}:' + shlex.quote(envval)]
        setenv = ''
        for elt in setenvs:
            setenv += elt + ' '
        if self.cwd is None:
            return  setenv + shortcmd + ' ' + ' '.join([shlex.quote(str(s)) for s in args])
        else:
            return  '(cd ' + shlex.quote(cwd) + ' && ' + setenv + shortcmd + ' ' + ' '.join([shlex.quote(str(s)) for s in args]) + ')'

    def invoke(self,return_stdout=False,return_stderr=False,print_stdout=False,print_stderr=False,write_stdout=None,write_stderr=None,write_stdout_lineformat=None,write_stderr_lineformat=None):
        invoke(self.cmd, self.args, cwd=self.cwd, addenv =self.addenv,appendenv=self.appendenv)

    def write_sh(outfilenname):
        outfilenname = os.path.join(outdir,cmdname + '.sh')
        self.outfilenname = outfilenname
        with open(outfilenname, 'w+') as f:
            f.writeline('#! /bin/sh\n')
            f.writeline('\n')
            f.writeline()


def query(cmd,*args,cwd=None,addenv=None,appendenv=None):
    print_command(cmd, *args,cwd=cwd,addenv=addenv,appendenv=appendenv)
    env = assemble_env(addenv=addenv,appendenv=appendenv)
    sys.stderr.flush()
    return subprocess.check_output([cmd] + [str(s) for s in args],cwd=cwd,env=env,universal_newlines=True)


def invoke_git(*args, **kwargs):
    invoke('git', *args, **kwargs)


def query_git(*args,addenv=None, **kwargs):
    myenv = dict() if addenv is None else copy(addenv)
    myenv['LC_ALL'] = 'C'
    #myenv['LANG'] = 'C'
    #myenv['LANGUAGE'] = 'C'
    return query('git', *args,addenv=myenv, **kwargs)



def write_string_to_file(filename, data):
    with open(filename, 'w') as file:
        file.write(data)


def read_string_from_file(filename):
    with open(filename,'r') as file:
        return file.read()

def ltrim_emptylines(lines,meta=None):
    while len(lines) and (not lines[0] or lines[0].isspace()):
        del lines[0]
        if meta is not None:
            del meta[0]


def rtrim_emptylines(lines):
    while len(lines) and (not lines[-1] or lines[-1].isspace()):
        del lines[-1]

def trim_emptylines(lines):
    ltrim_emptylines(lines)
    rtrim_emptylines(lines)

removecommentlines = re.compile(r'\n[ \t]*\#.*', re.MULTILINE)


class Treeish:
    def __init__(self,rep,treeish):
        self.rep = rep
        self.treeish = treeish


class Commit:
    @staticmethod
    def from_sha1(sha1):
        return Commit(None,sha1)

    def __init__(self,rep,sha1):
        self.rep = rep
        assert(str(sha1).strip() == str(sha1))
        self.sha1 = sha1

    def __str__(self):
        return str(self.sha1)
    def __repr__(self):
        return '<{cls} "{sha1}">'.format(cls=self.__class__.__name__, sha1=str(self))

    def __eq__(self, other):
        if not hasattr(other, 'sha1'):
            return False
        return self.sha1 == other.sha1
    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def is_branch(self):
        return False

    def as_commit(self):
        return self

    def predecessor(self,count=None):
        if count is None:
            return self.rep.rev_parse(self.sha1 + '^')
        assert(count >= 0)
        return self.rep.rev_parse(self.sha1 + '~' + str(count))

    def successor(self, descendant=None):
        if descendant is None:
            descendant = self.rep.workdir_commit()
        descendant = descendant.as_commit()
        # Traverse backwards to find commit in history and return one before
        # encountering it
        # TODO: Multiple predecessors
        successor = None
        cur = descendant
        while True:
            if self == cur:
                return successor
            successor = cur
            cur = cur.predecessor() #TODO: Handle case when self is not in descendant's ancestor chain

    def get_sha1(self):
        return self.sha1

    def get_short(self):
        return self.sha1[0:6]

    def get_message(self,title=False,body=False):
        opts = []

        if title and body:
            opts.append('--pretty=format:%s%n%+b')
        if title and not body:
            opts.append('--pretty=format:%s')
        if not title and body:
            opts.append('--pretty=format:%b')

        result = self.rep.query_git('log', self.sha1, '-n1', *opts)
        return result

    def __eq__(self, other):
        # Note that this does not compare rep!
        return self.sha1 == other.sha1

    def __ne__(self, other):
        return self.sha1 != other.sha1


# Local branch
class Branch:
    def __init__(self,rep,name):
        self.rep = rep
        self.name = name

    def __str__(self):
        return str(self.name)
    def __repr__(self):
        return '<{cls} "{treeish}">'.format(cls=self.__class__.__name__, treeish=str(self))

    def __eq__(self, other):
        return self.rep == other.rep and self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def is_branch(self):
        return True

    def is_local(self):
        return self.name.rfind('/') < 0

    def as_commit(self):
        return self.rep.rev_parse(str(self))

    def remove(self,resumeonerror=False):
        self.rep.invoke_git('branch', '-D', self.name, resumeonerror=resumeonerror)

    def get_head(self):
        return self.rep.get_commit(self.name)

    def get_name(self):
        return self.name

    def get_basename(self):
        last = self.name.rfind('/')
        if last < 0:
            return self.name
        return self.name[last + 1:]

    def exists(self):
        result = self.rep.branches(all=True, pattern=self.name)
        assert(len(result) <= 1)
        return len(result) == 1

    def push_to(self, remote, force=None):
        Remote(self.rep, remote).push(self, force=True)


class Remote:
    def __init__(self,rep,name):
        self.rep = rep
        self.name = name

    def __str__(self):
        return str(self.name)
    def __repr__(self):
        return '<{cls} "{name}">'.format(cls=self.__class__.__name__, name=str(self))

    def __eq__(self, other):
        return self.rep == other.rep and self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)

    def fetch(self, refspec=None, prune=False, resumeonerror=False):
        opts = []
        if prune:
            opts += ['--prune']
        if refspec is not None:
            if hasattr(refspec, '__iter__'):
                for spec in refspec:
                    opts += [str(spec)]
            else:
                opts += [str(refspec)]
        self.rep.invoke_git('fetch', self.name, *opts, resumeonerror=resumeonerror)

    def set_url(self,url):
        self.rep.invoke_git('remote','set-url',self.name,url)

    def branches(self):
        return self.rep.branches(remote_only=True, pattern=self.name + '/*')

    def get_branch(self, branchname):
        return Branch(self.rep, self.name + '/' + branchname)

    def push(self,branch,force=None):
        opts = []
        if force:
            opts.append('--force')
        self.rep.invoke_git('push', self, branch, *opts)



class Repository2:
    @classmethod
    def from_directory(cls, workdir):
        #workdir = pygit2.discover_repository(workdir)
        gitdir = os.path.join(workdir, '.git')
        assert os.path.exists(gitdir)
        return cls(gitdir, workdir)

    @classmethod
    def init(cls, workingdir):
        invoke_git('init', workingdir)
        return cls.from_directory(workingdir)

    def __init__(self, gitdir, workdir):
        #self.repo = pygit2.Repository(workdir)
        self.gitdir = gitdir
        self.workdir = workdir
        self.svn = Repository2.SVN(self)

    def __str__(self):
        return str(self.workdir)
    def __repr__(self):
        if os.path.join(self.workdir,'.git') == self.gitdir:
            formatstr = '<{cls} "{workdir}">'
        else:
            formatstr = '<{cls} "{workdir}" ({gitdir})>'
        return formatstr.format(cls=self.__class__.__name__, workdir=self.workdir, gitdir=self.gitdir)

    def __eq__(self, other):
        return self.gitdir == other.gitdir
    def __ne__(self, other):
        return not self.__eq__(other)

    def invoke_git(self,*args,**kwargs):
        # Some git command (e.g.  submodule) do not support --git-dir,
        # --work-dir
        #gitargs = ['--git-dir', self.gitdir, '--work-tree', self.workdir] +
        #list(args)
        #invoke_git(*gitargs,**kwargs)
        #assert os.path.join( self.workdir
        invoke_git(*args,cwd=self.workdir, **kwargs)

    def query_git(self,*args,**kwargs):
        #gitargs = ['--git-dir', self.gitdir, '--work-tree', self.workdir] +
        #list(args)
        return query_git(*args,cwd=self.workdir,**kwargs)
        #myenv = dict() if addenv is None else copy(addend)
        #myenv['LC_ALL'] = 'C'
        #return query('git', *args, addenv=myenv, **kwargs)

    def rev_parse(self, commitish):
        sha1 = self.query_git('rev-parse', '--verify', commitish + '^{commit}')
        return Commit(self,sha1.rstrip())

    class SVN():
        def __init__(self,parent):
            self.parent = parent

        def query_git_svn(self,*args,**kwargs):
            # git svn doesn't support --work-tree or --git-dir
            return self.parent.query_git('svn',*args,**kwargs)

        def find_rev(self,commit,after=False,before=False):
            opts = []
            if after:
                opts.append('--after')
            if before:
                opts.append('--before')
            result = self.query_git_svn('find-rev', commit, *opts)
            result = result.strip()
            if result:
                return int(result)
            return None

        def find_commit(self, revision, before=False, after=False, head=None):
            if isinstance(revision, int):
                revision = 'r{rev}'.format(rev=revision)
            opts = []
            if before:
                opts.append('--before')
            if after:
                opts.append('--after')
            if head is not None:
                opts.append(head)
            result = self.query_git_svn('find-rev', revision, *opts)
            if not result.strip():
                raise Exception("No revision found")
            result = result.rstrip().splitlines()[-1].strip()
            if result:
                return Commit(self.parent,result)
            return None

    def find_commit(self,revision,before=True, after=False):
        if isinstance(revision, int):
            return self.svn.find_commit(revision,before=before,after=after)
        return self.get_commit(revision)

    def workdir_branch(self):
        HEADfilename = os.path.join(self.gitdir,'HEAD')
        HEADstr = read_string_from_file(HEADfilename).rstrip()
        if HEADstr.startswith(r'ref: '):
            assert HEADstr.startswith('ref: refs/heads/') # Some other symbolic reference than a branch ?
            return Branch(self,HEADstr[16:])
        else:
            # Detached HEAD
            return Commit(self,HEADstr)

    def workdir_commit(self):
        return self.rev_parse('HEAD')

    def is_detached(self):
        return not self.workdir_branch().is_branch

    def create_remote(self, name, url, fetch=False, resumeonerror=False):
        opts = []
        if fetch:
            opts += ['-f']
        self.invoke_git('remote', 'add', name, url, *opts,resumeonerror=resumeonerror)
        return Remote(self,name)

    def create_branch(self,  name,commit=None,force=False):
        opts = []
        if commit is not None:
            opts.append(commit)
        if force:
            opts.append('--force')
        self.invoke_git('branch',name,*opts)
        return Branch(self,name)

    def get_branch(self,branchname):
        if isinstance(branchname,Branch):
            return branchname
        return Branch(self,branchname)

    def get_remote(self,remotename):
        if isinstance(remotename,Remote):
            return remotename
        return Remote(self,remotename)



    def branch_create(self, branchname):
        self.invoke_git('branch', branchname)
        return Branch(self,branchname)

    def branches(self,all=False,remote_only=False,pattern=None,patterns=[]):
        opts = []
        if all:
            opts.append('-a')
        if remote_only:
            opts.append('-r')
        if pattern is not None:
            opts.append(pattern)
        opts += patterns
        result = self.query_git('branch', '--list', *opts)
        branches = []
        for branchname in result.splitlines():
            m = re.match(r'\s*\*?\s*(?P<branchpath>\S+)', branchname)
            if not m:
                continue
            branchname = m.group('branchpath')
            if all and branchname.startswith('remotes/'):
                branchname = branchname[8:]
            branches.append(Branch(self,branchname))
        return branches

    def has_branch(self, branchname):
        return Branch(self,branchname).exists()

    def remotes(self):
        result = self.query_git('remote', 'show')
        remotes = []
        for remotename in result.splitlines():
            remotes.append(Remote(self,remotename))
        return remotes

    def clone_to(self, destdir):
        invoke_git('clone', self.gitdir, destdir)

    def commit(self, message, edit=False,cleanup=None,allow_empty=False,resumeonerror=None):
        args = []
        if message is not None:
            args += ['-m', message]
        if edit:
            args.append('--edit')
        if cleanup is not None:
            args.append('--cleanup=' + cleanup) # Commit message normalization: strip,whitespace,verbatim,scissors,default
        if allow_empty:
            args.append('--allow-empty')
        self.invoke_git('commit', *args,resumeonerror=resumeonerror)
        return self.workdir_commit()

    def copy_to(self, targetworkdir):
        # Assuming .git is a subdirectory
        shutil.copytree(self.workdir, targetworkdir)
        return self.from_directory(targetworkdir)

    def get_head(self):
        return self.get_commit('HEAD')

    def get_commit(self, rev):
        if isinstance(rev,Commit):
            if rev.rep == self:
                return rev
        sha1 = self.query_git('rev-parse', rev).rstrip()
        return Commit(self,sha1)

    def add(self,*args,all=None,update=False,force=False):
        opts = []
        if all:
            opts.append('-A')
        if update:
            opts.append('--update')
        if force:
            opts.append('--force')
        opts += args
        self.invoke_git('add',  *opts)

    def add_all(self,force=None):
        opts = []
        if force:
            opts.append('--force')
        self.invoke_git('add',  '-A', *opts)

    def add_update(self):
        self.invoke_git('add',  '--update')

    def checkout(self, commit=None, detach=False,force=False,branch=None,overwritebranch=None):
        opts = []
        if detach:
            opts.append('--detach')
        if force:
            opts.append('--force')
        if commit is not None:
            opts.append(commit)
        if branch is not None:
            opts += ['-b', str(branch)]
        if overwritebranch is not None:
            opts += ['-B', str(overwritebranch)]
        self.invoke_git('checkout', *opts)

    def gc(self,resumeonerror=False):
        self.invoke_git('gc', resumeonerror=resumeonerror)

    def detach(self):
        self.checkout(commit=None,detach=True)

    def reset(self,commit=None,index=None,workdir=None):
        opts = []
        if index and workdir:
            opts.append('--hard')
        elif not index and not workdir:
            opts.append('--soft')
        elif index and not workdir:
            opts.append('--mixed')
        else:
            raise Exception("No mode resets the workdir but not the index")
        if commit is not None:
            opts.append(commit)
        self.invoke_git('reset', *opts)

    def clean(self,force=False,x=False,d=False):
        opts = []
        if force:
            opts.append('--force')
        if x:
            opts.append('-x')
        if d:
            opts.append('-d')
        self.invoke_git('clean', *opts)

    def format_patch(self,revlist,reroll_count=None,signoff=False,output_directory=None):
        opts = []
        if reroll_count is not None:
            opts.append('--reroll-count=' + str(reroll_count))
        if signoff:
            opts.append('--signoff')
        if output_directory is not None:
            opts.append('--output-directory')
            opts.append(output_directory)
        opts.append(revlist)
        self.invoke_git('format-patch','-M',*opts)

    def send_email(self, files,dry_run=False,confirm=None,fromaddr=None,toaddr=None,smtp_encryption=None,smtp_server=None,smtp_server_port=None,smtp_user=None):
        opts = []
        if dry_run:
            opts.append('--dry-run')
        if confirm is not None:
            opts.append('--confirm=' + confirm)
        if fromaddr is not None:
            opts.append('--from=' + fromaddr)
        if toaddr is not None:
            opts.append('--to=' + toaddr)
        if smtp_encryption is not None:
            opts.append('--smtp-encryption=' + smtp_encryption)
        if smtp_server is not None:
            opts.append('--smtp-server=' + smtp_server)
        if smtp_server_port is not None:
            opts.append('--smtp-server-port=' + str(smtp_server_port))
        if smtp_user is not None:
            opts.append('--smtp-user=' + smtp_user)
        opts += files
        self.invoke_git('send-email', '--no-format-patch',*opts)

    def diff(self,src,dst=None):
        if dst:
            return  self.query_git('diff', src,dst)
        else:
            return self.query_git('diff', src)

    def describe(self,commit='HEAD',all=False):
        opts = []
        if all:
            opts.append('--all')
        result = self.query_git('describe',commit,*opts)
        if result:
            return result.strip()
        return None

    def merge(self,branch,noedit=None,strategy=None, nocommit=None):
        opts = []
        if noedit:
            opts.append('--no-edit')
        if strategy is not None:
            opts.append('--strategy=' + str(strategy))
        if nocommit:
            opts.append('--no-commit')
        self.invoke_git('merge',branch,*opts)

    def walk(self,commit='HEAD',order=None):
        opts = []
        if order == 'date':
            opts.append('--date-order')
        list = self.query_git('log', '--format=oneline', *opts).splitlines()
        return (Commit(self,line[:40]) for line in list if len(line.strip()) >= 1)


    def workdir_is_clean(self,ignored_files=False,untracked_files=None):
        opts = []
        if ignored_files:
            opts.append('--ignored')
        if untracked_files is None:
            pass
        elif isinstance(untracked_files, str):
            opts.append('--untracked-files=' + untracked_files)
        elif untracked_files:
            opts.append('--untracked-files=all')
        else:
            opts.append('--untracked-files=no')

        result = self.query_git('status', '--porcelain', *opts)
        return not result.strip()


    def workdir_something_to_commit(self):
        # self.query_git('commit', '--dry-run', '--porcelain')
        return not self.workdir_is_clean(ignored_files=False,untracked_files=False)


    def edit(self,commit,message):
        self.invoke_git('clean', '-df') # Remove uncommitted files; "git add -A" would add them
        self.checkout(commit,force=True,detach=True)
        assert self.workdir_is_clean(untracked_files=True)
        # Do local changes persist if not in conflict?  If yes, also reset
        write_string_to_file(os.path.join(self.workdir, '.commitmsg'), message)
        assert self.is_detached()


    def commit_edit(self):
        commitmsgfile = os.path.join(self.workdir, '.commitmsg')
        if os.path.isfile(commitmsgfile):
            commitmsg = read_string_from_file(commitmsgfile)
            commitmsg = re.sub(removecommentlines, "", commitmsg) # TODO: git commit has -cleanup=strip option
            commitmsg = commitmsg.rstrip()
            os.remove(commitmsgfile)
        self.invoke_git('add', '-A')
        if self. workdir_something_to_commit(): # Do not create empty commits
            return self.commit(message=commitmsg)
        return self.workdir_commit()


    def transfer(self,commit):
        remoterep = commit.rep
        if commit.rep == self or remoterep.workdir == self.workdir:
            return commit # Commit already exists in repo
        branch = remoterep.create_branch('_gittool',commit,force=True)
        #remote = self.create_remote('_gittool',url=remoterep.workdir)
        try:
            FETCH_HEADfilename = os.path.join(self.gitdir,'FETCH_HEAD')
            if os.path.exists(FETCH_HEADfilename):
                os.remove(FETCH_HEADfilename)

            #remote.fetch() # TODO: Only fetch _gittool branch
            self.invoke_git('fetch', remoterep.gitdir, '_gittool')
            FETCH_HEAD = read_string_from_file(FETCH_HEADfilename)
            result = Commit(self,FETCH_HEAD.split('\t')[0])
            #result = self.commit('_gittool/_gittool')
            assert result == commit # Same sha1
        finally:
            #remoterep.delete_head(branch)
            branch.remove() # TODO: Do later, otherwise FETCH_HEAD might be gcollected (practically no
                            # problem because there is the reflog)
            #self.repo.delete_remote(remote)
        return result

    def __enter__(self):
        self.restore_branch = self.workdir_branch()
        # TODO: Record branch commits

    def __exit__(self, exc_type, exc_value, traceback):
        if self.restore_branch is None:
            return # temporary; Will be deleted anyway

        successful = exc_type is None
        if successful:
            return

        # Rollback
        self.reset(self.restore_branch,index=True, workdir=True)
        self.restore_branch = None

    class State:
        def __init__(self):
            self.HEADcommit = None
            self.HEADbranch = None
            self.INDEXcommit = None
            self.UNCOMMITTEDcommit = None
            self.UNADDEDcommit = None
            self.IGNOREDcommit = None
            self.branches = dict() # branch => sha1

    def makeState(self):
        state = Repository2.State()

        state.HEADbranch = self.workdir_branch()
        state.HEADcommit = self.get_head()
        #self.detach()

        self.commit("index",resumeonerror=True)
        state.INDEXcommit = self.get_head()

        self.add(update=True)
        self.commit("uncommitted",resumeonerror=True)
        state.UNCOMMITTEDcommit = self.get_head()

        self.add(all=True)
        self.commit("unadded",resumeonerror=True)
        state.UNADDEDcommit = self.get_head()

        self.add(all=True,force=True)
        self.commit("ignored",resumeonerror=True)
        state.IGNOREDcommit = self.get_head()

        #self.checkout(state.HEADbranch)
        #self.reset(state.UNADDEDcommit,index=True,workdir=False)
        if state.INDEXcommit != state.IGNOREDcommit:
            self.reset(state.INDEXcommit,index=True,workdir=False)
        if state.HEADcommit != state.INDEXcommit:
            self.reset(state.HEADcommit,index=False,workdir=False)

        #TODO: Branches
        return state


    def setState(self, state):
        # Get to pristine HEAD and branch
        self.checkout(state.HEADbranch)
        self.clean(force=True,d=True,x=True)

        # Get all ignored,unadded,uncommitted and cached files
        if state.HEADcommit != state.IGNOREDcommit:
            self.reset(state.IGNOREDcommit,index=True,workdir=True)

        # Remove ignored and unadded from any tracking
        if state.INDEXcommit != state.IGNOREDcommit:
            self.reset(state.INDEXcommit,index=True,workdir=False)

        # Get back to HEAD, leaving files cached
        if state.HEADcommit != state.INDEXcommit:
            self.reset(state.HEADcommit,index=False,workdir=False)

        #TODO: Branches


    class PreserveState:
        def __init__(self, rep):
            self.rep = rep

        def __enter__(self):
            self.state = self.rep.makeState()
            return self.state

        def __exit__(self,type, value, traceback):
            self.rep.setState(self.state)

    def preserve(self):
        return Repository2.PreserveState(self)







def gittool_dirdiff(tmpdir, rep, commit):
    diffrep = rep.copy_to(os.path.join(tmpdir, 'Reference'))
    diffrep.checkout(commit, detach=True,force=True)
    invoke('meld', diffrep.workdir, rep.workdir)


def gittool_split(rep, left,right, tmpdir, commit):
    HEAD = rep.workdir_branch()
    HEADcommit = HEAD.as_commit()

    with rep:
        # TODO: If both are temporary, we can clone them instead of copying;
        # should be faster
        if not left:
            left = rep.copy_to(os.path.join(tmpdir, 'Left'))
        if not right:
            right = rep.copy_to(os.path.join(tmpdir, 'Right'))

        predecessor = commit.predecessor()
        successor = commit.successor(descendant=HEAD)

        oldmessage = commit.get_message(title=True,body=True)
        right.edit(commit, message=oldmessage + "\n# Rightside")
        left.edit(predecessor, message=oldmessage + "\n# Leftside")

        invoke('meld', left.workdir, right.workdir)

        cur = leftcommit = left.commit_edit()

        cur = right.transfer(leftcommit)
        right.invoke_git('update-ref', 'HEAD', leftcommit)
        cur = rightcommit = right.commit_edit()

        cur = rep.transfer(rightcommit)
        rep.checkout(cur, detach=True, force=True)
        if successor:
            rep.invoke_git('rebase', commit, HEADcommit, '--onto', rightcommit)
            cur = rep.workdir_commit()
        if HEAD.is_branch:
            rep.invoke_git('checkout', '-B', HEAD)


class ProjectRemote:
    def __init__(self,name,url,mainbranch='master',svn=None):
        self.name = name
        self.url = url
        self.mainbranch = mainbranch
        self.svn = svn


projects = dict()
class Project:
    def __init__(self, name):
        self.remotes = []
        self.subprojects = []
        self.name = name
        global projects
        projects[self.name] = self

    def __str__(self):
        return str(self.name)
    def __repr__(self):
        return '<{cls} "{name}">'.format(cls=self.__class__.__name__, treeish=name(self))

    def remote(self,*args,**kwargs):
        remote = ProjectRemote(*args,**kwargs)
        self.remotes.append(remote)
        return remote

    def submodule(self, subproject, subdir=None, checkout=True):
        if subdir is None:
            subdir = subproject.name
        self.subprojects.append((subproject,subdir.split('/'),True,checkout))

    def subproject(self, subproject, subdir=None, checkout=True):
        if subdir is None:
            subdir = subproject.name
        self.subprojects.append((subproject,subdir.split('/'),False,checkout))

    @property
    def mainremote(self):
        return self.remotes[0]

    @property
    def workdir(self):
        return os.path.join(os.path.expanduser('~'), 'src', self.name)





gittool = Project('gittool')
#gittool.remote('github', 'git@github.com:Meinersbur/gittool.git')
gittool.remote('meinersbur', 'git@meinersbur.de:gittool.git')

llvm_project = Project('llvm-project')
llvm_project.remote('chapuni', 'https://github.com/llvm-project/llvm-project.git')

llvm = Project('llvm')
llvm.remote('official', 'http://llvm.org/git/llvm.git', svn='https://llvm.org/svn/llvm-project/llvm/trunk')
llvm.remote('github-mirror', 'https://github.com/llvm-mirror/llvm.git')
llvm.remote('meinersbur', 'git@meinersbur.de:llvm.git')

polly = Project('polly')
polly.remote('official', 'http://llvm.org/git/polly.git', svn='https://llvm.org/svn/llvm-project/polly/trunk')
polly.remote('github-mirror', 'https://github.com/llvm-mirror/polly.git')
polly.remote('github', 'git@github.com:Meinersbur/polly.git')
polly.remote('meinersbur', 'git@meinersbur.de:polly.git')
polly.remote('execjobs', 'git@meinersbur.de:execjobs.git')
polly.remote('tobig', 'git@github.com:tobig/polly.git')
llvm.subproject(polly, 'tools/polly')

clang = Project('clang')
clang.remote('official', 'http://llvm.org/git/clang.git', svn='https://llvm.org/svn/llvm-project/cfe/trunk')
clang.remote('github-mirror', 'https://github.com/llvm-mirror/clang.git')
clang.remote('meinersbur', 'git@meinersbur.de:clang.git')
llvm.subproject(clang, 'tools/clang')

lnt = Project('lnt')
lnt.remote('official', 'http://llvm.org/git/lnt.git', svn='https://llvm.org/svn/llvm-project/lnt/trunk')
lnt.remote('github-mirror', 'https://github.com/llvm-mirror/lnt.git')
lnt.remote('meinersbur', 'git@meinersbur.de:lnt.git')
llvm.subproject(lnt, 'projects/lnt', checkout=False)

test_suite = Project('test-suite')
test_suite.remote('official', 'http://llvm.org/git/test-suite.git', svn='https://llvm.org/svn/llvm-project/test-suite/trunk')
test_suite.remote('github-mirror', 'https://github.com/llvm-mirror/test-suite.git')
test_suite.remote('github', 'git@github.com:Meinersbur/test-suite.git')
test_suite.remote('meinersbur', 'git@meinersbur.de:test-suite.git')
llvm.subproject(test_suite, 'projects/test-suite', checkout=False)

clang_tools_extra = Project('extra')
clang_tools_extra.remote('official', 'http://llvm.org/git/clang-tools-extra.git')
clang_tools_extra.remote('github-mirror', 'https://github.com/llvm-mirror/clang-tools-extra.git')
clang_tools_extra.remote('meinersbur', 'git@meinersbur.de:clang-tools-extra.git')
clang.subproject(clang_tools_extra, 'tools/extra', checkout=False)

compiler_rt = Project('compiler-rt')
compiler_rt.remote('official', 'http://llvm.org/git/compiler-rt.git', svn='https://llvm.org/svn/llvm-project/compiler-rt/trunk')
compiler_rt.remote('github-mirror', 'https://github.com/llvm-mirror/compiler-rt.git')
compiler_rt.remote('meinersbur', 'git@meinersbur.de:compiler-rt.git')
llvm.subproject(compiler_rt, 'projects/compiler-rt', checkout=False)

lld = Project('lld')
lld.remote('official', 'http://llvm.org/git/lld.git', svn='https://llvm.org/svn/llvm-project/lld/trunk')
lld.remote('github-mirror', 'https://github.com/llvm-mirror/lld.git')
lld.remote('meinersbur', 'git@meinersbur.de:lld.git')
llvm.subproject(lld, 'tools/lld', checkout=False)

lldb = Project('lldb')
lldb.remote('official', 'http://llvm.org/git/lldb.git', svn='https://llvm.org/svn/llvm-project/lldb/trunk')
lldb.remote('github-mirror', 'https://github.com/llvm-mirror/lldb.git')
lldb.remote('meinersbur', 'git@meinersbur.de:lldb.git')
llvm.subproject(lldb, 'tools/lldb', checkout=False)

libcxxabi = Project('libcxxabi')
libcxxabi.remote('official', 'http://llvm.org/git/libcxxabi.git', svn='https://llvm.org/svn/llvm-project/libcxxabi/trunk')
libcxxabi.remote('github-mirror', 'https://github.com/llvm-mirror/libcxxabi.git')
libcxxabi.remote('meinersbur', 'git@meinersbur.de:libcxxabi.git')
llvm.subproject(libcxxabi, 'projects/libcxxabi')

libcxx = Project('libcxx')
libcxx.remote('official', 'http://llvm.org/git/libcxx.git', svn='https://llvm.org/svn/llvm-project/libcxx/trunk')
libcxx.remote('github-mirror', 'https://github.com/llvm-mirror/libcxx.git')
libcxx.remote('meinersbur', 'git@meinersbur.de:libcxx.git')
llvm.subproject(libcxx, 'projects/libcxx')

openmp = Project('openmp')
openmp.remote('official', 'http://llvm.org/git/openmp.git', svn='https://llvm.org/svn/llvm-project/openmp/trunk')
openmp.remote('github-mirror', 'https://github.com/llvm-mirror/openmp.git')
openmp.remote('meinersbur', 'git@meinersbur.de:openmp.git')
llvm.subproject(openmp, 'projects/openmp', checkout=False)

debuginfo_tests = Project('debuginfo-tests')
debuginfo_tests.remote('official', 'http://llvm.org/git/debuginfo-tests.git', svn='https://llvm.org/svn/llvm-project/debuginfo-tests/trunk')
debuginfo_tests.remote('meinersbur', 'git@meinersbur.de:debuginfo-tests.git')
clang.subproject(debuginfo_tests, 'test/debuginfo-tests', checkout=False)

zorg = Project('zorg')
zorg.remote('official', 'http://llvm.org/git/zorg.git', svn='https://llvm.org/svn/llvm-project/zorg/trunk')
zorg.remote('github-mirror', 'https://github.com/llvm-mirror/zorg.git')
zorg.remote('meinersbur', 'git@meinersbur.de:zorg.git')
llvm.subproject(zorg, 'projects/zorg', checkout=False)

libunwind = Project('projects/libunwind')
libunwind.remote('official', 'git://git.sv.gnu.org/libunwind.git') # svn='https://llvm.org/svn/llvm-project/libunwind/trunk' (has no git-svn
                                                                   # associated with it)
libunwind.remote('github-mirror', 'https://github.com/llvm-mirror/libunwind.git')
libunwind.remote('meinersbur', 'git@meinersbur.de:libunwind.git')
# Contains directory 'aux', invalid name on Windows
#llvm.subproject(libunwind, 'projects/libunwind')

libclc = Project('libclc')
libclc.remote('official', 'http://llvm.org/git/libclc.git', svn='http://llvm.org/svn/llvm-project/libclc/trunk')
libclc.remote('github-mirror', 'https://github.com/llvm-mirror/libclc.git')
libclc.remote('meinersbur', 'git@meinersbur.de:libclc.git')
llvm.subproject(libclc, 'projects/libclc', checkout=False)







# Still missing:
# - llgo
# - vmkit (No CMakeLists.txt; abandoned)
# - Klee
# - Dragonegg (abandoned?)
# - Poolalloc
imath = Project('imath')
imath.remote('official', 'git@github.com:creachadair/imath.git')

isl = Project('isl')
isl.remote('github', 'git@github.com:Meinersbur/isl.git')
isl.remote('official', 'git://repo.or.cz/isl.git')
isl.remote('meinersbur', 'git@meinersbur.de:isl.git')
isl.remote('gforge', 'git+ssh://kruse@scm.gforge.inria.fr//gitroot/ppcg/isl.git')
isl.remote('tobig', 'git@github.com:tobig/isl.git')
isl.submodule(imath)

pet = Project('pet')
pet.remote('github', 'git@github.com:Meinersbur/pet.git')
pet.remote('official', 'git://repo.or.cz/pet.git')
pet.remote('meinersbur', 'git@meinersbur.de:pet.git')
pet.remote('gforge', 'git+ssh://kruse@scm.gforge.inria.fr//gitroot/ppcg/pet.git')
pet.submodule(isl)

ppcg = Project('ppcg')
ppcg.remote('github', 'git@github.com:Meinersbur/ppcg.git')
ppcg.remote('official', 'git://repo.or.cz/ppcg.git')
ppcg.remote('meinersbur', 'git@meinersbur.de:ppcg.git')
ppcg.remote('gforge', 'git+ssh://kruse@scm.gforge.inria.fr//gitroot/ppcg/ppcg.git')
ppcg.submodule(isl)
ppcg.submodule(pet)

prl = Project('prl')
prl.remote('github', 'git@github.com:Meinersbur/prl.git', mainbranch='pencilcc')
prl.remote('meinersbur', 'git@meinersbur.de:prl.git', mainbranch='pencilcc')

pencil_headers = Project('pencil-headers')
pencil_headers.remote('pencil-headers', 'git@github.com:pencil-language/pencil-headers.git')

pencilcc = Project('pencilcc')
pencilcc.remote('github', 'git@github.com:Meinersbur/pencilcc.git', mainbranch='pencilcc')
pencilcc.remote('pencil-driver', 'git@github.com:Meinersbur/pencil-driver.git')
pencilcc.submodule(ppcg)
pencilcc.submodule(prl)
pencilcc.submodule(pencil_headers)


execjobs = Project('execjobs')
execjobs.remote('meinersbur', 'git@meinersbur.de:execjobs.git')

execresults = Project('execresults')
execresults.remote('_wsl', '/root/execslave/work')
execresults.remote('_ficus', 'ficus:execslave/work')
#execresults.remote('_courge', 'fermi:execslave-courge/work')
execresults.remote('_pauli', 'pauli:execslave/work')
execresults.remote('fdcserver', 'git@meinersbur.de:execresults-fdcserver.git')
execresults.remote('wsl', 'git@meinersbur.de:execresults-wsl.git')
execresults.remote('arachide', 'git@meinersbur.de:execresults-arachide.git')
#execresults.remote('courge', 'git@meinersbur.de:execresults-courge.git')
execresults.remote('ficus', 'git@meinersbur.de:execresults-ficus.git')
execresults.remote('meinersbur', 'git@meinersbur.de:execresults.git')
execresults.remote('pauli', 'git@meinersbur.de:execresults-pauli.git')
execresults.remote('greina', 'git@meinersbur.de:execresults-greina.git')
#execresults.remote('greina8', 'git@meinersbur.de:execresults-greina8.git')
execresults.remote('leone', 'git@meinersbur.de:execresults-leone.git')
#execresults.remote('daint', 'git@meinersbur.de:execresults-daint.git')


class NamedSentinel:
    def __init__(self,name):
        self.name = name
    def __repr__(self):
        return self.name

REVISION = object()
REV_KEEP = NamedSentinel('REV_KEEP')
REV_HEAD = NamedSentinel('REV_HEAD')
REV_MERGE_HEAD = NamedSentinel('REV_MERGE_HEAD')
REV_DELETE = NamedSentinel('REV_DELETE')

def checkout_sub(project,parentdir,subdir,ismodule,parentrep=None,onlychildren=None,checkout=True,unlisted=REV_HEAD,ignore_fetch_errors=False,enable_svn=True):
    print('### Checking out', project.name)

    revision = None
    if isinstance(onlychildren, dict) and onlychildren:
        revision = parseRev(onlychildren[REVISION] if REVISION in onlychildren else None, allow_sentinels=True,default=REV_MERGE_HEAD)
    elif onlychildren is None:
        revision = parseRev(unlisted, allow_sentinels=True,default=REV_MERGE_HEAD)
    else:
        revision = parseRev(onlychildren, allow_sentinels=True,default=REV_MERGE_HEAD)
    assert(revision is not None)

    projectdir = os.path.join(parentdir, *subdir)
    if ismodule:
        created = not os.path.exists(os.path.join(projectdir,'.git'))
        if not created and revision is REV_KEEP:
            return

        if created:
            print('## Creating submodule', projectdir)
            parentrep.invoke_git('submodule', 'init', '--', '/'.join(subdir))
            parentrep.invoke_git('submodule','update','--no-fetch','--','/'.join(subdir))
            rep = Repository2.from_directory(projectdir)
            rep.invoke_git('remote','rm', 'origin')
            rep.invoke_git('config', 'user.email', project.name + '@meinersbur.de')
            rep.invoke_git('config', 'pack.compression', 9) # Max pack compression
        else:
            print('## Merging submodule',projectdir)
            rep = Repository2.from_directory(projectdir)
    elif not os.path.exists(projectdir):
        if not checkout or revision is REV_KEEP:
            print('## Chosen not to checkout subproject', projectdir)
            return

        print('## Creating',projectdir)
        rep = Repository2.init(projectdir)
        rep.invoke_git('config', 'user.email', project.name + '@meinersbur.de')
        created = True
    else:
        print('## Merging',projectdir)
        rep = Repository2.from_directory(projectdir)
        created = False

    # Search the unique SVN remote
    svnremote = None
    for remote in project.remotes:
        if remote.svn:
            assert svnremote is None
            svnremote = remote

    # Setup git-svn config
    if svnremote and created and enable_svn:
        rep.invoke_git('svn', 'init', '--username=meinersbur', svnremote.svn)
        rep.invoke_git('config', 'svn-remote.svn.fetch', ':refs/remotes/' + svnremote.name + '/' + svnremote.mainbranch)

    # Iterate in reverse order, st.  we fetch from github-mirror first, which
    # is faster and to reduce load on official LLVM servers.
    # Note: the official 'pack' is smaller by half!
    for remote in project.remotes:
        repremote = rep.create_remote(remote.name, remote.url,resumeonerror=True)
        repremote.fetch(prune=True,resumeonerror=ignore_fetch_errors)

    # Do an initial checkout without merge such that submodules exist
    if created:
        rep.checkout(project.mainremote.name + '/' + project.mainremote.mainbranch)

    if isinstance(onlychildren, dict) or (unlisted is not REV_KEEP): # don't recurse if it's not changing anything
        for subproject,subsubdir,subismodule,subcheckout in project.subprojects:
            if onlychildren is None:
            # Checkout latest mainbranch
                subonlychildren = None
            elif isinstance(onlychildren, dict):
                if subproject.name in onlychildren:
                    subonlychildren = onlychildren[subproject.name]
                    subcheckout = True
                else:
                    continue
            else:
                # Single revision specification
                continue
            subrep = checkout_sub(subproject, projectdir, subsubdir, subismodule, rep, onlychildren=subonlychildren,checkout=subcheckout,ignore_fetch_errors=ignore_fetch_errors,enable_svn=enable_svn,unlisted=unlisted)

    # Do not accidentally update any branch
    if revision is not REV_KEEP:
        rep.invoke_git('checkout', '--detach', resumeonerror=True)
    if ismodule:
        parentrep.invoke_git('submodule', 'update', '--merge', '/'.join(subdir))


    if revision is REV_MERGE_HEAD:
        rep.invoke_git('merge', '--no-edit',  project.mainremote.name + '/' + project.mainremote.mainbranch)
        #if svnremote:
        #    rep.invoke_git('svn', 'rebase', '-l')
    elif revision is REV_HEAD:
        rep.checkout(project.mainremote.name + '/' + project.mainremote.mainbranch, detach=True)
    elif revision is REV_KEEP:
        pass
    elif revision is REV_DELETE:
        raise Exception("Must not delete after children have been processed")
    elif isinstance(revision,int):
        svnbranch = svnremote.name + '/' + svnremote.mainbranch
        commit = rep.svn.find_commit(revision, before=True, head=svnbranch)
        rep.checkout(commit, detach=True,force=True)
    else:
        rep.checkout(revision, detach=True,force=True)

    return rep



def gittool_checkout(projectstr):
    global projects
    project = projects[projectstr]
    assert(project)
    srcdir = os.path.join(os.path.expanduser('~'), 'src')
    checkout_sub(project, srcdir, [project.name], ismodule=False, unlisted=REV_MERGE_HEAD)


def pushall_sub(project,remotestr,branch,parentdir,subdir,force=None):
    print("### Pushing {project} to {remote}".format(project=project,remote=remotestr))
    projectdir = os.path.join(parentdir, *subdir)
    rep = Repository2.from_directory(projectdir)
    remote = rep.get_remote(remotestr)
    remote.push(branch,force=force)

    for subproject,subsubdir,subismodule in project.subprojects:
        pushall_sub(subproject,remotestr,branch,parentdir=projectdir,subdir=subsubdir,force=force)

def gittool_pushall(projectstr,remote,branch,force=None):
    global projects
    project = projects[projectstr]
    assert(project)
    srcdir = os.path.join(os.path.expanduser('~'), 'src')
    pushall_sub(project,remote,branch,srcdir,[project.name],force=force)


def gittool_checkoutall(rep, force=False, fullname=False):
    for remote in rep.remotes():
        for branch in remote.branches():
            newbranchname = branch.get_name() if fullname else branch.get_basename()
            rep.create_branch(newbranchname, branch, force=force)


def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


if os.name == 'nt':
    class TemporaryDirectory(object):
        """Also delete read-only files on Windows
        """

        def __init__(self, suffix="", prefix=tempfile.template, dir=None):
            self.name = tempfile.mkdtemp(suffix, prefix, dir)
            self._finalizer = weakref.finalize(self, self._cleanup, self.name,
                warn_message="Implicitly cleaning up {!r}".format(self))

        @classmethod
        def _cleanup(cls, name, warn_message):
            shutil.rmtree(name)
            warnings.warn(warn_message, ResourceWarning)

        def __repr__(self):
            return "<{} {!r}>".format(self.__class__.__name__, self.name)

        def __enter__(self):
            return self.name

        def __exit__(self, exc, value, tb):
            self.cleanup()

        def cleanup(self):
            if self._finalizer.detach():
                shutil.rmtree(self.name,onerror=remove_readonly)
else:
    TemporaryDirectory = tempfile.TemporaryDirectory


def gittool_setseq(rep, commits):
    HEAD = rep.workdir_branch()
    HEADcommit = rep.workdir_commit()

    prev = commits[0]
    for commit in commits[1:]:
        added = rep.query_git('log',  str(prev) + '..' + str(commit),  '--pretty=format:# Added commit:%n%s%n%+b', '--no-merges')
        reverted = rep.query_git('log',  str(commit) + '..' + str(prev), '--pretty=format:# Reverted commit:%nRevert: "%s"%n%+b', '--no-merges')
        rep.checkout(commit,detach=True,force=True)
        rep.reset(prev,index=False,workdir=False)
        rep.add(all=True)
        #status = rep.query_git('status')
        #£status = '\n'.join(['# ' + s for s in status.splitlines()])
        prev = rep.commit(message=added + reverted,edit=True,cleanup='strip')
    rep.invoke_git('rebase', '--onto', prev, commits[-1], HEADcommit)
    if HEAD.is_branch:
        rep.invoke_git('checkout', '-B', HEAD.name)


def find_lastsvn(rep,commit='HEAD'):
    for commit in rep.walk(commit=commit, order='date'):
        svnrev = rep.svn.find_rev(commit.sha1)
        if svnrev:
            return Commit(rep,commit.sha1),svnrev
    return None,None


test_suite = os.path.expanduser('~/src/llvm/projects/test-suite')
unit_tests = os.path.expanduser('~/src/llvm/tools/polly/test')
failline = re.compile(r'^0.\tProgram arguments: (?P<cmd>.*)$',re.MULTILINE)
passargline = re.compile(r'^Pass Arguments:  (?P<passes>.*)$', re.MULTILINE)
reproduceline = re.compile(r'^\*\*\* You can reproduce the problem with\: opt (?P<filename>\S+) (?P<passes>.*)$', re.MULTILINE)

attachline = re.compile(r'^clang\-\d.\d\: note\: diagnostic msg\: (?P<shfilename>\/tmp\/\S+\.sh)',re.MULTILINE)
#cc1linere = re.compile(r'^\ (?P<cmdline>.*clang.*\ \-cc1\ .*)^',re.MULTILINE)


def bugpoint_reduce(bugpoint, opt, curpass, mllvm, optllfile,targetfile,tmpdir,derived):
    args = []
    args += [bugpoint]
    args += ['-opt-command=' + opt]
    args += [optllfile]
    args += ['-basicaa', '-scoped-noalias', '-tbaa', curpass]
    if mllvm:
        args += ['-opt-args']
        args += mllvm
    #args += ['-opt-args=' + ' '.join([shlex.quote(s) for s in mllvm])]
    print_command(*args)
    bpout = subprocess.check_output(args, universal_newlines=True, cwd=tmpdir)

    m = [x for x in reproduceline.finditer(bpout)][-1]
    redfilename = os.path.join(tmpdir,m.group('filename'))
    print("Bugpoint output file is", redfilename)
    disargs = [opt, redfilename, '-S']

    print_command(*disargs)
    dis = subprocess.check_output(disargs, universal_newlines=True)
    with open(targetfile, 'w+') as target:
        target.write('; RUN: opt %loadPolly -basicaa -scoped-noalias -tbaa ' + ''.join([shlex.quote(s) + ' ' for s in mllvm if s != '-polly' and s != '-polly-process-unprofitable' and s != '-polly-use-llvm-names']) + curpass + ' -analyze < %s\n\n')
        target.write('; Derived from test-suite/' + derived + '\n\n')
        target.write(dis)
    print("Reduced testcase written to",targetfile)




def add_clang_args(clangparser,optargs,emitargs,inputargs):
    if inputargs:
        clangparser.add_argument('-x',nargs=2)
    clangparser.add_argument('-o')
    if optargs:
        clangparser.add_argument('-O')
    if emitargs:
        clangparser.add_argument('-emit-obj', action='store_true')

def generate_preopt(opt,curpass,mllvm, llfile,outfile,tmpdir):
    args = [opt, llfile] + mllvm + ['-basicaa', '-scoped-noalias', '-tbaa', curpass, '-S', '-o', outfile]
    return invoke(*args, cwd=tmpdir, resumeonerror=True)

def generate_ll(clang, cc1_args, output, tmpdir):
    args = [clang] + cc1_args + ['-O0', '-S', '-emit-llvm', '-o', output]
    invoke(*args,cwd=tmpdir)

#def subprocess_stderr(cmdline,**kwargs):
#    with subprocess.Popen(cmdline, stderr=subprocess.PIPE, universal_newlines=True, **kwargs) as p:
#        stdout, stderr = p.communicate()
#        retcode = p.poll()
#        return stderr

def get_passes(clang, cc1_args,tmpdir):
    _,_,_,stderr = invoke(clang, *(cc1_args + ['-mllvm','-debug-pass=Arguments']),cwd=tmpdir,return_stderr=True)
    #stderr = subprocess_stderr([clang] + cc1_args + ['-mllvm','-debug-pass=Arguments'],cwd=tmpdir)
    passes = []
    for m in passargline.finditer(stderr):
        line = m.group('passes')
        passes += line.split()
    return passes


def genllfilename(testlogdir, inputreldir, inputbase, i,curpass=''):
    return os.path.join(testlogdir, inputreldir, inputbase + str(i) + curpass + '.ll')


def derive_testcase(cmd,  tmpdir, testlogdir, cmds=None):
    clangparser = argparse.ArgumentParser()
    add_clang_args(clangparser,optargs=True,emitargs=True,inputargs=False)

    clanginputparser = argparse.ArgumentParser()
    add_clang_args(clanginputparser,optargs=True,emitargs=True,inputargs=False)

    clangoptparser = argparse.ArgumentParser()
    add_clang_args(clangoptparser,optargs=False,emitargs=False,inputargs=False)

    if cmds is None:
        cmds = shlex.split(cmd)
    clang = cmds[0]
    opt = os.path.join(os.path.dirname(clang), 'opt')
    bugpoint = os.path.join(os.path.dirname(clang), 'bugpoint')
    known,unknown = clangparser.parse_known_args(cmds[1:])
    inputknown,inputunknown = clanginputparser.parse_known_args(cmds[1:])
    optknown,optunkonwn = clangoptparser.parse_known_args(cmds[1:])

    i = 1
    mllvm = []
    inputs = []
    remainder = []
    while i < len(cmds):
        if cmds[i] == '-mllvm':
            mllvm.append(cmds[i + 1])
            i+=2
            continue
        elif cmds[i].startswith('-mllvm='):
            mllvm.append(cmds[i][7:])
        elif cmds[i].startswith('-'):
            pass
        elif os.path.isfile(cmds[i]):
            inputs.append(cmds[i])
            i+=1
            continue
        remainder.append(cmds[i])
        i += 1

    assert(len(inputs)==1)
    inputpath = inputs[0]
    inputdir,inputfile = os.path.split(inputpath)
    inputbase,inputext = os.path.splitext(inputfile)

    inputrelpath = os.path.relpath(inputpath,start=test_suite)
    inputreldir = os.path.relpath(inputdir,start=test_suite)

    #outputpath = known.o
    #if outputpath is not None:
    #    outputdir,outputfile = os.path.split(outputpath)
    #    outputbase,outputext = os.path.splitext(outputfile)

    llfile = genllfilename(testlogdir, inputreldir, inputbase, 0)

    print("Reducing fail of", inputrelpath)
    passes = get_passes(clang, optunkonwn, tmpdir)

    generate_ll(clang, inputunknown, llfile, tmpdir)
    lastllfile = llfile
    i = 1
    for curpass in passes:
        # TODO: From -polly-detect to -polly-codegen we have implicit
        # state
        # Keep all passes since -polly-detect to not loose state
        newllfile = genllfilename(testlogdir, inputreldir, inputbase, i, curpass)
        genresult,rtncode = generate_preopt(opt,curpass,mllvm,lastllfile,newllfile,tmpdir)
        if not genresult:
            print('###', curpass, "failed")
            targetfile = os.path.join(unit_tests,inputbase + '.ll')
            j = 0
            while os.path.isfile(targetfile):
                targetfile = os.path.join(unit_tests,inputbase + str(j) + '.ll')
                j+=1
            bugpoint_reduce(bugpoint,opt,curpass,mllvm,lastllfile,targetfile,tmpdir,inputrelpath)
            return
        lastllfile = newllfile
        i += 1

    print("Everything executed ?!?")




def gittool_bugpointreduce(logfile=None,content=None,testlogdir=None):
    if content is None:
        with open(logfile, 'r') as file:
            content = file.read()

    global failline
    fails = failline.finditer(content)
    for fail in fails:
        print(fail)
        with tempfile.TemporaryDirectory(prefix='bugpoint-') as tmpdir:
            derive_testcase(fail.group('cmd'), tmpdir, tmpdir if testlogdir is None else os.path.join(testlogdir, 'build'))

def parse_opt_args(*args,Inputs=False,S=False,Passes=False):
    optparser = argparse.ArgumentParser(allow_abbrev=False)
    if S:
        optparser.add_argument('-S',action='store_true')

    known,unknown= optparser.parse_known_args(args[1:])

    knownpasses = set()
    if Passes:
        _,_,helpout,_ = invoke(args[0], '-help-list', return_stdout=True )
        passlist = re.findall(r'^    \-(?P<passname>[a-zA-Z0-9_\-]+)\s*\- ', helpout, re.MULTILINE)
        knownpasses = set('-' + passname for passname in passlist )
        assert(knownpasses)


    inputargs = []
    newunknown = []
    passes = []

    i = 0
    while i < len(unknown):
        arg = unknown[i]
        nextarg = unknown[i+1] if i +1 <len(unknown) else None

        if Passes and arg in knownpasses:
            passes.append(arg)
            i+=1
            continue
        elif Inputs and arg =='<':
            inputargs.append(nextarg)
            i+=2
            continue
        elif arg.startswith('-'):
            pass
        elif Inputs and os.path.isfile(arg):
            inputargs.append(arg)
            i+=1
            continue
        newunknown.append(arg)
        i+=1

    if Inputs:
        known.inputs = inputargs
    if Passes:
        known.passes = passes

    return known,newunknown


def parse_clang_args(*args,I=False,D=False,O=False,mllvm=False,Inputs=False,c=False,o=False,emit_obj=False,internal_i=False,v=False,DebugPass=False,include=False,MT=True,MF=True,dependency_file=True):
    clangparser = argparse.ArgumentParser(allow_abbrev=False)
    abbrevparser = argparse.ArgumentParser(allow_abbrev=True)

    if o:
        abbrevparser.add_argument('-o')
    if O:
        abbrevparser.add_argument('-O')
    if MF:
        abbrevparser.add_argument('-MF')
    if MT:
        abbrevparser.add_argument('-MT')
    if dependency_file:
        clangparser.add_argument('-dependency-file')

    if emit_obj:
        clangparser.add_argument('-emit-obj', action='store_true')
    if I:
        abbrevparser.add_argument('-I')
    if D:
        abbrevparser.add_argument('-D')
    if c:
        # without allow_abbrev=False, matches '-cc1'
        clangparser.add_argument('-c', action='store_true')
    if v:
        clangparser.add_argument('-v', action='store_true')
    if internal_i:
        clangparser.add_argument('-internal-isystem')
        clangparser.add_argument('-internal-externc-isystem')

    if include :
        abbrevparser.add_argument('-include')

    known,unknownpwabbrev = clangparser.parse_known_args(args[1:])
    abbrev,unknown = abbrevparser.parse_known_args(unknownpwabbrev)

    # Combine parses
    for key,val in vars( abbrev).items():
        setattr(known, key, val)

    i = 0
    # clangparser.add_argument('-mllvm') does not work because the next element often is an option itself, which argparse would not interpret as the argument to -mllvm
    mllvmargs = []
    inputargs = []
    remainder = []
    while i < len(unknown):
        arg = unknown[i]
        nextarg = unknown[i+1] if i +1 <len(unknown) else None
        #if arg == '-c':
        #    known.c = True
        #    i+=1
        #    continue
        if arg == '-x' and nextarg is not None:
            i+=2
            remainder.append(arg)
            remainder.append(nextarg)
            continue
        if DebugPass and arg == '-mllvm'  and nextarg.startswith('-debug-pass='):
            known.debug_pass = nextarg[12:]
            i+=2
            continue
        if mllvm and arg == '-mllvm' and nextarg is not None:
            mllvmargs.append(nextarg)
            i+=2
            continue
        elif mllvm and arg.startswith('-mllvm='):
            mllvmargs.append(arg[7:])
            i+=1
            continue
        #elif O and arg == '-O' and nextarg is not None:
        #    known.O = nextarg
        #    i+=2
        #    continue
        #elif O and arg.startswith('-O'):
        #    known.O = arg[2:]
        #    i+=1
        #    continue
        elif arg.startswith('-'):
            pass
        elif Inputs and os.path.isfile(arg):
            inputargs.append(arg)
            i+=1
            continue
        remainder.append(arg)
        i += 1
    if mllvm:
        known.mllvm = mllvmargs
    if Inputs:
        known.inputs = inputargs
    unknown = remainder

    exe = args[0]
    known.exe = exe
    if exe.lower().endswith('.exe'):
        exe = exe[:-4]
    known.cxx = exe.endswith('++')
    if len(remainder)>=1 and remainder[0]=='-cc1':
        known.mode = 'clang -cc1'
    elif known.cxx:
        known.mode = 'clang++'
    else:
        known.mode = 'clang'

    return known,unknown


def clang_mllvm(mllvm):
    if mllvm is None:
        return []
    result = []
    for arg in mllvm:
        result.append('-mllvm')
        result.append(arg)
    return result

def clang_optlevel(O):
    if O is None:
        return []
    return ['-O' + O]

def unique_path(filepath):
    i = 0
    dir,name = os.path.split(filepath)
    base,ext = os.path.splitext(filepath)
    while os.path.exists(filepath):
        filepath = os.path.join(dir,"{base}_{i}{ext}".format(base=base,i=i,ext=ext))
        i+=1
    return filepath



def gittool_reduce(testfile,build,cpp_includes, cpp_macros, cpp_lines, cc_cc1,cc_minargs,cc_afl,cc_format, dump_ll, emit_ll,ll_minargs,fewer_passes, bugpoint,writetest,inplace):
    testfilepath = os.path.join(unit_tests, testfile)
    testdir = os.path.dirname(testfilepath)

    with open(testfilepath, 'r') as f:
        testcase = f.read()

    m = re.search(r'^\s*\;\s*RUN\s*\:\s*(?P<cmdline>.*)$', testcase, re.MULTILINE)
    morig = re.search(r'\s*\;\s*Original\s+command\s*\:\s*(?P<cmdline>.*)$', testcase, re.MULTILINE)
    mderived = re.search(r'\s*\;\s*Derived from\s+(?P<derived>.*)$', testcase, re.MULTILINE)
    cmdline = m.group('cmdline')
    cmdline = shlex.split(cmdline)
    cmdline = [arg.replace('%s', testfilepath).replace('%S', testdir) for arg in cmdline]

    oldcmdline = cmdline
    cmdline=[]
    for arg in oldcmdline:
        if arg=='%loadPolly':
            cmdline += ['-polly-process-unprofitable', '-polly-remarks-minimal', '-polly-use-llvm-names']
        else :
            cmdline.append(arg)

    prog = cmdline[0]
    args = cmdline[1:]
    prog = os.path.join(homedir,'build','llvm','release','bin',prog)
    if os.path.isfile(prog + '.exe'):
        prog += '.exe'
    #cmdline[0] = prog

    kwargs = {}
    if inplace:
        kwargs['targettestfile'] = testfile
    if morig:
        kwargs['origcmdline'] = morig.group('cmdline')
    if mderived:
        kwargs['originput'] = mderived.group('derived')

    reduce(cmdline,build=build,cpp_includes=cpp_includes ,cpp_macros=cpp_macros,cpp_lines=cpp_lines, cc_cc1=cc_cc1, cc_minargs=cc_minargs ,cc_afl=cc_afl,cc_format=cc_format,dump_ll=dump_ll ,emit_ll=emit_ll ,ll_minargs=ll_minargs ,fewer_passes=fewer_passes, ll_bugpoint=bugpoint ,writetest=writetest,**kwargs)





def gittool_reproduce(cmdline,asif,even_successful,build,cpp_includes, cpp_macros,cpp_lines,cc_cc1,cc_minargs,cc_afl,cc_format,dump_ll, emit_ll,ll_minargs,fewer_passes, bugpoint,writetest,clang_cwd):
    if asif:
        success,errocode = invoke(*cmdline, resumeonerror=True)

    if not asif or not success or even_successful:
        reduce(cmdline,build=build,cpp_includes=cpp_includes ,cpp_macros=cpp_macros,cpp_lines=cpp_lines,cc_cc1=cc_cc1, cc_minargs=cc_minargs ,cc_afl=cc_afl,cc_format=cc_format ,dump_ll=dump_ll, emit_ll=emit_ll ,ll_minargs=ll_minargs ,fewer_passes=fewer_passes, ll_bugpoint=bugpoint ,writetest=writetest,clang_cwd=clang_cwd)

    if asif:
        exit(errocode)


class ReduceState:
    def __init__(self):
        pass

class ReduceStateSource(ReduceState):
    filepath = None
    args = None

    def __init__(self):
        super().__init__(self)
        pass

class ReduceStateIR(ReduceState):
    filepath = None
    args = None
    passes = None

    def __init__(self):
        super().__init__(self)
        pass



def reduce(cmdline,build,cpp_includes,cpp_macros,cpp_lines,cc_cc1,cc_minargs,cc_afl,cc_format,dump_ll,emit_ll,ll_minargs,fewer_passes,ll_bugpoint,writetest,targettestfile=None,origcmdline=None,originput=None,clang_cwd=None) :
    global homedir

    exepath = cmdline[0]
    if os.path.isabs(exepath):
        pass
    elif os.path.exists(os.path.join('bin', exepath)):
        exepath = os.path.abspath(os.path.join( 'bin', exepath))
    elif os.path.exists(os.path.join('bin', exepath  + '.exe')):
        exepath = os.path.abspath(os.path.join('bin', exepath + '.exe'))
    else:
        exepath = shutil.which(exepath)

    exedir,exefilename = os.path.split(exepath)
    exebasename,exeext = os.path.splitext(exefilename)

    if build:
        targets=[]
        if exebasename!='opt':
            targets.append('clang')
        if exebasename=='opt' or ll_minargs or fewer_passes:
            targets.append('opt')
        if cc_format:
            targets.append('clang-format')
        if ll_bugpoint:
            targets.append('bugpoint')
        llvmbuilddir = os.path.join(homedir,'build','llvm','release')  # os.path.dirname(exepath)
        ninja = True
        while True:
            path,dirname = os.path.split(llvmbuilddir)
            if dirname in ['Debug','Release']:
                ninja = False
            if dirname in ['bin','Debug','Release']:
                llvmbuilddir  = path
                continue
            break

        builddir = os.path.join(homedir,'build')
        if os.path.commonprefix([llvmbuilddir, builddir]) == builddir:
            print("### Building...")
            if ninja:
                invoke('ninja', *targets,cwd=llvmbuilddir)
            else:
                for target in targets:
                    invoke('cmake', '--build', llvmbuilddir, '--target',target)

        exepath = os.path.join( llvmbuilddir,'bin',exefilename)
        if os.path.isfile(exepath + '.exe'):
            exepath = exepath + '.exe'



    with tempfile.TemporaryDirectory(prefix='reproduce-') as tmpdir:
        #cmd = cmdline[0]
        #args = cmdline[1:]

        if exebasename=='opt':
            known,mllvm=parse_opt_args(*cmdline,Inputs=True,Passes=True,S=True)
            if len(known.inputs)==0:
                print("No file to reduce")
                return
            assert(len(known.inputs)==1)
            inputfilepath = known.inputs[0]

            c_mode = None
            c_filepath = None
            c_args = None

            ll_filepath = inputfilepath
            ll_mllvm = mllvm
            ll_passes = known.passes
        else:
            known,unknown = parse_clang_args(*cmdline,Inputs=True,c=True,o=True)
            if len(known.inputs)==0:
                print("No file to reduce")
                return
            if not known.c and known.mode != 'clang -cc1':
                print("Cannot reduce linking")
                return
            print("Input: ",known.inputs)
            assert(len(known.inputs)==1)
            inputfilepath = os.path.abspath(known.inputs[0])
            #mllvm = known.mllvm

            # Passed on data in c/c++ format
            c_mode = known.mode # 'clang', 'clang++', 'clang -cc1'
            c_filepath = inputfilepath
            c_args = unknown
            #c_optlevel = known.O
            #c_mllvm = mllvm

            # Passed on data in ll format
            ll_filepath = None
            ll_passes = None
            ll_mllvm = None

            inputdir,inputfile = os.path.split(inputfilepath)
            inputbase,inputext = os.path.splitext(inputfile)


        clang = os.path.join(os.path.dirname(exepath), 'clang')
        clangpp = os.path.join(os.path.dirname(exepath), 'clang++')
        opt = os.path.join(os.path.dirname(exepath), 'opt')
        bugpoint = os.path.join(os.path.dirname(exepath), 'bugpoint')
        clang_format = os.path.join(os.path.dirname(exepath), 'clang-format')
        tmin = os.path.join(homedir, 'src', 'afl-2.39b', 'afl-tmin')
        bugpointexe = os.path.join(os.path.dirname(exepath),'bugpoint')

        if clang_cwd is None:
            clang_cwd=tmpdir

        if originput is None:
            originput = inputfilepath
        else:
            #originputdir,originputfile = os.path.split(originput)
            #originputbase,originputext = os.path.splitext(originputfile)
            pass

        # OS-independent approach
        split = originput.replace('\\','/') .split(sep='/')
        inputbase,originputext = os.path.splitext(split[-1])



        def run_clang(args,mllvm=None,optlevel=None,**kwargs):
            clang_opts = args[:]
            clang_opts += clang_mllvm(mllvm)
            clang_opts += clang_optlevel(optlevel)
            if len(args)>0 and args[0]=='-cc1':
                clang_opts += [c_filepath]
            else:
                clang_opts += ['-c', c_filepath]
            return invoke(clang, *clang_opts,cwd=clang_cwd,resumeonerror=True,**kwargs)


        if c_filepath is not None and c_mode != 'clang -cc1' and cc_cc1:
            print("### Deriving -cc1 arguments...")
            _,_,_,out = run_clang(['-###']+c_args,return_stderr=True)

            print(out)
            m=re.search(r'^ (?P<cmdline>.*clang.*\s+(\-cc1|\"\-cc1\")\s+.*)$', out, re.MULTILINE)
            cc1line = m.group('cmdline').replace( '\\\\', '\\' )
            known,unknown = parse_clang_args(*shlex.split(cc1line),o=True,Inputs=True,v=True)

            c_args = unknown
            c_mode = 'clang -cc1'

            print("## -cc1 arguments are:", shquote(c_args))
            print("## Scrapped arguments:",known)
            print()


        if c_filepath is not None and (cpp_includes or cpp_macros):
            print("### Preprocessing...")
            cppout = os.path.join(tmpdir,inputbase + '-cpp' + inputext)
            clang_opts = c_args[:]
            clang_opts += [c_filepath,'-E']
            if not cpp_macros:
                clang_opts += ['-frewrite-includes']
            if cpp_lines:
                clang_opts += ['-P']
            clang_opts += ['-o',cppout]
            invoke(clang, *clang_opts,cwd=clang_cwd)

            _,strippedargs = parse_clang_args(clang, *c_args, I=True, D=cpp_macros,internal_i=True,o=True,include=cpp_includes)
            if cpp_macros:
                strippedargs.append('-fpreprocessed')

            c_filepath = cppout
            c_args = strippedargs



        if c_filepath is not None and cc_afl:
            print("### Reducing file using afl...")
            reducedout = os.path.join(tmpdir,inputbase + '-tmin' + inputext)
            clang_opts = c_args[:]
            clang_opts += clang_mllvm(c_mllvm)
            clang_opts += clang_optlevel(c_optlevel)
            clang_opts += ['-Werror=implicit-int']
            invoke(tmin,'-t', '10000','-i',c_filepath,'-o',reducedout,'--',clang,*clang_opts,cwd=clang_cwd)

            c_filepath = reducedout


        if c_filepath is not None and cc_minargs:
            print("### Reducing arguments...")

            success,expected_rtncode = run_clang(c_args)
            #assert(not success)

            known,args = parse_clang_args(clang, *c_args, mllvm=True,O=True,c=True)
            c_mllvm = known.mllvm
            c_optlevel = known.O

            print("## Reducing general arguments...")
            i = 0
            while i < len(args):
                tryargs = args[:]
                del tryargs[i]

                _,rtncode = run_clang(tryargs,c_mllvm,c_optlevel)
                if rtncode == expected_rtncode:
                    args = tryargs
                    continue

                tryargs = args[:]
                del tryargs[i:i+2]
                _,rtncode = run_clang(tryargs,c_mllvm,c_optlevel)
                if rtncode == expected_rtncode:
                    args = tryargs
                    continue

                i += 1

            print("## Reducing -mllvm arguments...")
            i = 0
            while i < len(c_mllvm):
                trymllvm = c_mllvm[:]
                del trymllvm[i]
                _,rtncode = run_clang(args,trymllvm,c_optlevel)
                if rtncode == expected_rtncode:
                    c_mllvm = trymllvm
                    continue

                trymllvm = c_mllvm[:]
                del trymllvm[i:i+2]
                _,rtncode = run_clang(args,trymllvm,c_optlevel)
                if rtncode == expected_rtncode:
                    c_mllvm = trymllvm
                    continue

                i+=1

            print("## Reducing -O argument...")
            def tryreduceoptlevel(fr,to):
                nonlocal c_optlevel
                if c_optlevel == fr:
                    _,rtncode = run_clang(args,c_mllvm,to)
                    if rtncode == expected_rtncode:
                        c_optlevel = to
            tryreduceoptlevel('3','2')
            tryreduceoptlevel('2','1')
            tryreduceoptlevel('1','0')

            tryreduceoptlevel('z','s')
            tryreduceoptlevel('s','0')

            tryreduceoptlevel('0',None)

            c_args = args + clang_mllvm(c_mllvm) + clang_optlevel(c_optlevel)



        if c_filepath is not None and cc_format:
            print("### Reformating...")
            formatout = os.path.join(tmpdir,inputbase + '-format' + inputext)
            invoke(clang_format, '--assume-filename=' + inputfile, c_filepath, stdout=formatout, cwd=tmpdir)
            if not os.path.isfile(formatout):
                raise Exception("No file output")

            c_filepath = formatout



        def run_pass(mllvm,passes,inpfile,outfile,**kwargs):
            opt_opts = mllvm[:]
            #opt_opts += ['-basicaa', '-scoped-noalias', '-tbaa']
            opt_opts += passes
            opt_opts += [inpfile, '-S', '-o', outfile]
            return invoke(opt, *opt_opts, cwd=tmpdir, resumeonerror=True,**kwargs)

        def ll_replace_if_sameresult(mllvm,passes,inputfile,resultfile=None):
            if resultfile is None:
                resultfile = unique_path(os.path.join(tmpdir, '{inputbase}-sameresult.ll'.format(inputbase=inputbase)))
            success,expectedrtn = run_pass(mllvm, passes, inputfile, resultfile)
            if expectedrtn == gen_expectedrtn:
                ll_filepath = inputfile
                ll_mllvm = mllvm
                ll_passes = passes
                return True
            return False


        if c_filepath is not None and dump_ll:
            regularout = os.path.join(tmpdir,inputbase + '-clang.ll')
            dumpout = os.path.join(tmpdir,inputbase + '-dump.ll')
            #osargs = []
            #if os.name == 'nt':
            #    osargs.append(r'''-IC:\Users\Meinersbur\AppData\Local\lxss\rootfs\usr\include''')

            known,unknown = parse_clang_args(clang,*c_args,mllvm=True,c=True)
            if known.mode != 'clang -cc1':
                unknown += ['-c']

            _,rtnval,_,stderr = invoke(clang, *(unknown + clang_mllvm(known.mllvm) + ['-emit-llvm','-mllvm','-debug-pass=Arguments', '-mllvm', '-polly-dump-before-file='+dumpout ,c_filepath,'-o',regularout]),  cwd=clang_cwd,return_stderr=True,resumeonerror=True)

            passes = []
            for m in passargline.finditer(stderr):
                line = m.group('passes')
                passes += line.split()
                passes.append('-barrier')
            assert(passes)
            dumppassindex = max(loc for loc, val in enumerate(passes) if val == '-polly-dump-module')


            mllvm = known.mllvm

            dump1out = os.path.join(tmpdir,inputbase + '-dump1.ll')
            passes1 = passes[dumppassindex+1:]
            success1,rtncode1 = run_pass(mllvm, passes1, dumpout, dump1out)

            dump2out = os.path.join(tmpdir,inputbase + '-dump2.ll')
            passes2 = passes[:dumppassindex] + passes[dumppassindex+1:]
            success2,rtncode2 = run_pass(mllvm, passes2, dumpout, dump2out)

            if rtncode1 == rtncode2:
                ll_passes = passes1
            elif not success1:
                ll_passes = passes1
            else:
                ll_passes = passes2
            ll_filepath = dumpout
            ll_mllvm = mllvm


        if c_filepath is not None and emit_ll and  ll_filepath is None:
            print("### Generating unoptimized ll..")
            outfilepath = os.path.join(tmpdir, inputbase + '-nonopt.ll')

            known,unknown = parse_clang_args(clang,*c_args,O=True)

            clang_opts = unknown[:]
            clang_opts += ['-O0']
            if known.O is not None and known.O != '0':
                clang_opts += ['-D__OPTIMIZE__', '-U__NO_INLINE__'] # TODO: __NO_INLINE__ is conditional on -fno-inline
            if known.O == 's' or known.O == 'z':
                clang_opts += ['-D__OPTIMIZE_SIZE__']
            clang_opts += [c_filepath, '-S', '-emit-llvm',  '-o', outfilepath]
            if c_mode!='clang -cc1':
                clang_opts+=['-c']
            invoke(clang, *clang_opts,cwd=tmpdir)


            tmpfilepath = os.path.join(tmpdir, inputbase + '-clangopt.ll')
            known,unknown = parse_clang_args(clang,*c_args,DebugPass=True)
            clang_opts = unknown[:]
            clang_opts += clang_mllvm(['-debug-pass=Arguments'])
            if c_mode!='clang -cc1':
                clang_opts+=['-c']
            clang_opts += [c_filepath, '-S', '-emit-llvm', '-o', tmpfilepath]
            _,_,_,stderr = invoke(clang, *clang_opts,cwd=tmpdir,return_stderr=True,resumeonerror=True)
            passes = []
            for m in passargline.finditer(stderr):
                line = m.group('passes')
                passes += line.split()
                passes.append('-barrier')
            assert(passes)

            known,unknown = parse_clang_args(clang,*c_args,mllvm=True)

            ll_passes = passes
            ll_filepath = outfilepath
            ll_mllvm = known.mllvm




        if ll_filepath is not None and (fewer_passes or ll_minargs or ll_bugpoint):
            genllfilepath = os.path.join(tmpdir, inputbase + '.ll')
            gensuccess,gen_expectedrtn = run_pass(ll_mllvm, ll_passes, ll_filepath, genllfilepath)
            ll_genfail = not gensuccess




        if ll_filepath is not None and fewer_passes and ll_genfail:
            print("### Invoke fewer passes...")

            #genllfilepath = os.path.join(tmpdir, inputbase + '.ll')
            #gensuccess,_ = invoke(opt, *(mllvm + ['-basicaa', '-scoped-noalias', '-tbaa', passes, '-S', '-o', genllfilepath]), cwd=tmpdir, resumeonerror=True)
            #assert(not gensuccess)

            testi = 0
            Changed =False
            def trypasssplit(precomputepasses, keeppasses, name):
                nonlocal ll_filepath,ll_passes,Changed,testi
                assert(keeppasses)
                testi+=1

                if precomputepasses:
                    genllfilepath = unique_path( os.path.join(tmpdir, '{inputbase}{i}-{name}.ll'.format(inputbase=inputbase,i=testi,name=name)))
                    _,rtncode = run_pass(ll_mllvm,precomputepasses,ll_filepath,genllfilepath)

                    if rtncode == gen_expectedrtn and len(ll_passes)>len(keeppasses):
                        print("## Failing precomputed passes:",' '.join(precomputepasses))
                        ll_passes = precomputepasses
                        Changed = True
                        return 2
                    elif rtncode != 0:
                        print("## Could not precompute passes but also did not crash")
                        return False
                else:
                    genllfilepath = ll_filepath

                endresultfilepath =  unique_path( os.path.join(tmpdir, '{inputbase}{i}-{name}.ll'.format(inputbase=inputbase,i=testi,name=name)))
                resultsuccess,rtncode = run_pass(ll_mllvm,keeppasses,genllfilepath,endresultfilepath)
                if rtncode == gen_expectedrtn:
                    print("## Still crashes:",' '.join(keeppasses))
                    ll_filepath = genllfilepath
                    ll_passes = keeppasses
                    Changed = True
                    return True

                print("## Does not crash:", ' '.join( keeppasses))
                return False


            persistent = 0
            while persistent < len(ll_passes):
                Changed = False

                # Precompute head passes
                # TODO: Care for required analysis passes (those do not modify the IR itself, but provide info such as AliasAnalysis)
                i = len(ll_passes) - 1
                while i > persistent:
                    keep = ll_passes[:persistent]
                    head = ll_passes[persistent:i]
                    tail = ll_passes[i:]
                    if trypasssplit(keep + head, keep + tail, 'precompute') == True:
                        break
                    i-=1

                # Remove unused passes, starting at the tail
                i = len(ll_passes) - 1
                while i >= persistent and len(ll_passes)-persistent>1:
                    head = ll_passes[:i]
                    tail = ll_passes[i+1:]
                    trypasssplit([], head+tail , 'skip')
                    i-=1

                # Add first pass as persistent, might be a required analysis pass
                persistent += 1


                # Precompute, but keep
                #i = len(ll_passes) - 1
                #while i >=0:
                #    head = ll_passes[:i]
                #    tail = ll_passes[i:]
                #    if trypasssplit(head, head+tail, 'prekeep'):
                #        break
                #    i-=1


                #if not Changed:
                #    break



        if ll_filepath is not None and ll_minargs and ll_genfail:
            print("## Reducing opt arguments...")
            i = 0
            while i < len(ll_mllvm):
                trymllvm = ll_mllvm[:]
                del trymllvm[i]

                tmpllfilepath1 =  unique_path(os.path.join(tmpdir, inputbase + str(i) + '-optmllvm1.ll'))
                _,rtncode = run_pass(trymllvm,ll_passes,ll_filepath,tmpllfilepath1)
                if rtncode == gen_expectedrtn:
                    ll_mllvm = trymllvm
                    continue
                tmpllfilepath2 =  unique_path(os.path.join(tmpdir, inputbase + str(i) + '-optmllvm2.ll'))
                trymllvm = ll_mllvm[:]
                del trymllvm[i:i+2]
                _,rtncode = run_pass(trymllvm,ll_passes,ll_filepath,tmpllfilepath2)
                if rtncode == gen_expectedrtn:
                    ll_mllvm = trymllvm
                    continue

                i += 1


        if ll_filepath is not None and ll_bugpoint and ll_genfail:
            print("### Reducing fail using bugpoint...")

            args = []
            args += ['-opt-command=' + opt]
            args += [ll_filepath]
            args += ll_passes
            if ll_mllvm:
                args += ['-opt-args']
                args += ll_mllvm

            _,_,bpout,_ = invoke(bugpointexe, *args,return_stdout=True,cwd=tmpdir)
            m = [x for x in reproduceline.finditer(bpout)][-1]
            redfilename = os.path.join(tmpdir,m.group('filename'))
            print("Bugpoint output file is", redfilename)
            redpasses = shlex.split( m.group('passes'))


            redllfilename = os.path.join(tmpdir, inputbase + '-reduced.ll')
            invoke(opt, redfilename, '-S', '-o', redllfilename, cwd=tmpdir)

            ll_filepath = redllfilename
            ll_replace_if_sameresult(ll_mllvm, redpasses, ll_filepath)


        if writetest:
            testfilepath = targettestfile if targettestfile is not None else unique_path(os.path.join(unit_tests,inputbase + '.ll'))
            if origcmdline is None:
                origcmdline = ' '.join([shlex.quote(arg) for arg in cmdline])

            if ll_filepath is not None:
                print("### Writing ll regression test...")

                with open(ll_filepath, 'r') as source:
                    llcontent = source.read()
                with open(testfilepath, 'w+') as target:
                    target.write('; RUN: opt %loadPolly ' + ''.join([shlex.quote(s) + ' ' for s in ll_mllvm if s != '-polly' and s != '-polly-process-unprofitable' and s != '-polly-remarks-minimal' and s != '-polly-use-llvm-names']) + ' '.join(ll_passes) + ' -S < %s\n')
                    target.write('; Derived from ' + inputfilepath + '\n')
                    target.write('; Original command: ' + origcmdline + '\n\n')
                    target.write(llcontent)

                print("Reduced testcase written to",testfilepath)
            elif c_filepath is not None:
                testfileprefix,_ = os.path.splitext(testfilepath)
                targetfilepath = testfileprefix + '.c' #TODO: Use original file extension
                reltargetfilepath = os.path.relpath(targetfilepath, unit_tests)
                clangexe = 'clang' if c_mode=='clang -cc1' else c_mode

                with open(testfilepath, 'w+') as target:
                    target.write('; RUN: ' + clangexe + ' ' + ' '.join([shlex.quote(arg) for arg in c_args]  + [shlex.quote('%S/' + reltargetfilepath)]) + '\n')
                    target.write('; Original command: ' + origcmdline + '\n')
                if os.path.normpath(c_filepath) != os.path.normpath(targetfilepath):
                    shutil.copyfile(c_filepath, targetfilepath)

                print("Reduced testcase written to",testfilepath,"and",targetfilepath)
            else:
                print("No regression test available")






def gittool_extractreproducer(logfile=None,content=None):
    global unit_tests

    if content is None:
        with open(logfile, 'r') as file:
            content = file.read()

    global attachline
    fails = attachline.finditer(content)
    for fail in fails:
        shfilepath = fail.group('shfilename')
        print("Found:",shfilepath)
        shdir,shfilename = os.path.split(shfilepath)
        shbasename,shext = os.path.splitext(shfilename)

        with open(shfilepath, 'r') as file:
            while True:
                shcontent = file.readline()
                if not shcontent.startswith('#'):
                    break

        cmdline = shlex.split(shcontent)
        prog = cmdline[0]
        args = cmdline[1:-1]

        inpfilepath = os.path.join(shdir, cmdline[-1])
        inpdir,inpfilename = os.path.split(inpfilepath)

        targetfilename = os.path.join(unit_tests, shbasename + '.ll')
        with open(targetfilename, 'w+') as target:
            target.write('; RUN: clang ' + ' '.join([shlex.quote(arg) for arg in args] + [shlex.quote('%S/' + inpfilename)])  + '\n')

        inptargetfilepath = os.path.join(unit_tests,  inpfilename)
        shutil.copyfile(inpfilepath, inptargetfilepath)
        print("Written files:", [targetfilename,inptargetfilepath] )



def replace_file(src,dst):
    try:
        os.replace(src,dst)
    except:
        os.remove(dst)
        shutil.move(src,dst)


def gittool_mintest( filepath,min_args,cpp,afl,format, dryrun=False):
    global homedir

    filepath = os.path.join( homedir, 'src', 'llvm', 'tools' , 'polly', 'test', filepath)
    dirpath = os.path.dirname(filepath)

    with open(filepath, 'r') as f:
        testcase = f.read()

    m = re.search(r'^\s*\;\s*RUN\s*\:\s*(?P<cmd>.*)$', testcase, re.MULTILINE)
    cmd = m.group('cmd')
    cmd = shlex.split(cmd)
    prog = cmd[0]
    args = cmd[1:-1]
    inpfile = cmd[-1]
    originp = inpfile
    _,inpfilename = os.path.split(inpfile)
    inpbasename,inpext = os.path.splitext(inpfilename)
    assert(prog == 'clang');

    buildtype = 'release'
    if afl:
        buildtype = 'release_afl-gcc'

    builddir = os.path.join(homedir, 'build', 'llvm', buildtype)
    clang_release = os.path.join(builddir, 'bin', 'clang')
    if os.path.exists(clang_release + '.exe'):
        clang_release += '.exe'

    clangformat = os.path.join(builddir, 'bin', 'clang-format')
    if os.path.exists(clangformat + '.exe'):
        clangformat += '.exe'

    tobuild = ['clang']
    if format:
        tobuild.append('clang-format')
    invoke('ninja', *tobuild, cwd=builddir)

    with tempfile.TemporaryDirectory(prefix='mintest') as tmpdir:

        if cpp:
            print('### Preprocessing...')
            cppout = os.path.join(tmpdir,inpbasename + '-cpp' + inpext)
            invoke(clang_release, *[arg.replace('%s', filepath).replace('%S', dirpath) for arg in args + ['-E',inpfile,'-P','-o',cppout]],cwd=tmpdir)

            inpfile = cppout


        if min_args:
            print('### Reducing arguments...')
            success,expected_rtncode = invoke(clang_release, *[arg.replace('%s', filepath).replace('%S', dirpath) for arg in args + [inpfile]],cwd=tmpdir, resumeonerror=True)

            i = 0
            while i < len(args):
                tryargs = args[:]
                del tryargs[i]
                _,rtncode = invoke(clang_release, *[arg.replace('%s', filepath).replace('%S', dirpath) for arg in tryargs + [inpfile]],cwd=tmpdir, resumeonerror=True)
                if rtncode == expected_rtncode:
                    args = tryargs
                    continue

                tryargs = args[:]
                del tryargs[i:i+2]
                _,rtncode = invoke(clang_release, *[arg.replace('%s', filepath).replace('%S', dirpath) for arg in tryargs + [inpfile]],cwd=tmpdir, resumeonerror=True)
                if rtncode == expected_rtncode:
                    args = tryargs
                    continue

                # to remove eg. "-mllvm -debug-only -mllvm scop-detect"
                tryargs = args[:]
                del tryargs[i:i+4]
                _,rtncode = invoke(clang_release, *[arg.replace('%s', filepath).replace('%S', dirpath) for arg in tryargs + [inpfile]],cwd=tmpdir, resumeonerror=True)
                if rtncode == expected_rtncode:
                    args = tryargs
                    continue

                i += 1


        if afl:
            print('### Reducing file...')
            tmin = os.path.join(homedir,'src','afl-2.39b','afl-tmin')
            reducedout = os.path.join(tmpdir,inpbasename + '-tmin' + inpext)
            invoke(tmin,'-t', '10000','-i',inpfile.replace('%s', filepath).replace('%S', dirpath),'-o',reducedout,'--',clang_release,*[arg.replace('%s', filepath).replace('%S', dirpath) for arg in args + ['-Werror=implicit-int']],cwd=tmpdir)

            inpfile = reducedout

        if format:
            print('### Reformating...')
            formatout = os.path.join(tmpdir,inpbasename + '-format' + inpext)
            invoke(clangformat,inpfile,stdout=formatout,cwd=tmpdir)
            if not os.path.isfile(formatout):
                raise Exception("No file output")

            inpfile = formatout


        if not dryrun:
            if inpfile != originp:
                print('### Replacing ' + inpfilename + '...')
                replace_file(inpfile,originp.replace('%s', filepath).replace('%S', dirpath))

        if min_args:
            testdir,testfilename = os.path.split(filepath)
            newtestfile = os.path.join(tmpdir,testfilename)

            with open(newtestfile,'w+') as newllf:
                newllf.write('; RUN: clang ' + ' '.join([shlex.quote(arg) for arg in args + [originp]]) + '\n')

            if not dryrun:
                print('### Replacing ' + testfilename + '...')
                replace_file(newtestfile,filepath)



def gittool_runtest_alt(mllvm,testonly,threads=None,build_threads=None,exec_threads=None,verbose=False,bugpoint=False,processunprofitable=False,polly=False,suiteflags=None,keepgoing=False,build='release',debug=None,debug_only=None,reproduce=False,reproduce_all=False,llvmbuilddir=None,testsuitecmake=[]):
    global homedir,script
    srcdir = os.path.join(homedir, 'src')
    builddir = os.path.join(homedir, 'build')
    if llvmbuilddir is None:
        llvmbuilddir = os.path.join(builddir, 'llvm', build)
    llvmbuilddir = os.path.abspath(llvmbuilddir)
    tmpdir = tempfile.gettempdir()
    print("tmpdir is: " + tmpdir)
    lntdir = os.path.join(tmpdir, 'lnt')

    sandboxdir = tempfile.mkdtemp(prefix='runtests-')
    print("Using sandbox:",sandboxdir)

    testsuitesrcdir = os.path.join(srcdir, 'llvm', 'projects', 'test-suite')
    lntsrcdir = os.path.join(srcdir, 'llvm', 'projects', 'lnt')

    clang = os.path.join(llvmbuilddir,'bin','clang')
    clangxx = os.path.join(llvmbuilddir,'bin','clang++')
    llvmsize = os.path.join(llvmbuilddir,'bin','llvm-size')
    lit = os.path.join(llvmbuilddir,'bin','llvm-lit')
    lntpython = os.path.join(lntdir,'bin','python')
    lnt = os.path.join(lntdir, 'bin','lnt')
    cmake = shutil.which('cmake')

    reqbuild = ['clang', 'opt', 'llvm-size']
    if bugpoint:
        reqbuild.append('bugpoint')
    invoke('ninja', *reqbuild, cwd=llvmbuilddir)
    #invoke('ninja', 'check-polly-tests',cwd=llvmbuilddir,resumeonerror=True)

    if not os.path.exists(lnt):
        invoke('virtualenv', lntdir)
        invoke(lntpython, os.path.join(lntsrcdir, 'setup.py'), 'develop')

    if threads is None:
        threads = multiprocessing.cpu_count()
    if build_threads is None:
        build_threads = threads
    if exec_threads is None:
        exec_threads = threads

    cc = clang
    cxx = clangxx

    if bugpoint or reproduce or reproduce_all:
        reduceccfilepath = os.path.join(sandboxdir,'cc')
        reproduce_args = ['--no-build', '--as-if', '--write-test', '--preprocess-includes', '--cc1']
        if reproduce_all:
            reproduce_args.append('--even-successful')
        if bugpoint:
            reproduce_args.append('--emit-ll')
            reproduce_args.append('--bugpoint')

        with open(reduceccfilepath,'w+') as f:
            f.write('#! /bin/bash\n')
            f.write('python3 {script} reproduce {args} -- {clang} "$@"\n'.format(script=script,clang=clang,args=' '.join(reproduce_args)))
        os.chmod(reduceccfilepath, 0o755)

        reducdecxxfilepath = os.path.join(sandboxdir,'c++')
        with open(reducdecxxfilepath,'w+') as f:
            f.write('#! /bin/bash\n')
            f.write('python3 {script} reproduce {args} -- {clangxx} "$@"\n'.format(script=script,clangxx=clangxx,args=' '.join(reproduce_args)))
        os.chmod(reducdecxxfilepath, 0o755)

        cc = reduceccfilepath
        cxx = reducdecxxfilepath


    runtestopts = []

    if exec_threads is not None:
        runtestopts += ['--threads', exec_threads]
    if build_threads is not None:
        runtestopts += ['--build-threads', build_threads]

    if testonly is not None:
        runtestopts += ['--only-test', testonly]

    runtestopts += ['--cmake-define=' + conf for conf in testsuitecmake]

    if polly:
        runtestopts += ['--cppflags', '-mllvm','--cppflags', '-polly']

    if processunprofitable:
        runtestopts += ['--cppflags', '-mllvm','--cppflags','-polly-process-unprofitable']

    if suiteflags is not None:
        for flag in suiteflags:
            runtestopts += ['--cppflags', flag]

    if mllvm is not None:
        for opt in mllvm:
            runtestopts += ['--cppflags', '-mllvm', '--cppflags', opt]

    if verbose:
        runtestopts.append('-v')

    if debug:
        runtestopts += ['--cppflags', '-mllvm', '--cppflags', '-debug']
    if debug_only is not None:
        if not isinstance(debug_only, str):
            debug_only = ','.join(debug_only)
        runtestopts += ['--cppflags', '-mllvm', '--cppflags', '-debug-only='+debug_only]

    testlogpath = os.path.join(sandboxdir, 'output.txt')

    testlogoutpath = os.path.join(sandboxdir, 'stdout.txt')
    stdout = [testlogoutpath, sys.stdout, testlogpath]

    testlogerrpath = os.path.join(sandboxdir, 'stderr.txt')
    stderr = [testlogerrpath, sys.stderr, testlogpath]

    _,_,report,errreport  = invoke(lntpython, lnt, 'runtest', 'test-suite',
        '--sandbox' , sandboxdir,
        '--test-suite', testsuitesrcdir,
        '--cc', cc, '--cxx', cxx, '--use-lit', lit,
        '--cmake-define', 'TEST_SUITE_LLVM_SIZE=' + llvmsize,
        '--use-cmake', cmake,
        '--cmake-cache', 'ReleaseNoLTO',
        '--no-timestamp',
        '--benchmarking-only',
        *runtestopts,  stdout=stdout, stderr=stderr, return_stderr=True,return_stdout=True)

    m = re.search(r'^FAIL\s*\:(.*)$',errreport,re.MULTILINE)
    if not m:
        m = re.search(r'^FAIL\s*\:(.*)$',report,re.MULTILINE)

    print("Sandbox was:", sandboxdir)
    if m:
        print("Fail status:", m.group(0))
        print("ENDSTATUS: TESTFAIL",file=sys.stderr)
        print("ENDSTATUS: TESTFAIL",file=sys.stdout)
    else:
        print("ENDSTATUS: SUCCESS",file=sys.stderr)
        print("ENDSTATUS: SUCCESS",file=sys.stdout)



def first_existing(*args):
    assert(len(args) >= 1)
    for arg in args[:-1]:
        if os.path.exists(arg):
            return arg
    return args[-1]


def first_defined(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None

def empty_none(arg):
    if arg is None:
        return []
    return arg

def min_none(*args):
    result = args[0]
    for arg in args[1:]:
        if result is None:
            result = arg
        if arg is None:
            continue
        result = min(result, arg)
    return result


def max_none(first, *args):
    result = args[0]
    for arg in args[1:]:
        if result is None:
            result = arg
        if arg is None:
            continue
        result = max(result, arg)
    return result


class RuntestConfig:
    scalar_props = {
        'verbose', 'build_verbose', 'llvm_build_verbose', 'suite_build_verbose', 'exec_verbose', 'suite_exec_verbose',
        'threads', 'build_threads', 'llvm_build_threads', 'suite_build_threads', 'exec_threads', 'suite_exec_threads','thread_limit',
        'load', 'build_load', 'llvm_build_load', 'suite_build_load', 'exec_load', 'suite_exec_load','load_limit',
        'llvm_source_dir', 'polly_source_dir', 'llvm_build_dir', 'suite_source_dir', 'suite_build_dir',
        'revision', 'llvm_revision', 'clang_revision', 'libcxxabi_revision', 'libcxx_revision', 'polly_revision', 'suite_revision',
        'llvm_checkout', 'llvm_configure',
        'suite_build_polly','suite_build_pollyprocessunprofitable', 'suite_build_stats',
        'suite_build_debug', 'suite_build_reproduce', 'suite_build_reproduceall',
        'suite_build_useperf', 'suite_build_taskset', 'suite_build_libcxx',
        'suite_exec_taskset',
        'suite_exec_multisample'
        }
    list_props = {
        'llvm_build_cmakeargs', 'llvm_build_cmakedefs', 'llvm_build_flags',
        'suite_testonly',
        'suite_build_cmakeargs', 'suite_build_cmakedefs', 'suite_build_flags', 'suite_build_mllvm','suite_build_debugonly'
        }
    props = scalar_props | list_props


    def __init__(self):
        for prop in self.props:
            setattr(self, prop, None)

    @staticmethod
    def add_runtest_arguments(parser):
        parser.add_argument('--only-test', '--test-only', action='append', help="Only configure/run this test-suite subdir")

        parser.add_argument('--llvm-source-dir') # only: run-test-suite
        parser.add_argument('--llvm-build-dir')  # only: runtest, run-test-suite
        parser.add_argument('--suite-build-dir')

        parser.add_argument('--verbose', '-v', action='store_const', const=True,  help="Verbose everything")
        parser.add_argument('--build-verbose', action='store_const', const=True)
        parser.add_argument('--llvm-build-verbose', action='store_const', const=True)
        parser.add_argument('--suite-build-verbose', action='store_const', const=True)
        parser.add_argument('--exec-verbose', action='store_const', const=True)
        parser.add_argument('--suite-exec-verbose', action='store_const', const=True,  help="Verbose lit")

        parser.add_argument('--threads', '-j', type=int, help="Number of threads")
        parser.add_argument('--build-threads', type=int, help="Number of compile/link threads")
        parser.add_argument('--llvm-build-threads', type=int)
        parser.add_argument('--suite-build-threads', type=int)
        parser.add_argument('--suite-exec-threads','--exec-threads', type=int, help="Number of execution threads")
        parser.add_argument('--thread-limit', type=int, help="Hard limit of threads to start")

        parser.add_argument('--load', type=float)
        parser.add_argument('--build-load',type=float)
        parser.add_argument('--llvm-build-load',type=float)
        parser.add_argument('--suite-build-load',type=float)
        parser.add_argument('--suite-exec-load','--exec-load',type=float)
        parser.add_argument('--load-limit', type=float)

        parser.add_argument('--revision')
        parser.add_argument('--llvm-revision')
        parser.add_argument('--clang-revision')
        parser.add_argument('--libcxxabi-revision')
        parser.add_argument('--libcxx-revision')
        parser.add_argument('--polly-revision')
        parser.add_argument('--suite-revision','--test-suite-revision')

        parser.add_argument('--llvm-build-cmakeargs', action='append')
        parser.add_argument('--llvm-build-cmakedefs', action='append')

        parser.add_argument('--suite-build-cmakeargs', action='append')
        parser.add_argument('--suite-build-cmakedefs', action='append')
        parser.add_argument('--suite-build-polly','--polly', '-polly','--suite-polly', action='store_const', const=True,  help="Enable Polly")
        parser.add_argument('--suite-build-polly-process-unprofitable', '--polly-process-unprofitable', '-polly-process-unprofitable',  '--suite-polly-process-unprofitable',action='store_const', const=True, help="Enable Polly in 'process-unprofitable' mode")
        parser.add_argument('--suite-build-stats','--stats', action='store_const', const=True,  help="Get compiler transformation statistics")
        parser.add_argument('--suite-build-mllvm','--suite-mllvm','--mllvm', action='append')
        parser.add_argument('--suite-build-flags','--suite-flags', '--cppflags', '--flags', action='append')
        parser.add_argument('--suite-build-libcxx', '--suite-libcxx', '--libcxx', action='store_const', const=True, help="Use libc++ from source instead of the default C++ standard library")
        parser.add_argument('--suite-build-reproduce',  '--reproduce', action='store_const', const=True)
        parser.add_argument('--suite-build-reproduce-all', '--reproduce-all', action='store_const', const=True)

        parser.add_argument('--suite-exec-multisample', '--exec-multisample', '--multisample',type=int)



    @classmethod
    def from_cmdargs(cls,args):
        self = cls();

        self.verbose = args.verbose
        self.build_verbose = args.build_verbose
        self.llvm_build_verbose = args.llvm_build_verbose
        self.suite_build_verbose = args.suite_build_verbose
        self.suite_exec_verbose = args.suite_exec_verbose

        self.threads=args.threads
        self.build_threads=args.build_threads
        self.llvm_build_threads = args.llvm_build_threads
        self.suite_build_threads = args.suite_build_threads
        self.suite_exec_threads=args.suite_exec_threads
        self.thread_limit=args.thread_limit

        self.load = args.load
        self.build_load = args.build_load
        self.llvm_build_load = args.llvm_build_load
        self.suite_build_load = args.suite_build_load
        self.suite_exec_load = args.suite_exec_load
        self.load_limit = args.load_limit

        self.revision = parseRev(args.revision)
        self.llvm_revision = parseRev(args.llvm_revision)
        self.clang_revision = parseRev(args.clang_revision)
        self.polly_revision = parseRev(args.polly_revision)
        self.suite_revision = parseRev(args.suite_revision)
        self.libcxxabi_revision = parseRev(args.libcxxabi_revision)
        self.libcxx_revision = parseRev(args.libcxx_revision)

        self.llvm_source_dir = args.llvm_source_dir
        self.llvm_build_dir = args.llvm_build_dir
        self.suite_build_dir = args.suite_build_dir

        self.llvm_build_cmakeargs = args.llvm_build_cmakeargs
        self.llvm_build_cmakedefs= args.llvm_build_cmakedefs

        self.suite_testonly=args.only_test

        self.suite_build_cmakeargs = args.suite_build_cmakeargs
        self.suite_build_cmakedefs= args.suite_build_cmakedefs


        #self.suite_build_dir=args.suite_build_dir
        self.suite_build_polly=args.suite_build_polly
        self.suite_build_pollyprocessunprofitable=args.suite_build_polly_process_unprofitable
        self.suite_build_stats=args.suite_build_stats
        self.suite_build_mllvm=args.suite_build_mllvm
        self.suite_build_flags=args.suite_build_flags
        self.suite_build_libcxx=args.suite_build_libcxx
        self.suite_build_reproduce = args.suite_build_reproduce
        self.suite_build_reproduceall = args.suite_build_reproduce_all

        self.suite_exec_multisample = args.suite_exec_multisample

        return self


    def merge(self, other):
        for prop in self.scalar_props:
            val = getattr(self, prop, None)
            if val is None:
                setattr(self, prop, getattr(other, prop))

        for prop in self.list_props:
            selfval = getattr(self, prop, None)
            otherval = getattr(other, prop, None)
            if otherval is None:
                continue

            setattr(self, prop, empty_none(selfval) + empty_none(otherval))


    def get_cmdline(self):
        args = []

        if self.verbose:
            args += ['-v']
        if self.build_verbose:
            args += ['--build-verbose']
        if self.llvm_build_verbose:
            args += ['--llvm-build-verbose']
        if self.suite_build_verbose:
            args += ['--suite-build-verbose']
        if self.exec_verbose:
            args += ['--exec-verbose']
        if self.suite_exec_verbose:
            args += ['--suite-exec-verbose']

        if self.threads is not None:
            args += ['-j' + str(self.threads)]
        if self.build_threads is not None:
            args += ['--build-threads=' + str(self.build_threads)]
        if self.llvm_build_threads is not None:
            args += ['--llvm-build-threads=' + str(self.llvm_build_threads)]
        if self.suite_build_threads is not None:
            args += ['--suite-build-threads=' + str(self.suite_build_threads)]
        if self.exec_threads is not None:
            args += ['--exec-threads=' + str(self.exec_threads)]
        if self.suite_exec_threads is not None:
            args += ['--suite-exec-threads=' + str(self.suite_exec_threads)]
        if self.thread_limit is not None:
            args += ['--thread-limit=' + str(self.thread_limit)]

        if self.load is not None:
            args += ['--load' + str(self.load)]
        if self.build_load is not None:
            args += ['--build-load=' + str(self.build_load)]
        if self.llvm_build_load is not None:
            args += ['--llvm-build-load=' + str(self.llvm_build_load)]
        if self.suite_build_load is not None:
            args += ['--suite-build-load=' + str(self.suite_build_load)]
        if self.exec_load is not None:
            args += ['--exec-load=' + str(self.exec_load)]
        if self.suite_exec_load is not None:
            args += ['--suite-exec-load=' + str(self.suite_exec_load)]
        if self.load_limit is not None:
            args += ['--load-limit=' + str(self.load_limit) ]

        if self.revision is not None:
            args += ['--revision='+ revToStr( self.revision)]
        if self.llvm_revision is not None:
            args += ['--llvm-revision='+revToStr(self.llvm_revision)]
        if self.clang_revision is not None:
            args += ['--clang-revision='+revToStr(self.clang_revision)]
        if self.libcxxabi_revision is not None:
            args += ['--libcxxabi-revision='+revToStr(self.libcxxabi_revision)]
        if self.libcxx_revision is not None:
            args += ['--libcxx-revision='+revToStr(self.libcxx_revision)]
        if self.polly_revision is not None:
            args  += ['--polly-revision='+revToStr(self.polly_revision)]
        if self.suite_revision is not None:
            args += ['--suite-revision='+revToStr(self.suite_revision)]

        if self.suite_build_dir is not None:
            args += ['--suite-build-dir=' + self.suite_build_dir]

        for arg in empty_none(self.llvm_build_cmakeargs):
            args += ['--llvm-build-cmakeargs='+ arg]
        for d in empty_none(self.llvm_build_cmakedefs):
            args += ['--llvm-build-cmakedefs='+ d]

        for  testonly in empty_none(self.suite_testonly):
            args += ['--test-only='+ testonly]

        for arg in empty_none(self.suite_build_cmakeargs):
            args += ['--suite-build-cmakeargs='+ arg]
        for d in empty_none(self.suite_build_cmakedefs):
            args += ['--suite-build-cmakedefs='+ d]
        for flag in empty_none(self.suite_build_flags):
            args += ['--suite-build-flags='+ flag]
        for mllvm in empty_none( self.suite_build_mllvm):
            args += ['--suite-build-mllvm='+ mllvm]
        if self.suite_build_polly:
            args += ['--polly']
        if self.suite_build_pollyprocessunprofitable:
            args += ['--polly-process-unprofitable']
        if self.suite_build_stats:
            args += ['--stats']
        if self.suite_build_debug:
            args += ['--debug']
        for debugonly in empty_none(self.suite_build_debugonly):
            args += ['--debug-only='+ debugonly]
        if self.suite_build_reproduce:
            args += ['--reproduce']
        if self.suite_build_reproduceall:
            args += ['--reproduce-all']
        if self.suite_build_useperf:
            args += ['--use-perf']
        if self.suite_build_taskset:
            args += ['--taskset']
        if self.suite_build_libcxx:
            args += ['--libcxx']
        for cmakedef in  empty_none(self.suite_build_cmakedefs):
            args += ['--suite-build-cmakedefs='+ cmakedef]

        if self.suite_exec_taskset:
            args += ['--taskset']
        if self.suite_exec_multisample is not None:
            args += ['--multisample=' + str(self.suite_exec_multisample)]

        return args


    def get_llvm_build_verbose(self):
        return first_defined(self.llvm_build_verbose,self.verbose)

    def get_suite_build_verbose(self):
        return first_defined(self.suite_build_verbose,self.verbose)

    def get_suite_exec_verbose(self):
        return first_defined(self.suite_exec_verbose,self.verbose)


    def get_llvm_build_threads(self):
        return min_none(first_defined(self.llvm_build_threads,self.build_threads,self.threads), self.thread_limit)

    def get_llvm_build_load(self):
        return min_none(first_defined(self.llvm_build_load,self.build_load,self.load), self.load_limit)


    def get_suite_build_threads(self):
        return min_none(first_defined(self.suite_build_threads,self.build_threads,self.threads), self.thread_limit)

    def get_suite_build_load(self):
        return min_none(first_defined(self.suite_build_load,self.build_load,self.load), self.load_limit)


    def get_suite_exec_threads(self):
        return min_none(first_defined(self.suite_exec_threads,self.exec_threads,self.threads), self.thread_limit)

    def get_suite_exec_load(self):
        return min_none(first_defined(self.suite_exec_load,self.exec_load,self.load), self.load_limit)



    def get_llvm_source_dir(self):
        return self.llvm_source_dir

    def get_clang_source_dir(self):
        if self.llvm_source_dir is not None:
            return os.path.join(self.llvm_source_dir, 'tools', 'clang')
        return None

    def get_polly_source_dir(self):
        if self.polly_source_dir is not None:
            return self.polly_source_dir
        if self.llvm_source_dir is not None:
            return os.path.join(self.llvm_source_dir, 'tools', 'polly')
        return None

    def get_suite_source_dir(self):
        if self.llvm_source_dir is not None:
            return os.path.join(self.llvm_source_dir, 'projects', 'test-suite')
        return None

    def get_libcxxabi_source_dir(self):
        if self.llvm_source_dir is not None:
            return os.path.join(self.llvm_source_dir, 'projects', 'libcxxabi')
        return None

    def get_libcxx_source_dir(self):
        if self.llvm_source_dir is not None:
            return os.path.join(self.llvm_source_dir, 'projects', 'libcxx')
        return None


    def get_llvm_revision(self):
        return first_defined(self.llvm_revision, self.revision)

    def get_clang_revision(self):
        return first_defined(self.clang_revision, self.revision)

    def get_libcxxabi_revision(self):
        return first_defined(self.libcxxabi_revision, self.revision)

    def get_libcxx_revision(self):
        return first_defined(self.libcxx_revision, self.revision)

    def get_polly_revision(self):
        return first_defined(self.polly_revision, self.revision)

    def get_suite_revision(self):
        return first_defined(self.suite_revision, self.revision)


# Clean-up version of gittool_runtest, also to be used by execslave
# Feature wish-list:
# - Execute on remote machine
# - Store invoke command to file
def runtest(config,print_logs=False,enable_svn=True):
    tmpdir = tempfile.gettempdir()

    targets_to_build = {'clang', 'llvm-size'}
    enabled_projects = {'clang', 'polly', 'test-suite'}
    if config.suite_build_libcxx:
        targets_to_build |= {'cxx_shared'}
        enabled_projects |= {'libcxxabi', 'libcxx'}


    cores =  multiprocessing.cpu_count()


    llvm_source_dir = os.path.abspath(config.get_llvm_source_dir())
    llvm_build_dir = os.path.abspath(config.llvm_build_dir)
    suite_source_dir = os.path.abspath(config.get_suite_source_dir())
    suite_build_dir = config.suite_build_dir

    if suite_build_dir is None:
        suite_build_dir = tempfile.mkdtemp(prefix='runtest-',dir=tmpdir)
    suite_build_dir = os.path.abspath(suite_build_dir)





    if llvm_source_dir is not None:
        print("LLVM source      :", llvm_source_dir)
    print("LLVM build       :", llvm_build_dir)
    print("test-suite source:", suite_source_dir)
    print("test-suite build :", suite_build_dir)



    def llvm_checkout():
        onlychildren = {
            REVISION: first_defined(config.get_llvm_revision(), REV_KEEP)
        }
        if  'clang' in enabled_projects:
            onlychildren['clang'] =  first_defined(config.get_clang_revision(), REV_KEEP)
        if  'polly' in enabled_projects:
            if config.polly_source_dir is None:
                onlychildren['polly'] = first_defined(config.get_polly_revision(), REV_KEEP)
            else:
                onlychildren['polly'] = REV_KEEP # TODO: checkout at polly_source_dir location?!?
        if  'test-suite' in enabled_projects:
            onlychildren['test-suite'] = first_defined(config.get_suite_revision(), REV_KEEP)
        if  'libcxxabi' in enabled_projects:
            onlychildren['libcxxabi'] = first_defined(config.get_libcxxabi_revision(), REV_KEEP)
        if  'libcxx' in enabled_projects:
            onlychildren['libcxx'] = first_defined(config.get_libcxx_revision(), REV_KEEP)

        checkout_sub(llvm, llvm_source_dir, subdir=[], ismodule=False, onlychildren=onlychildren, unlisted=REV_KEEP, ignore_fetch_errors=True,enable_svn=enable_svn) # Or delete unlisted?

    if config.llvm_checkout:
        llvm_checkout()



    suite_testonly = config.suite_testonly
    conf_testonly = None
    build_testonly = None
    exec_testonly = None
    if suite_testonly is not None:
        # TODO: Check existence of directories
        known_all_subdirs_configurable = {'Polybench',  'External/SPEC/CINT2017rate', 'External/SPEC/CINT2017speed', 'External/SPEC/CFP2017rate', 'External/SPEC/CFP2017speed'}
        known_configurable = { 'Performance', 'Performance/Polybench-32', 'Performance/Polybench-421', 'Performance/Polybench-421-boost', 'Correctness', 'Correctness/Polybench-32', 'Correctness/Polybench-421',
                               'External', 'External/SPEC',
                               'SingleSource', # Sets 'traditional_output' and 'single_source' properties
                               'MultiSource' # Sets 'traditional_output' property
                               }
        conf_testonly = set()
        build_testonly = set()
        exec_testonly = set()

        def configurable_subdir(dir):
            for configurable in known_all_subdirs_configurable:
                if dir == configurable or dir.startswith(configurable + '/'):
                    return dir

            i = 0
            while True:
                parts = dir.rsplit('/',i)[0]
                if '/' not in parts or parts in known_configurable:
                    return parts
                i+=1


        # TODO: Ensure that if a dir is include, none of its subdirs are included
        for dir in suite_testonly:
            subdir = configurable_subdir(dir)
            fulldir = os.path.join(suite_source_dir, dir)
            if not os.path.isdir(fulldir):
                print("Warning: " + fulldir + " not in test-suite")
                raise Exception("Test '" + fulldir + "' not in test-suite")

            if not os.path.isfile(os.path.join(fulldir,'CMakeLists.txt')):
                print("Warning: " + fulldir + " has not CMakeLists.txt")
                raise Exception("No CMakeLists.txt in '" + fulldir + "'")

            conf_testonly.add(subdir)
            build_testonly.add(dir)
            exec_testonly.add(dir)


    if conf_testonly is not None:
        print("configure tests  :", ' '.join(conf_testonly))
    if build_testonly is not None:
        print("build tests      :", ' '.join(build_testonly))
    if exec_testonly is not None:
        print("run tests        :", ' '.join(exec_testonly))



    if print_logs and llvm_source_dir is not None:
        llvmrep = Repository2.from_directory(llvm_source_dir)
        print("LLVM log:\n{msg}\n".format(msg=llvmrep.get_head().get_message()))

        if 'clang' in enabled_projects:
            clangrep = Repository2.from_directory(config.get_clang_source_dir())
            print("Clang log:\n{msg}\n".format(msg=clangrep.get_head().get_message()))

        if 'polly' in enabled_projects:
            pollyrep = Repository2.from_directory(config.get_polly_source_dir())
            print("Polly log:\n{msg}\n".format(msg=pollyrep.get_head().get_message()))

        if 'test-suite' in enabled_projects:
            suiterep = Repository2.from_directory(config.get_suite_source_dir())
            print("test-suite log:\n{msg}\n".format(msg=suiterep.get_head().get_message()))

        if 'libcxxabi' in enabled_projects:
            libcxxabirep = Repository2.from_directory(config.get_libcxxabi_source_dir())
            print("libcxxabi log:\n{msg}\n".format(msg=libcxxabirep.get_head().get_message()))

        if 'libcxx' in enabled_projects:
            libcxxrep = Repository2.from_directory(config.get_libcxx_source_dir())
            print("libcxx log:\n{msg}\n".format(msg=libcxxrep.get_head().get_message()))



    def llvm_configure():
        os.makedirs(llvm_build_dir, exist_ok=True)
        cmakeopts = ['-GNinja', '-DCMAKE_BUILD_TYPE=Release'] # '-DLLVM_PARALLEL_LINK_JOBS=1',

        defs = []
        cppflags = []
        cflags = []
        cxxflags = []

        if config.suite_build_stats:
            defs +=['LLVM_ENABLE_STATS=ON']
        # else... off?

        for d in defs:
            cppflags += ['-D'+d]

        if config.llvm_build_flags is not None:
            cppflags += config.llvm_build_flags

        cflags += cppflags
        cxxflags += cppflags
        if cflags:
            cmakeopts += ['-DCMAKE_C_FLAGS=' + shquote(cflags)]
        if cxxflags:
            cmakeopts += ['-DCMAKE_CXX_FLAGS=' + shquote(cxxflags)]

        if config.polly_source_dir is not None:
            cmakeopts += ['-DLLVM_TOOL_POLLY_BUILD=ON',  '-DLLVM_POLLY_BUILD=ON', '-DLLVM_EXTERNAL_POLLY_SOURCE_DIR=' + config.polly_source_dir]
        # else ... off?

        cmakeopts += empty_none(config.llvm_build_cmakeargs)
        for d in empty_none(config.llvm_build_cmakedefs):
            if d.startswith('-D'):
                cmakeopts += [d]
            else:
                cmakeopts += ['-D' + d]

        # TODO: Build only subprojects in enabled_projects
        invoke('cmake', llvm_source_dir, *cmakeopts, cwd=llvm_build_dir)

    if config.llvm_configure:
        llvm_configure()



    def llvm_build():
        ninjaopts = []

        llvm_build_threads = config.get_llvm_build_threads()
        if llvm_build_threads is not None:
            ninjaopts  += ['-j{0}'.format(llvm_build_threads)]

        llvm_build_load = config.get_llvm_build_load()
        if llvm_build_load is not None:
            ninjaopts  += ['-l{0}'.format(llvm_build_load*cores)]

        if config.get_llvm_build_verbose():
            ninjaopts  += ['-v']

        ninjaopts += targets_to_build
        invoke('ninja', *ninjaopts, cwd=llvm_build_dir)

    llvm_build()






    def get_lit_args(i=None):
        litopts = []

        suite_exec_threads = config.get_suite_exec_threads()
        suite_exec_load = config.get_suite_exec_load()
        if suite_exec_load is not None:
            suite_exec_threads = min_none(suite_exec_threads, max_none(int(cores*suite_exec_load), 1))

        if suite_exec_threads is not None:
            litopts += ['-j' + str(suite_exec_threads)]

        if config.get_suite_exec_verbose():
            litopts += ['-v'] # "Show test output for failures"
        else:
            # --help desc: "Reduce amount of output"
            # Actually disables printing the metrics
            litopts += ['-s']

        if config.suite_exec_multisample is None or i is None:
            litopts += ['-o', os.path.join(suite_build_dir,'output.json')]
        else:
            litopts += ['-o', os.path.join(suite_build_dir,'output-{i}.json'.format(i=i))]

        if exec_testonly is None:
            litopts += ['.']
        else:
            litopts += exec_testonly
        return litopts




    def suite_configure():
        os.makedirs(suite_build_dir, exist_ok=True)

        cmakedefs = []
        cmakeopts = []

        cc = 'cc'
        cxx = 'c++'
        if llvm_build_dir is not None:
            cc = first_existing(os.path.join(llvm_build_dir, 'bin', 'clang-cl.exe'), os.path.join(llvm_build_dir, 'bin', 'clang'))
            cxx = first_existing(os.path.join(llvm_build_dir, 'bin', 'clang-cl.exe'), os.path.join(llvm_build_dir, 'bin', 'clang++'))


        if config.suite_build_reproduce or config.suite_build_reproduceall:
            reduceccfilepath = os.path.join(suite_build_dir,'cc')
            reproduce_args = ['--no-build', '--as-if', '--write-test', '--preprocess-includes', '--cc1']
            if config.suite_build_reproduceall:
                reproduce_args.append('--even-successful')

            with open(reduceccfilepath,'w+') as f:
                f.write('#! /bin/bash\n')
                f.write('python3 {script} reproduce {args} -- {clang} "$@"\n'.format(script=script,clang=cc,args=' '.join(reproduce_args)))
            os.chmod(reduceccfilepath, 0o755)

            reducdecxxfilepath = os.path.join(suite_build_dir,'c++')
            with open(reducdecxxfilepath,'w+') as f:
                f.write('#! /bin/bash\n')
                f.write('python3 {script} reproduce {args} -- {clangxx} "$@"\n'.format(script=script,clangxx=cxx,args=' '.join(reproduce_args)))
            os.chmod(reducdecxxfilepath, 0o755)

            cc = reduceccfilepath
            cxx = reducdecxxfilepath


        if cc is not None:
            cmakedefs += ['CMAKE_C_COMPILER=' + cc.replace('\\', '/') ]
        if cxx is not None:
            cmakedefs += ['CMAKE_CXX_COMPILER=' + cxx.replace('\\', '/') ]

        if conf_testonly is not None:
            cmakedefs += ['TEST_SUITE_SUBDIRS=' +';'.join(conf_testonly)]
        cmakedefs += ['CMAKE_BUILD_TYPE=Release']
        cmakedefs += ['TEST_SUITE_LLVM_SIZE=' + os.path.join(llvm_build_dir,'bin','llvm-size')]
        lit_prog = os.path.join(llvm_build_dir,'bin','llvm-lit')
        cmakedefs += ['TEST_SUITE_LIT=' + lit_prog]

        if config.suite_build_stats:
            cmakedefs += ['TEST_SUITE_COLLECT_STATS=ON']

        cppflags = []
        cflags = []
        cxxflags = []

        if config. suite_build_libcxx:
            cxxflags += ['-stdlib=libc++']
            cxxflags += ['-L', os.path.join(llvm_build_dir,'lib')]
        if config.suite_build_polly or config.suite_build_pollyprocessunprofitable:
            cppflags   += ['-mllvm', '-polly']
        if config.suite_build_pollyprocessunprofitable:
            cppflags   += ['-mllvm', '-polly-process-unprofitable']
        if config.suite_build_flags is not None:
            cppflags   += config.suite_build_flags
        if config.suite_build_mllvm is not None:
            for mllvm in config.suite_build_mllvm:
                cppflags   += ['-mllvm', mllvm]

        cflags += cppflags
        cxxflags += cppflags
        if cflags:
            cmakedefs += ['CMAKE_C_FLAGS=' + ' '.join(cflags)]
        if cxxflags:
            cmakedefs += ['CMAKE_CXX_FLAGS=' + ' '.join(cxxflags)]


        if config.suite_build_useperf:
            cmakedefs += ['TEST_SUITE_USE_PERF=ON']
        if config.suite_build_taskset:
            cmakedefs += ['TEST_SUITE_RUN_UNDER=taskset -c1']

        litopts = get_lit_args()
        cmakedefs += ['TEST_SUITE_LIT_FLAGS=' +  ';'.join(litopts)]

        cmakeopts += empty_none(config.suite_build_cmakeargs)
        for d in empty_none(config.suite_build_cmakedefs):
            if d.startswith('-D'):
                cmakeopts += [d]
            else:
                cmakeopts += ['-D' + d]

        for d in cmakedefs:
            cmakeopts += ['-D' + d]

        invoke('cmake', suite_source_dir, '-GNinja', *cmakeopts, cwd=suite_build_dir)

    suite_configure()




    def suite_build():
        ninjaopts=[]

        suite_build_threads = config.get_suite_build_threads()
        if suite_build_threads is not None:
            ninjaopts += ['-j' + str(suite_build_threads)]

        suite_build_load = config.get_suite_build_load()
        if suite_build_load is not None:
            ninjaopts  += ['-l{0}'.format(suite_build_load*cores)]

        if config.get_suite_build_verbose():
            ninjaopts  += ['-v']

        ninjaopts += ['-k0'] # Do not fail on build errors, we'll still run those that were built.

        if build_testonly is not None:
            ninjaopts += [s + '/all' for s in build_testonly]

        invoke('ninja', *ninjaopts, cwd=suite_build_dir, resumeonerror=True)

    suite_build()



    def suite_run():
        llvmlit_prog = first_existing(os.path.join(llvm_build_dir, 'bin', 'llvm-lit.py'), os.path.join(llvm_build_dir, 'bin', 'llvm-lit'))

        litappendenv = dict()
        if config.suite_build_libcxx:
            litappendenv['LD_LIBRARY_PATH'] = os.path.join(llvm_build_dir,'lib')

        count = config.suite_exec_multisample
        if count is None:
            count = 1

        for i in range(count):
            print("Run:",i+1,"of",count)
            litopts = get_lit_args(i=i)
            invoke('python3', llvmlit_prog, *litopts, cwd=suite_build_dir,appendenv=litappendenv)

    suite_run()

    print("test-suite build dir:",suite_build_dir)



def gittool_buildbot(rep,builder,password, comment='', patches=None, revision=None):
    if revision:
        svnrev = revision
        svncommit = rep.svn.find_commit(revision)
    else:
        svncommit,svnrev = find_lastsvn(rep)


    revdesc = rep.describe(svncommit,all=True)
    if revision:
        fullcomment = "[r{svnrev} {revdesc}+{patches}] {comment}".format(svnrev=svnrev,revdesc=revdesc,comment=comment,patches=' '.join(patches) if patches else '')
    else:
        HEADcommit = rep.get_head().sha1
        HEADdesc = rep.describe(all=True)
        fullcomment = "[r{svnrev} {revdesc} ---> {headdesc} {headsh1a}+{patches}] {comment}".format(svnrev=svnrev,revdesc=revdesc,headdesc=HEADdesc,headsh1a=HEADcommit,comment=comment,patches=' '.join(patches) if patches else '')

    if patches or revision:
        with rep.preserve():
            if revision:
                rep.reset(svncommit,index=True,workdir=True)
            else:
                #rep.add_all()
                rep.add_update()
                rep.commit(message="Leftover changes", allow_empty=True)
            if patches:
                for patch in patches:
                    if os.path.isfile(patch):
                        with open(patch, 'r') as f:
                            invoke('patch', '-p1', stdin=f)
                    else:
                        rep.merge(patch,noedit=True)
            diff = rep.diff(svncommit)
    else:
        diff = rep.diff(svncommit)

    print("Diff has {lines} lines, {len} chars".format(lines=diff.count('\n') + 1,len=len(diff)))
    invoke('buildbot', 'try', '--connect=pb', '--master', 'gcc12.fsffrance.org:8031', '--builder={builder}'.format(builder=builder),
           '--username=meinersbur', '--passwd=' + password, '--who=Michael Kruse',
           '-p1', '--diff=-', '--baserev={svnrev}'.format(svnrev=svnrev), '--comment=' + fullcomment,stdin=diff)


def createfile(filename,contents):
    with open(filename, 'w+')as f:
        f.write(contents)

def create_testdir():
    repdir = tempfile.mkdtemp(prefix='gittool-selftest ')
    rep = Repository2.init(repdir)
    rep.invoke_git('config', 'user.email', 'selftest@meinersbur.de')

    createfile(os.path.join(repdir, '.gitignore'), "/ignoredfile\n")
    createfile(os.path.join(repdir, 'ignoredfile'), "Ignored content")

    createfile(os.path.join(repdir, 'firstfile'), "Initial content")
    createfile(os.path.join(repdir, 'workfile'), "Initial content")
    createfile(os.path.join(repdir, 'indexfile'), "Initial content")
    rep.add(all=True)
    rep.commit("Init")

    createfile(os.path.join(repdir, 'workfile'), "Changed content")
    rep.add(update=True)
    rep.commit("Change/HEAD")

    createfile(os.path.join(repdir, 'indexfile'), "Index content")
    createfile(os.path.join(repdir, 'workfile'), "Index content")
    rep.add(update=True)

    createfile(os.path.join(repdir, 'workfile'), "Workingset content")
    createfile(os.path.join(repdir, 'newfile'), "New content")

    return rep


def expectfile(filename,expected_contents):
    with open(filename, 'r') as f:
        actual_contents = f.read()
        if actual_contents != expected_contents:
            raise Exception("File {0}: Expected '{1}' but found '{2}'".format(filename,expected_contents,actual_contents))

def expectnofile(filename):
    if os.path.exists(filename):
        raise Exception("File {0}: Should not exist".format(filename))


def verify_testdir(rep):
    repdir = rep.workdir
    expectfile(os.path.join(repdir,'.gitignore'), "/ignoredfile\n")
    expectfile(os.path.join(repdir,'ignoredfile'), "Ignored content")
    expectfile(os.path.join(repdir,'firstfile'), "Initial content")
    expectfile(os.path.join(repdir,'indexfile'), "Index content")
    expectfile(os.path.join(repdir,'workfile'), "Workingset content")
    expectfile(os.path.join(repdir,'newfile'), "New content")


def gittool_sendmail(rep,since,commit=None,reroll_count=None):
    tmpdir = tempfile.mkdtemp(prefix='gitsendemail-')
    if commit is None:
        revlist = since
    else:
        revlist = str(since) + '..' + str(commit)
    rep.format_patch(revlist,signoff=True,reroll_count=reroll_count,output_directory=tmpdir)

    patches = os.listdir(path=tmpdir)
    print("Found {len} patches:".format(len=len(patches)))
    for patch in patches:
        print('  ' + patch)

    print()
    print("Sending test mail...")
    rep.send_email(files=[os.path.join(tmpdir,patch) for patch in patches],fromaddr='Michael Kruse <isl@meinersbur.de>',toaddr='testcommit@meinersbur.de',confirm='never')

    isok = input("Was the email OK? [y/N]")
    if isok == 'y' or isok == 'Y':
        print("Sending the mail...")
        rep.send_email(files=[os.path.join(tmpdir,patch) for patch in patches],fromaddr='Michael Kruse <isl@meinersbur.de>',toaddr='isl-development@googlegroups.com',confirm='never')


class Execjob:
    def __init__(self,slavename,configname,
                      srchead,dstname,dsthead):
        # Global
        self.slavename = slavename
        self.configname = configname

        # This job
        #self.workdir = workdir
        #self.persistentdir = persistentdir
        self.srchead = srchead
        self.dstname = dstname
        self.dsthead = dsthead

        # Job status
        self.jobid = None
        self.n = None

    def execute(self,workdir,persistentdir,source=None,target=None):
        execjob(slavename=self.slavename,configname=self.configname,workdir=workdir, persistentdir=persistentdir, srchead=self.srchead,dsthead=self.dsthead,dstname=self.dstname,source=source,target=target)



# Executes on the node
def gittool_execjob(workdir,persistentdir,source,target,slavename,configname,srchead,dstname,dsthead):
    job = Execjob(configname=configname,srchead=srchead,dstname=dstname,dsthead=dsthead,slavename=slavename)
    job.execute(workdir=workdir,persistentdir=persistentdir,source=source,target=target)




def execjob(slavename,configname,workdir,persistentdir,srchead,dsthead,dstname,source=None,target=None):
    if os.path.exists(os.path.join(workdir, '.git')):
        rep = Repository2.from_directory(workdir)
    else:
        rep = Repository2.init(workdir)
        rep.invoke_git('config', 'user.email', 'execslave@meinersbur.de')
        rep.invoke_git('config', 'pack.compression', '9')

    with TemporaryDirectory(prefix='slavemsg-') as msgtmpdir, contextlib.ExitStack() as stack:
        if persistentdir is None:
            persistentdir = stack.enter_context(TemporaryDirectory(prefix='persistent-'))

        os.makedirs(persistentdir, exist_ok=True)

        if source is not None:
            sourceremote = rep.create_remote('source',source,resumeonerror=True)
            sourceremote.set_url(source)
            sourceremote.fetch(prune=True)

        targetremote = None
        if target is not None:
            targetremote = rep.create_remote('target',target,resumeonerror=True)
            targetremote.set_url(target)
            targetremote.fetch(prune=True)

        if srchead is None:
            srchead = rep.get_head()

        srchead = rep.get_commit(srchead)
        srcsha1 = srchead.get_sha1()
        srcbody = srchead.get_message(body=True)
        srcmessage = srchead.get_message(title=True,body=True)
        mcmd = re.search(r'^Exec\s*\:\s*(?P<cmd>.*)', srcbody, re.MULTILINE)

        if not mcmd:
            raise Exception("Commit does not contain Exec: command")


        msgfile = os.path.join(msgtmpdir, 'message.txt')
        reportfile = os.path.join(workdir, 'report.txt')
        stdoutfile = os.path.join(workdir, 'stdout.txt')
        stderrfile = os.path.join(workdir, 'stderr.txt')
        outputfile = os.path.join(workdir, 'output.txt')

        # Get pristine workdir
        rep.checkout(srchead,detach=True,force=True)

        # Remove leftovers
        rep.reset(index=True,workdir=True)
        rep.clean(x=True, d=True, force=True)

        if dsthead is not None:
            rep.merge(dsthead, noedit=True, strategy='ours', nocommit=True)


        cmd = shlex.split(mcmd.group('cmd'))
        exe = os.path.join(workdir, cmd[0])
        if not os.path.isfile(exe):
            exe = cmd[0]
        args = cmd[1:]

        with open(msgfile, 'x') as file:
            file.write(srcmessage)

        addenv = { 'persistentdir': persistentdir, 'messagefile': msgfile }

        print_command(exe, *args, cwd=workdir, addenv=addenv)
        env = assemble_env(addenv=addenv)

        print('###############################################################################')
        print('###############################################################################',file=sys.stderr)
        start = datetime.datetime.now()

        errmsg = None
        rtncode = None
        try:
            p = subprocess.Popen([exe] + [str(s) for s in args],cwd=workdir,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,bufsize = 1)
        except Exception as err:
            errmsg = "Exception thrown: {err}".format(err=err)
        else:
            def catch_std(out, outhandles, jointouthandles, prefix):
                while True:
                    line = out.readline()
                    if len(line) == 0:
                        break
                    for h in outhandles:
                        h.write(line)
                    for h in jointouthandles:
                        h.write(prefix + line)

            with open(stdoutfile,'w') as stdouth, open(stderrfile, 'w') as stderrh, open(outputfile, 'w') as outh:
                tout = threading.Thread(target=catch_std, args=(p.stdout, {stdouth,sys.stdout},{outh},'[stdout] '))
                tout.daemon = True
                tout.start()

                terr = threading.Thread(target=catch_std, args=(p.stderr, {stderrh,sys.stderr},{outh}, '[stderr] '))
                terr.daemon = True
                terr.start()

                rtncode = p.wait()
                tout.join()
                p.stdout.close()
                terr.join()
                p.stderr.close()





        stop = datetime.datetime.now()
        print('###############################################################################')
        print('###############################################################################',file=sys.stderr)


        with open(msgfile, 'r') as file:
            dstmessgagelines = [line.rstrip('\r\n') for line in file.readlines()]

        titleline = dstmessgagelines[0]
        pos = 0
        nontags = 0
        while True:
            if pos >= len(titleline):
                break
            if titleline[pos] == '[':
                while True:
                    if pos >= len(titleline):
                        break
                    if titleline[pos] == ']':
                        pos+=1
                        nontags = pos
                        break
                    pos += 1
                continue
            if not titleline[pos].isspace():
                break
            pos += 1
        tags = titleline[0:nontags]
        title = titleline[pos:]

        bodylines = dstmessgagelines[1:]
        trim_emptylines(bodylines)
        body = '\n'.join(bodylines)

        plat = platform.platform()
        processor = platform.processor()
        osys = platform.system()
        if not slavename:
            slavename = platform.node()
        success = "SUCCESS" if rtncode == 0 else "FAIL"
        formatspec = dict(errmsg=errmsg,title=title,tags=tags,success=success,body=body,srcsha=srcsha1,hostname=slavename,processor=processor,start=start,duration=stop - start,os=osys,platform=plat,exitcode=rtncode,configname=configname)

        report = []
        report.append("Start: {start}")
        report.append("Duration: {duration}")
        if rtncode is not None:
            report.append("Exit-code: {exitcode}")
        if errmsg is not None:
            report.append("Error: {errmsg}")
        report.append("")
        #report.append("OS: {os}")
        report.append("Platform: {platform}")
        report.append("Processor: {processor}")
        report = '\n'.join(report).format(**formatspec)


        message = ["[{hostname} ({success})]{tags} {title}"]
        message.append("")
        message.append("{body}")
        message.append("")
        message.append("From-source: {srcsha}")
        if configname is not None:
            message.append("Config-name: {configname}")
        message.append("")
        message.append("{report}")
        message = '\n'.join(message).format(report=report, **formatspec)

        with open(reportfile, 'w') as file:
            file.write(report)

        rep.add_all()
        rep.commit(message)
        rep.checkout(overwritebranch=dstname)
        rep.gc(resumeonerror=True) # Avoid that too much clutter accumulates
        if targetremote is not None:
            targetremote.push(dstname,force=True)


testmode = (os.name == 'nt')


def gittool_execslave(workdir, source, target, persistentdir,slavename,waitsecs=datetime.timedelta(minutes=5),onlyone=False,configname=None,onlyjob=None,watch=True,parallel=1,slurm=False,dry=False,push=True):
    multiwork = parallel != 1 or slurm
    if multiwork:
        repdir = os.path.join(workdir, 'rep')
    else:
        repdir = workdir


    if os.path.exists(os.path.join(repdir, '.git')):
        rep = Repository2.from_directory(repdir)
    else:
        rep = Repository2.init(repdir)
        rep.invoke_git('config', 'user.email', 'execslave@meinersbur.de')
        rep.invoke_git('config', 'pack.compression', '9')

    os.makedirs(persistentdir, exist_ok=True)


    sourceremote = rep.create_remote('source',source,resumeonerror=True)
    sourceremote.set_url(source)

    targetremote = rep.create_remote('target',target,resumeonerror=True)
    targetremote.set_url(target)

    processing = set()
    processedbranches = set()

    def execjob(job,jobworkdir,jobpersistentdir,srcbranch,n=None):
        nonlocal activejobs,workdir

        jobworkdir = os.path.abspath(jobworkdir)
        jobpersistentdir = os.path.abspath(jobpersistentdir)

        os.makedirs(jobworkdir,exist_ok=True)
        os.makedirs(persistentdir,exist_ok=True)

        if srcbranch is not None:
            srcbranchname = srcbranch.get_basename()

        if slurm:
            if n is None:
                tmpdir = tempfile.mkdtemp(prefix='job-')
                jobname = 'node_' + str(job.srchead)
            else:
                i = 0
                while True:
                        tmpdir = os.path.join(os.path.abspath(workdir), 'work' + str(n) + '_' + str(i))
                        jobname = srcbranchname + '_' + str(n) + '_' + str(i)
                        if not os.path.exists(tmpdir):
                           break
                        i += 1
                os.makedirs(tmpdir,exist_ok=True)

            jobfile = os.path.join(tmpdir,'job.sh')
            jobfile = os.path.abspath(jobfile)
            outfile = os.path.join(tmpdir,'job.out')
            outfile = os.path.abspath(outfile)
            errfile = os.path.join(tmpdir,'job.err')
            errfile = os.path.abspath(errfile)

            execjobargs = [script, 'execjob', '--workdir',jobworkdir,'--persistentdir', jobpersistentdir,
                                              '--slavename',job.slavename, '--srchead', str(job.srchead), '--dstname',job.dstname]
            if job.configname is not None:
                execjobargs +=['--configname',job.configname]
            if source is not None:
                execjobargs += ['--source',source]
            if target is not None and push:
                execjobargs += ['--target',target]
            if job.dsthead is not None:
                execjobargs += ['--dsthead', str(job.dsthead)]
            #if not push:
            #    execjobargs += ['--no-push']
            execjobcmd = shjoin(execjobargs)

            with open(jobfile, 'w+') as f:
                s = """#! /bin/bash -l
#SBATCH --job-name={jobname}
#SBATCH --mail-type=END,FAIL,REQUEUE,STAGE_OUT
#SBATCH --mail-user=cscs@meinersbur.de
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --output {outfile}
#SBATCH --error {errfile}

eval `ssh-agent -s`
trap 'ssh-agent -k' EXIT
ssh-add ~/.ssh/id_rsa_self

python3 {execjobcmd}

""".format(jobname=jobname,outfile=outfile,errfile=errfile,execjobcmd=execjobcmd)
                f.write(s)

            print("Comitting job",
                  "n=",n,
                  "jobworkdir=",jobworkdir,
                  "tmpdir=",tmpdir,
                  "branch=",srcbranchname)
            if testmode:
                with open(outfile, 'w+') as f:
                    f.write("Dummy output")
                stdout = "Submitted batch job 101381\n"
            else:
                _,_,stdout,_ = invoke('sbatch', jobfile, '--export=ALL',
                       return_stdout=True,cwd=jobworkdir)



            m = re.search(r'Submitted\s+batch\s+job\s+(?P<jobid>\d+)', stdout)
            job.jobid = int(m.group('jobid'))
            job.n = n
            print("Jobid is",job.jobid)

            # Wait until outfile appears, so we know job has started
            print("Waiting until job is starting...")
            while not os.path.exists(outfile):
                time.sleep(datetime.timedelta(seconds=2).total_seconds())
            print("Job started! Starting more jobs...")
        else:
            job.execute(workdir=jobworkdir,persistentdir=jobpersistentdir,source=source,target=target if push else None)

        activejobs.add(job)


    totalnumbers = 0
    numberpool = queue.PriorityQueue()

    jobqueue = queue.Queue()
    jobsdone = queue.Queue()

    activejobs = set()

    def work_once():
        job = jobqueue.get()
        if job is not None:
            n = numberpool.get()
            jobworkdir = os.path.join(workdir,'work'+str(n))
            jobpersistentdir = os.path.join(persistentdir,'persistent' + str(n))

            execjob(job,jobworkdir=jobworkdir,jobpersistentdir=jobpersistentdir,n=n)

            numberpool.put(n)
            jobsdone.put(job)

        jobqueue.task_done()
        return job is None


    def cleanup_done():
        nonlocal activejobs,numberpool

        if not slurm :
            return

        if testmode:
            stdout = """100733
100732
100731
100730
100729
100845
100825
100718
101354
101351
101336
101335
101334
101333
101330
101325
101096
101142
100257
101126
101098
100928
100881
100824
100783
100827
100823
101326
101094
101285
101377
101352
101306
101296
101284
"""
        else:
            _,_,stdout,_ = invoke('squeue',
                                    '-h', #  No header
                                    '-o', '%A', # Print just the jobid
                                    return_stdout=True)
        stillactivejobids = set(int(s) for s in stdout.splitlines())
        stillactivejobs = set(job for job in activejobs if job.jobid in stillactivejobids)
        donejobs = activejobs.difference(stillactivejobs)
        activejobs = stillactivejobs
        usednumbers = set(int(job.n) for job in activejobs)
        numberpool = queue.PriorityQueue()
        for n in set(range(len(usednumbers)+1)).difference(usednumbers):
            numberpool.put_nowait(n)
        for donejob in donejobs:
            processing.remove(str(donejob.srchead)) # Keep in there, to avoid repeated queuing if something fails?
            processedbranches.remove(str(donejob.dstname))

        if donejobs:
            print(str(len(activejobs)), "jobs finished",file=sys.stderr)
        if activejobs:
            print(str(len(activejobs)), "jobs still running",file=sys.stderr)


    def getfirstnum():
        return numberpool.get_nowait()

    if slurm:
        FirstRound = False
        while True:
            if testmode:
                stdout = '\n'
            else:
                _,_,stdout,_ = invoke('squeue',
                                        '-h', #  No header
                                        '-o', '%A', # Print just the jobid
                                        '-u', os.getlogin(), # Only current user
                                        return_stdout=True)
            if stdout and not stdout.isspace():
                if FirstRound:
                    print("You have active jobs that might interfere with the work and/or persistent dir",file=sys.stderr)
                    print("Waiting for them to finish...",file=sys.stderr)
                FirstRound = False
                time.sleep(10)
            else:
                break

        if not FirstRound :
            print("No more use jobs, continuing...",file=sys.stderr)




    # Start new thread for each job
    def worker(keepalive):
        while True:
            abort = work_once()
            if abort or not keepalive:
                break


    # TODO: Instead of starting all at the beginning, is it possible to find out whether all are busy and then start an new thread; would make the parallel!=1 case equal
    if parallel > 1:
        for i in range(parallel):
            t = threading.Thread(target=worker,args=(True,))
            t.start()



    def lookforjobs():
        nonlocal totalnumbers

        while True:
            if not testmode:
                sourceremote.fetch(prune=True)
            srcbranches = sourceremote.branches()

            if not testmode:
                targetremote.fetch(prune=True)


            if False:
                # Cleanup jobsdone, remove jobs from processed that have not been pushed to run again
                try:
                    while True:
                        job = jobsdone.get_nowait()
                        processing.remove(job.srchead)
                except queue.Empty:
                    pass

            foundany = False
            for srcbranch in srcbranches:
                if (onlyjob is not None) and (onlyjob!=srcbranch.get_basename()):
                    continue

                name = srcbranch.get_basename()
                dstname = "{hostname}_{srcname}".format(hostname=slavename,srcname=name)
                if dstname in processedbranches:
                    continue
                srchead = srcbranch.get_head()

                srcsha1 = srchead.get_sha1()
                if srcsha1 in processing:
                    continue


                srctitle = srchead.get_message(title=True)
                srcbody = srchead.get_message(body=True)
                mcmd = re.search(r'^Exec\s*\:\s*(?P<cmd>.*)', srcbody, re.MULTILINE)
                if not mcmd:
                    print("Missing exec source: {src} {title}".format(title=srctitle,src=srcsha1), file=sys.stderr)
                    continue

                dstbranch = targetremote.get_branch(dstname)
                dsthead = None
                if dstbranch.exists():
                    dsthead = dstbranch.get_head()

                    dstbody = dsthead.get_message(body=True)
                    msource = re.search(r'^From-source\s*\:\s*(?P<sha1>[a-fA-F0-9]+)', dstbody, re.MULTILINE)
                    mconfig = re.search(r'^Config-name\s*\:\s*(?P<config>[a-fA-F0-9]+)', dstbody, re.MULTILINE)
                    dstconfigname = mconfig.group('config') if mconfig else None

                    if msource:
                        msha1 = msource.group('sha1')
                        if srcsha1 == msha1:
                            if configname is not None and dstconfigname != configname:
                                print("Executing again by {hostname}, because of different config ('{dstconfigname}'!='{configname}'): {name} {src} {title}".format(hostname=slavename,title=srctitle,src=srcsha1,name=name,configname=configname,dstconfigname=dstconfigname), file=sys.stderr)
                            else:
                                print("Already executed by {hostname}: {name} {src} {title}".format(hostname=slavename,title=srctitle,src=srcsha1,name=name), file=sys.stderr)
                                #processed.add(srcsha1)
                                continue

                # We decided that it is necessary to execute
                foundany = True

                cleanup_done()

                job = Execjob(slavename=slavename,configname=configname,srchead=srchead,dstname=dstname,dsthead=dsthead)
                processing.add(str(srcsha1))
                processedbranches.add(str(dstname))

                if slurm:
                    n = getfirstnum()
                    jobworkdir = os.path.join(workdir,'work' + str(n))
                    jobpersistentdir = os.path.join(persistentdir,'persistent' + str(n))
                    execjob(job,jobworkdir=jobworkdir,jobpersistentdir=jobpersistentdir,n=n,srcbranch=srcbranch)
                elif parallel == 1:
                    #job.execute(workdir,persistentdir)
                    execjob(job,jobworkdir=workdir,jobpersistentdir=persistentdir,srcbranch=srcbranch)
                else:
                    # Ensure that we always have enough numbers, but prefer reusing existing work/persistendir
                    numberpool.put(totalnumbers)
                    totalnumbers+=1

                    jobqueue.put(job)

                    if parallel == 0:
                        t = threading.Thread(target=worker,args=(False,))
                        t.start()



                # Exit execslave after one job
                if onlyone:
                    return

                # re-read branches to get only the latest jobs (and-restart
                # from first if it has changed)
                break

            if not foundany:
                if not watch:
                    print("No additional job found. exiting...")
                    return
                print("No more job found; waiting {waitsecs} seconds before looking for new job".format(waitsecs=waitsecs))
                time.sleep(waitsecs.total_seconds())

    lookforjobs()

    if parallel > 1:
        for i in range(parallel):
            jobqueue.put(None) # Signal to threat to exit

        jobqueue.join()


def parseRev(str, default=None, allow_sentinels=False):
    if str is None:
        return default
    if isinstance(str,int):
        return str # Already an SVN revision number
    if allow_sentinels and (str is REV_KEEP or str is REV_DELETE or str is REV_MERGE_HEAD or str is REV_HEAD):
        return str
    str = str.strip()
    if len(str) == 0:
        return default
    if str[0] == 'r' and str[1:].isdigit():
        return int(str[1:])
    return str # git SHA1


def revToStr(rev):
    if rev is None:
        return ''
    if isinstance(rev, int):
        return 'r{rev}'.format(rev=rev)
    return rev


def gittool_makejob(config, jobname, rep, comment, testrun=False,invocation=None):
    # max_procs=threads
    workdir = rep.workdir

    #if revision is not None:
    #    svnrev = revision
    #    svncommit = rep.svn.find_commit(revision,before=True)
    #else:
    #    svncommit,svnrev = find_lastsvn(rep)



    #testsuiterev = revToStr(testsuiterevision)
    #lntrev = revToStr(lntrev)
    #llvmrev = revToStr(llvmrevision)

    with rep.preserve() as state:
        if config.polly_revision is None:
            pollyrev = state.UNADDEDcommit.get_sha1()
        else:
            pollyrev = parseRev(config.polly_revision)

        if isinstance(pollyrev,int):
            svnrev = pollyrev
            svncommit =  rep.svn.find_commit(svnrev)
            pollycommit = svncommit
        else:
            svncommit,svnrev = find_lastsvn(rep,commit=config.polly_revision)
            pollycommit = rep.get_commit(pollyrev)


        llvmrev = config.get_llvm_revision()
        llvmrep = Repository2.from_directory(os.path.join(homedir,'src','llvm'))
        llvmcommit = llvmrep.get_head() if llvmrev is None else llvmrep.find_commit(llvmrev)
        config.llvm_revision = llvmcommit.get_sha1()

        clangrev = config.get_clang_revision()
        clangrep = Repository2.from_directory( os.path.join(homedir,'src','llvm','tools','clang'))
        clangcommit = clangrep.get_head() if clangrev is None else clangrep.find_commit(clangrev)
        config.clang_revision = clangcommit.get_sha1()

        suiterev = config.get_suite_revision()
        suiterep = Repository2.from_directory(os.path.join(homedir,'src','llvm','projects','test-suite'))
        suitecommit = suiterep.get_head() if suiterev is None else  suiterep.find_commit(suiterev)
        config.suite_revision = suitecommit.get_sha1()

        #if config.suite_build_libcxx:
        if True:
            libcxxabirev = config.get_libcxxabi_revision()
            libcxxabirep =Repository2.from_directory(os.path.join(homedir,'src','llvm', 'projects', 'libcxxabi'))
            libcxxabicommit = libcxxabirep.get_head() if libcxxabirev is None else libcxxabirep.find_commit(libcxxabirev)
            config.libcxxabi_revision = libcxxabicommit.get_sha1()

            libcxxrev = config.get_libcxx_revision()
            libcxxrep = Repository2.from_directory(os.path.join(homedir,'src','llvm', 'projects', 'libcxx'))
            libcxxcommit = libcxxrep.get_head() if libcxxrev is None else  libcxxrep.find_commit(libcxxrev)
            config.libcxx_revision = libcxxcommit.get_sha1()


        if config.revision is None:
            config.revision = svnrev



        branch = rep.get_branch(jobname)
        rep.checkout(pollycommit,detach=True,force=True)
        if branch.exists():
            rep.merge(branch,noedit=True,strategy='ours')




        shutil.copy(script, workdir)
        shutil.copy(os.path.join(os.path.dirname(script), 'run-test-suite.py'), workdir)

#        with open(os.path.join(workdir, 'run-test-suite.ini'), 'w') as file:
#            file.write("""[llvm]
#base=r{svnrev}
#cmake={llvmcmake}
#flags={llvmflags}
#revision={llvmrev}
#
#[lnt]
#revision={lntrev}
#args={lntargs}
#
#[test-suite]
#revision={testsuiterev}
#cmake={testsuitecmake}
#flags={testsuiteflags}
#mllvm={testsuitemllvm}
#multisample={multisample}
#max_procs={max_procs}
#max_load={max_load}
#only={only}
#taskset={taskset}
#""".format(svnrev=svnrev,llvmcmake=shlist(llvmcmake),lntargs=shlist(lntargs),testsuitecmake=shlist(testsuitecmake),testsuiteflags=shlist(testsuiteflags),testsuitemllvm=shlist(testsuitemllvm),multisample='' if multisample is None else multisample,testsuiterev=testsuiterev,max_procs='' if max_procs is None else max_procs,max_load='' if max_load is None else max_load,lntrev='' if lntrev is None else lntrev,llvmflags=shlist(llvmflags),llvmrev='' if llvmrev is None else llvmrev,only='' if suite_testonly is None else shlist(suite_testonly),taskset=taskset))

        resultdir = os.path.join(workdir, 'run-test-suite')
        os.makedirs(resultdir, exist_ok=True)

        with open(os.path.join(resultdir, '.gitignore'), 'w') as file:
            file.write("""
; Exclude all files, but include directories (to make globs below apply)
*
!*/

; Include this file, otherwise it is not added to the slave's workdir
!.gitignore

!*.time
!*.perfstats
!*.stats
!*.out
!*.stdout
!*.json
""")

        rep.add_all()

        configargs = config.get_cmdline()
        configstr = shquote(configargs)
        if comment is None:
            comment = ' '.join(configargs)


        msgdict = dict(configstr=configstr,svnrev=svnrev,comment=comment,shortcommit=pollycommit.get_short(),invocation=shjoin(invocation))
        message = """[r{svnrev}/{shortcommit}] {comment}

Job create using command:
{invocation}

Exec: python3 ./run-test-suite.py {configstr}""".format(**msgdict)

        jobcommit = rep.commit(message=message,allow_empty=True)
        rep.checkout(overwritebranch=jobname)
        #config.polly_revision = pollycommit.get_sha1()


        if testrun:
            run_test_suite =  __import__("run-test-suite")
            # Find the parent LLVM directory
            llvmsrc = os.path.abspath('.')
            while True:
                if os.path.isfile(os.path.join(llvmsrc, 'llvm.spec.in')):
                    break

                if llvmsrc == os.path.dirname(llvmsrc):
                    llvmsrc = os.path.abspath('.')
                    break
                llvmsrc = os.path.dirname(llvmsrc)


            argv = ['--llvm-source-dir=' + llvmsrc, '--llvm-build-dir=' + os.path.join(homedir,'build','llvm','release')] + configargs
            os.environ['persistentdir'] = os.path.join(homedir, 'execslave', 'persistent')
            os.chdir(rep.workdir)
            # llvm_source_dir=os.path.join(homedir,'execslave','persistent','llvm') , llvm_build_dir= os.path.join(homedir,'execslave','persistent','llvm-build')
            run_test_suite.main(argv=argv)
        else:
            branch.push_to('execjobs', force=True)



def gittool_transcmd(cmd):
    homedir = os.path.expanduser('~')
    srcdir = os.path.join(homedir, 'src')
    builddir = os.path.join(homedir, 'build')
    bindir = os.path.join(builddir, 'llvm', 'vc14', 'Debug', 'bin')

    #parser = argparse.ArgumentParser()
    #parser.add_argument('-o')
    #parser.add_argument('args', nargs=argparse.REMAINDER)
    #known = parser.parse_args(cmd)

    origclang = cmd[0]
    _,origexe = os.path.split(origclang)
    origargs = cmd[1:]

    exe = os.path.join(bindir, origexe + '.exe')

    args = []
    i = 0
    while i < len(origargs):
        origarg = origargs[i]
        if origarg=='-o':
            i += 1
            output = origargs[i]
        elif origarg.startswith('/root/src/'):
            args.append(os.path.join(srcdir,origarg[10:]))
        else:
            args.append(origarg)
        i+=1

    p = subprocess.Popen([exe] + args + ['-v'], stderr=subprocess.PIPE, universal_newlines=True)
    p.wait()
    result = p.stderr.read()

    m = re.search( r'^ (?P<exe>\S+)\s+\-cc1\s+(?P<line>.*)$', result, re.MULTILINE)
    line = '-cc1 ' + m.group('line')
    print(line)



def bisect_run(cmd):
    if cmd[0] == 'gittool':
        cmd = [ 'python3', script] + cmd[1:]
    else:
        cmd[0] = shutil.which(cmd[0])
    _,errcode,_,output = invoke(*cmd, return_stderr=True,resumeonerror=True)


    m = re.search(r'^ENDSTATUS\:(?P<endstatus>.*)$', output, re.MULTILINE)
    if m:
        result = m.group('endstatus').strip()
    else:
        result = errcode

    return result;



def gittool_bisect_run(cmd,good=None,bad=None):
    result = bisect_run(cmd)
    if good is not None and result == good:
        print("Good state:",result)
        exit(0)
    if bad is not None and result == bad:
        print("Bad state:",result)
        exit(1)
    print("Undecidable state:",result)
    exit(125)


def gittool_bisect(rep,cmd):
    def bisect_try(commit=None):
        if commit is not None:
            rep.checkout(commit,detach=True)
        result = bisect_run(cmd)
        print("### Result for",commit,":",result)
        return result

    curhead = rep.get_head()
    curresult = bisect_try()

    with rep.preserve():
        goback = 1
        while True:
            print("### goback=",goback)

            head = curhead.predecessor(goback)
            result = bisect_try(commit=head)
            if result != curresult:
                prevhead = head
                prevresult=result
                break
            failhead = head

            goback = max(goback+1, min(2*goback, goback + 10 + goback//2))

        print("HEAD=",curresult, "vs. PREV=",prevresult)
        rep.invoke_git('bisect', 'start', failhead, prevhead)
        rep.invoke_git('bisect', 'run', script, 'bisect-run', '--bad', curresult, '--good', prevresult, '--cmd', *cmd)
        rep.invoke_git('bisect', 'reset')


def gittool_taskset(cmd):
    pid = os.gitpid()
    psout = query('ps', '-o', 'psr', '-p', pid)
    pslines = psout.splitlines()
    tid = int(pslines[1])
    print("Running on core",tid)
    invoke('taskset', '-c', tid, *cmd)


def gittool_selfcheck():
    testrep = create_testdir()
    with testrep.preserve():
        verify_testdir(testrep)
        createfile(os.path.join(testrep.workdir,'tempfile'), "Delete me")
    expectnofile(os.path.join(testrep.workdir,'tempfile'))
    verify_testdir(testrep)


def _str_to_bool(s):
    """Convert string to bool (in argparse context)."""
    if s.lower() not in ['true', 'false', '1', '0','y','n','yes','no','on','off']:
        raise ValueError('Need bool; got %r' % s)
    return {'true': True, 'false': False, '1':True, '0':False,'y':True,'n':False, 'yes':True,'no':False, 'on':True,'of':False}[s.lower()]


def add_boolean_argument(parser, name, default=False):
    """Add a boolean argument to an ArgumentParser instance."""
    destname = name.replace('-','_')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--' + name, dest=destname, nargs='?', default=default, const=True, type=_str_to_bool)
    group.add_argument('--no-' + name, dest=destname, action='store_false')




def addcommand_selfcheck(parser=None, args=None):
    if parser is not None:
        pass

    if args is not None:
        gittool_selfcheck()


def addcommand_get(parser=None, args=None):
    if parser is not None:
        parser.add_argument('project')

    if args is not None:
        gittool_checkout(args.project)


def addcommand_pushall(parser=None, args=None):
    if parser is not None:
        pushall=parser
        pushall.add_argument('project')
        pushall.add_argument('remote')
        pushall.add_argument('branch')
        pushall.add_argument('--force','-f',action='store_true')

    if args is not None:
        gittool_pushall(args.project, args.remote, args.branch, force=args.force)


def addcommand_checkoutall(parser=None, args=None):
    if parser is not None:
        checkoutall = parser
        checkoutall.add_argument('--force','-f',action='store_true')
        checkoutall.add_argument('--fullname',action='store_true')

    if args is not None:
        rep = Repository2.from_directory(args.work_tree)
        gittool_checkoutall(rep,force=args.force,fullname=args.fullname)



def addcommand_split(parser=None, args=None):
    if parser is not None:
        split = parser
        split.add_argument('commit', default='HEAD')
        split.add_argument('--work', choices=['none', 'left', 'right'], default='none')

    if args is not None:
        # --work-tree C:\Users\Meinersbur\src\llvm\tools\polly split HEAD
        rep = Repository2.from_directory(args.work_tree) #  rep = Repository(args.work_tree)

        leftrep = None
        rightrep = None
        if args.work == 'left':
            leftrep = rep
        elif args.work == 'right':
            rightrep = rep
        assert rep.workdir_is_clean(untracked_files=True) # TODO: We can save cached and untracked (and ignored?) by creating throwaway
                                                          # commits (or git stash)

        commit = rep.rev_parse(args.commit)
        assert commit


        #with TemporaryDirectory(prefix='gittool-') as tmpdir:
        if True:
            tmpdir = tempfile.mkdtemp(prefix='gittool-')
            gittool_split(rep,leftrep, rightrep, tmpdir, commit)
            shutil.rmtree(tmpdir,onerror=remove_readonly)


def addcommand_dirdiff(parser=None, args=None):
    if parser is not None:
        parser.add_argument('commit')

    if args is not None:
        rep = Repository2.from_directory(args.work_tree)
        commit = rep.rev_parse(args.commit)
        tmpdir = tempfile.mkdtemp(prefix='gittool-')
        gittool_dirdiff(tmpdir, rep, commit)
        shutil.rmtree(tmpdir,onerror=remove_readonly)


def addcommand_setseq(parser=None, args=None):
    if parser is not None:
        parser.add_argument('commits', nargs='*')

    if args is not None:
        rep = Repository2.from_directory(args.work_tree)
        commits = []
        for commit in args.commits:
            commits.append(rep.rev_parse(commit))
        gittool_setseq(rep, commits)


def addcommand_reproduce(parser=None, args=None):
    if parser is not None:
        reproduce=parser
        reproduce.add_argument('cmd', nargs=argparse.REMAINDER)
        add_boolean_argument(reproduce, 'as-if', default=False)
        add_boolean_argument(reproduce, 'even-successful',default=False)
        add_boolean_argument(reproduce, 'build',default=True)
        add_boolean_argument(reproduce, 'preprocess-includes',default=False)
        add_boolean_argument(reproduce, 'preprocess-macros',default=False)
        add_boolean_argument(reproduce, 'preprocess-line',default=False)
        add_boolean_argument(reproduce, 'cc1',default=False)
        add_boolean_argument(reproduce, 'min-args',default=False)
        add_boolean_argument(reproduce, 'afl',default=False)
        add_boolean_argument(reproduce, 'format',default=False)
        add_boolean_argument(reproduce, 'dump-ll',default=False)
        add_boolean_argument(reproduce, 'emit-ll',default=False)
        add_boolean_argument(reproduce, 'fewer-passes',default=False)
        add_boolean_argument(reproduce, 'min-mllvm',default=False)
        add_boolean_argument(reproduce, 'bugpoint',default=False)
        add_boolean_argument(reproduce, 'write-test',default=True)

    if args is not None:
        cmdline = args.cmd
        if cmdline[0] == '--':
            cmdline = cmdline[1:]
        cwd=os.getcwd()
        gittool_reproduce(cmdline=cmdline,asif=args.as_if,even_successful=args.even_successful,build=args.build,
                          cpp_includes=args.preprocess_includes,cpp_macros=args.preprocess_macros,cc_cc1=args.cc1,cc_minargs=args.min_args,cc_afl=args.afl,cc_format=args.format, ll_minargs=args.min_mllvm,
                          dump_ll=args.dump_ll,  emit_ll=args.emit_ll,fewer_passes=args.fewer_passes,bugpoint=args.bugpoint,writetest=args.write_test,cpp_lines=args.preprocess_line,clang_cwd=cwd)


def addcommand_buildbot(parser=None, args=None):
    if parser is not None:
        buildbot = parser
        buildbot.add_argument('project', nargs='?')
        buildbot.add_argument('--comment',help="Additional comment")
        buildbot.add_argument('--revision', type=int, help="Base revision (do not use HEAD)")
        buildbot.add_argument('--patch',action='append',help="Apply patch before committing")
        buildbot.add_argument('--builder',default='perf-x86_64-penryn-O3-polly')
        buildbot.add_argument('--password', required=True)

    if args is not None:
        if args.project is None:
            rep = Repository2.from_directory(args.work_tree)
        else:
            global projects
            workdir = projects[args.project].workdir
            rep = Repository2.from_directory(workdir)
        gittool_buildbot(rep=rep, password=args.password, comment=args.comment, patches=args.patch,revision=args.revision,builder=args.builder)



def addcommand_reduce(parser=None, args=None):
    if parser is not None:
        reduce=parser
        reduce.add_argument('testfile')
        reduce.add_argument('--inplace','-i',action='store_true')
        add_boolean_argument(reduce, 'build',default=True)
        add_boolean_argument(reduce, 'preprocess-includes',default=False)
        add_boolean_argument(reduce, 'preprocess-macros',default=False)
        add_boolean_argument(reduce, 'preprocess-line',default=False)
        add_boolean_argument(reduce, 'cc1',default=False)
        add_boolean_argument(reduce, 'min-args',default=False)
        add_boolean_argument(reduce, 'afl',default=False)
        add_boolean_argument(reduce, 'format',default=False)
        add_boolean_argument(reduce, 'dump-ll',default=False)
        add_boolean_argument(reduce, 'emit-ll',default=False)
        add_boolean_argument(reduce, 'fewer-passes',default=False)
        add_boolean_argument(reduce, 'min-mllvm',default=False)
        add_boolean_argument(reduce, 'bugpoint',default=False)
        add_boolean_argument(reduce, 'write-test',default=True)

    if args is not None:
        gittool_reduce(testfile=args.testfile,build=args.build,inplace=args.inplace,
                          cpp_includes=args.preprocess_includes,cpp_macros=args.preprocess_macros,cc_cc1=args.cc1,cc_minargs=args.min_args,cc_afl=args.afl,cc_format=args.format, ll_minargs=args.min_mllvm,
                          dump_ll=args.dump_ll, emit_ll=args.emit_ll,fewer_passes=args.fewer_passes,bugpoint=args.bugpoint,writetest=args.write_test,cpp_lines=args.preprocess_line)





def addcommand_sendmail(parser=None, args=None):
    if parser is not None:
        sendmail=parser
        sendmail.add_argument('since')
        sendmail.add_argument('--reroll-count', '-v', type=int)

    if args is not None:
        rep = Repository2.from_directory(args.work_tree)
        if not rep.workdir_is_clean(untracked_files=False):
            print("Something left in the workdir. Want to commit?")
            return False
        since = None
        if args.since is not None:
            since = rep.rev_parse(args.since)
        gittool_sendmail(rep=rep,since=since,commit=None,reroll_count=args.reroll_count)


# execslave --slavename wsl --persistentdir C:\Users\Meinersbur\execslave\persistent --source git@meinersbur.de:execjobs.git --target git@meinersbur.de:execresults-wsl.git  --slurm  --no-watch
def addcommand_execslave(parser=None, args=None):
    if parser is not None:
        execslave=parser
        execslave.add_argument('--source', required=True, help="Git path to observe")
        execslave.add_argument('--target', required=True, help="Git path to push results to")
        #execslave.add_argument('--workdir',required=True, help="Path to prepare,
        #execute commands in, and results are found")
        execslave.add_argument('--persistentdir', default=os.path.join(tempfile.gettempdir(), 'execslave'), help="For files that persist between builds")
        execslave.add_argument('--slavename','--slave-name',default=platform.node(),help="Name of this slavebot")
        execslave.add_argument('--configname', '--config-name')
        execslave.add_argument('--waitsecs', type=int, default=300, help="Seconds to wait between looking for new jobs")
        execslave.add_argument('--onlyone', '--oneonly','--once', action='store_true',help="Do only one job and then exit (For diagnosing execslaves)")
        execslave.add_argument('--onlyjob')
        execslave.add_argument('--no-watch', action='store_true', help="When there is no more job to do, exit instead of watching for new jobs")
        execslave.add_argument('--no-push', action='store_true', help="Do not push results to target")
        #execslave.add_argument('--use-perf', help="Pass --use-perf=/TEST_SUITE_USE_PERF=ON")
        #execslave.add_argument('--exec-cpus', type=int)
        #execslave.add_argument('--compile-cpus', type=int)
        #execslave.add_argument('--llvm-cmake-defs',dest='llvmcmake',action='append',default=[])
        #execslave.add_argument('--llvm-flags',dest='llvmflags',action='append',default=[])
        #execslave.add_argument('--lnt-args',dest='lntargs',action='append',default=[])
        #execslave.add_argument('--suite-cmake-defs',dest='testsuitecmake',action='append',default=[])
        #execslave.add_argument('--suite-flags',dest='testsuiteflags', action='append',default=[])
        #execslave.add_argument('--suite-mllvm',dest='testsuitemllvm', action='append',default=[])
        execslave.add_argument('--parallel', type=int,default=1,nargs='?',const=0)
        execslave.add_argument('--slurm', action='store_true')

    if args is not None:
        workdir = os.getcwd()
        if args.work_tree is not None:
            workdir = args.work_tree

        gittool_execslave(workdir=workdir, source=args.source, target=args.target, persistentdir=args.persistentdir, slavename=args.slavename,waitsecs=datetime.timedelta(seconds=args.waitsecs),onlyone=args.onlyone,onlyjob=args.onlyjob,watch=not args.no_watch,slurm=args.slurm,parallel=args.parallel,push=not args.no_push)



def addcommand_execjob(parser=None, args=None):
    if parser is not None:
        parser.add_argument('--workdir')
        parser.add_argument('--persistentdir')
        parser.add_argument('--source')
        parser.add_argument('--target')
        parser.add_argument('--slavename')
        parser.add_argument('--configname')
        parser.add_argument('--srchead')
        parser.add_argument('--dstname')
        parser.add_argument('--dsthead')
        #parser.add_argument('--no-push',action='store_true')
    if args is not None:
        workdir = os.getcwd()
        if args.work_tree is not None:
            workdir = args.work_tree
        if args.workdir is not None:
            workdir = args.workdir
        gittool_execjob(workdir=workdir,persistentdir=args.persistentdir,source=args.source,target=args.target,slavename=args.slavename,configname=args.configname,srchead=args.srchead,dstname=args.dstname,dsthead=args.dsthead)



def addcommand_runtest(parser=None, args=None):
    if parser is not None:
        RuntestConfig.add_runtest_arguments(parser)
        #parser.add_argument('--suite-build-dir',help="Where to configure/build the test suite (default: some unique temporary dir)")

        #parser.add_argument('--mllvm','-mllvm','--suite-mllvm', action='append')
        #parser.add_argument('--suite-flags','--suite-cppflags', action='append')
        #parser.add_argument('--verbose', '-v', action='store_true')
        #parser.add_argument('--threads','-j',type=int)
        #parser.add_argument('--build-threads',type=int)
        #parser.add_argument('--exec-threads',type=int)
        #add_boolean_argument(parser, 'bugpoint',default=False)
        #parser.add_argument('--polly','-polly',action='store_true')
        #parser.add_argument('--process-unprofitable','--polly-process-unprofitable','-polly-process-unprofitable',action='store_true')
        #parser.add_argument('--clang',default='release')
        #parser.add_argument('--clang-debug',dest='clang', action='store_const',const='debug')
        #parser.add_argument('--debug',action='store_true')
        #parser.add_argument('--debug-only')
        #add_boolean_argument(parser, 'reproduce',default=True)
        #add_boolean_argument(parser, 'reproduce-all',default=False)
        #parser.add_argument('--llvm-builddir')
        #parser.add_argument('--suite-cmake-defs',dest='testsuitecmake',action='append',default=[])

    if args is not None:
        global homedir
        srcdir = os.path.join(homedir,'src')
        builddir = os.path.join(homedir,'build')
        tmpdir = tempfile.gettempdir()

        config = RuntestConfig.from_cmdargs(args)

        if config.llvm_source_dir is None:
            config.llvm_source_dir = os.path.join(srcdir,'llvm')
        if config.llvm_build_dir is None:
            config.llvm_build_dir = os.path.join(builddir,'llvm','release')
        #if config.suite_source_dir is None:
        #    config.suite_source_dir = os.path.join(srcdir,'llvm','projects','test-suite')

        runtest(config)
        #gittool_runtest(mllvm=args.mllvm,testonly=args.only_test,threads=args.threads,build_threads=args.build_threads,exec_threads=args.exec_threads,verbose=args.verbose,bugpoint=args.bugpoint,processunprofitable=args.process_unprofitable,polly=args.polly,suiteflags=args.suite_flags,build=args.clang,debug=args.debug,debug_only=args.debug_only,reproduce=args.reproduce,reproduce_all=args.reproduce_all,llvmbuilddir=args.llvm_builddir,testsuitecmake=args.testsuitecmake)


def addcommand_makejob(parser=None, args=None):
    if parser is not None:
        makejob = parser
        makejob.add_argument('jobname')
        makejob.add_argument('--comment')

        makejob.add_argument('--testrun', action='store_true')
        #makejob.add_argument('--suite-build-dir',help="Where to configure/build the test suite (default: some unique temporary dir)")

        RuntestConfig.add_runtest_arguments(makejob)

        #makejob.add_argument('--revision')
        #makejob.add_argument('--testsuiterevision','--suite-rev')
        #makejob.add_argument('--lntrevision', '--lnt-rev')
        #makejob.add_argument('--llvmrevision', '--llvm-rev')
        #makejob.add_argument('--llvm-cmake-defs', '--llvm-cmake', dest='llvmcmake',action='append',default=[])
        #makejob.add_argument('--llvm-flags',dest='llvmflags',action='append',default=[])
        #makejob.add_argument('--lnt-args',dest='lntargs',action='append',default=[])
        #makejob.add_argument('--suite-cmake-defs','--suite-cmake',dest='testsuitecmake',action='append',default=[])
        #makejob.add_argument('--suite-flags',dest='testsuiteflags', action='append',default=[])
        #makejob.add_argument('--suite-mllvm',dest='testsuitemllvm', action='append',default=[])
        #makejob.add_argument('--multisample',type=int)
        #makejob.add_argument('--max-procs',type=int)
        #makejob.add_argument('--max-load',type=float)
        #makejob.add_argument('--only-test', '--test-only',action='append')
        #makejob.add_argument('--polly', '-polly',action='store_true')
        #makejob.add_argument('--polly-process-unprofitable', '-polly-process-unprofitable',action='store_true')
        #add_boolean_argument(makejob, 'taskset', default=True)

    if args is not None:
        config  = RuntestConfig.from_cmdargs(args)
        rep = Repository2.from_directory(args.work_tree)

        gittool_makejob(config=config,jobname=args.jobname,rep=rep,comment=args.comment,testrun=args.testrun,invocation=sys.argv)


def addcommand_bisect(parser=None, args=None):
    if parser is not None:
        parser.add_argument('--cmd', nargs=argparse.REMAINDER)

    if args is not None:
        rep = Repository2.from_directory(args.work_tree)
        gittool_bisect(rep, args.cmd)




def addcommand_bisectrun(parser=None, args=None):
    if parser is not None:
        bisect_run = parser
        bisect_run.add_argument('--good')
        bisect_run.add_argument('--bad')
        bisect_run.add_argument('--cmd', nargs=argparse.REMAINDER)

    if args is not None:
        gittool_bisect_run(cmd=args.cmd, good= args.good,bad=args.bad)




def main():
    parser = argparse.ArgumentParser(description="Interactively split a git commit into two") # ,allow_abbrev=False (since python3 3.5, but msys currently is at 3.4)
    parser.add_argument('--work-tree','--work-dir','--workdir', default='.')
    subparsers = parser.add_subparsers(dest='command')

    commands = {
        'selfcheck': addcommand_selfcheck,
        'get': addcommand_get,
        'push-all': addcommand_pushall,
        'checkout-all': addcommand_checkoutall,
        'split': addcommand_split,
        'dirdiff': addcommand_dirdiff,
        'setseq': addcommand_setseq,
        'reproduce': addcommand_reproduce,
        'reduce': addcommand_reduce,
        'buildbot': addcommand_buildbot,
        'sendmail': addcommand_sendmail,
        'execslave': addcommand_execslave,
        'execjob': addcommand_execjob,
        'runtest': addcommand_runtest,
        'makejob': addcommand_makejob,
        'bisect': addcommand_bisect,
        'bisect-run': addcommand_bisectrun
    }

    for cmd,func in commands.items():
        subparser = subparsers.add_parser(cmd)
        func(parser=subparser,args=None)

    args = parser.parse_args()

    for cmd,func in commands.items() :
        if args.command==cmd:
            return func(parser=None,args=args)

    print("No command?")

if __name__ == '__main__':
    main()
    pass
