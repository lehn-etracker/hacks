#!/usr/bin/python
#
# Steal env: steal a process' environment
# (c)2011 Dennis Kaarsemaker, dedicated to the public domain

import os
import sys

def from_pid(pid, update=False):
     env = open(os.path.join('/proc/%d/environ' % pid)).read()
     env = dict([x.split('=', 1) for x in env.split('\x00') if x])
     if update:
        os.environ.update(env)
     return env

def from_name(name, update=False):
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            exe = os.readlink(os.path.join('/proc', d, 'exe'))
        except OSError:
            continue
        if exe == name:
            return from_pid(int(d), update)
    else:
        print "Process %s not running" % find_exe

if __name__ == '__main__':
    import optparse
    usage = """%prog [options] pid

Output the environment of the process with the specified pid in a variety of
formats, usable by shells and other languages."""
    p = optparse.OptionParser(usage=usage)
    p.add_option('-s','--sh',
                 action='store_true', dest='sh', default=False,
                 help='Output sh style commands')
    p.add_option('-c','--csh',
                 action='store_true', dest='csh', default=False,
                 help='Output csh style commands')
    p.add_option('-j','--json',
                 action='store_true', dest='json', default=False,
                 help='Output json')
    p.add_option('-e','--export',
                 action='store_true', dest='export', default=False,
                 help='sh/csh command will export variables')
    p.add_option('-0', '--null',
                 action='store_true', dest='zero', default=False,
                 help='Output null-terminated strings and a trailing null')

    opts, args = p.parse_args()
    if len(args) < 1:
        p.error('Must specify a pid or application to steal from')
    if sum([opts.sh, opts.csh, opts.json, opts.zero, len(args) > 1]) > 1:
        p.error('Must specify exactly one output format or specify a command line')
    elif sum([opts.sh, opts.csh, opts.json, opts.zero]) == 0:
        if os.environ['SHELL'].endswith('csh'):
            opts.csh = True
        else:
            opts.sh = True

    if args[0].isdigit():
        env = from_pid(int(args[0], False))
    else:
        env = from_name(args[0], False)

    if len(args) > 1:
        os.environ.update(env)
        os.execve(args[1], args[1:], os.environ)

    if opts.json:
        import simplejson
        print simplejson.dumps(env)
        exit(0)

    escape = True
    if opts.sh:
        tmpl = '%s="%s"'
        if opts.export:
            tmpl = 'export ' + tmpl
    elif opts.csh:
        tmpl = 'set %s="%s"'
        if opts.export:
            tmpl = 'setenv %s "%s"'
    elif opts.zero:
        tmpl = '%s\x00%s\x00'
        escape = False

    for key, val in env.items():
        if escape:
            val = val.replace('\\','\\\\')
            val = val.replace('$','\\$')
            val = val.replace('"','\\"')
            val = val.replace('`','\\`')

        print tmpl % (key, val)

    if opts.zero:
        print '\x00'
