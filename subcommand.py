"""Library to build command line utilities with subcommands.
"""

__author__ = "Anand Chitipothu <anandology@gmail.com>"
__version__ = "0.1"

__all__ = ["subcommand", "main", "Option"]

import optparse
import re
import sys
import itertools

prog = None
global_options = {}
subcommand_lookup = {}
subcommands = []

class Program:
    def __init__(self, name, help, options):
        """Creates a program instance.
        name - name of the program, if not specified uses sys.argv[0]
        help - help for the program, if not specified taken from docstring of __main__ module
        options - global options for the program, if not specified taken from docstring of __main__ module
        """
        main_module = __import__("__main__")
        self.name = name or ("python " + sys.argv[0])
        _help, _options = parse_docstring(main_module.__doc__)
        self.help = help or _help
        self.options = options or _options

    def __call__(self, args):
        global global_options
        global_options, args = parse_options(self.options, args)
        if args:
            cmd, args = args[0], args[1:]
        else:
            cmd = "help"

        if cmd in subcommand_lookup:
            subcommand_lookup[cmd](args)
        else:
            print >> sys.stderr, "Unknown command:", cmd
            print >> sys.stderr, "Type '%s help' for usage." % prog.name

class SubCommand:
    def __init__(self, func, name, aliases, help, options):
        self.func = func
        self.name = name or func.__name__
        self.aliases = aliases

        _help, _options = parse_docstring(func.__doc__)
        self.help = help or _help
        self.options = options or _options

    def __call__(self, args=[]):
        options, args = parse_options(self.options, args)
        return self.func(options, *args)

    def __str__(self):
        return self._title() + "\t" + self._short_desc()

    def _title(self):
        name = self.name
        if self.aliases:
            name += " (" + ", ".join(self.aliases) + ")"
        return name

    def _short_desc(self):
        return self.help and self.help.splitlines()[0].strip()

    def _long_desc(self):
        lines = self.help.splitlines()[1:]
        return "\n".join(lines).strip()

    def showhelp(self):
        print self._title() + ": " + self._short_desc()
        print
        long_desc = self._long_desc()
        if long_desc:
            print long_desc
            print
        if self.options:
            print "Valid Options:"
            for option in self.options:
                print "  " + str(option)

def subcommand(name=None, aliases=[], help=None, options=None):
    def decorator(f):
        cmd = SubCommand(f, name, aliases, help, options)
        subcommands.append(cmd)
        subcommand_lookup[cmd.name] = cmd
        for alias in cmd.aliases:
            subcommand_lookup[alias] = cmd
        return cmd
    return decorator

def xrepr(name, *a, **kw):
    a = list([repr(x) for x in a]) + ["%s=%s" % (k, repr(v)) for k, v in kw.items() if v is not None]
    return "%s(%s)" % (name, ", ".join(a))

class Option(optparse.Option):
    """
    >>> Option("-v", "--verbose", help="Turn on verbose output")
    Option('-v', '--verbose', dest='verbose', type='string', help='Turn on verbose output')
    """
    def __repr__(self):
        opts = self._short_opts + self._long_opts
        kw = dict(type=self.type, dest=self.dest, help=self.help)
        if self.default != ('NO', 'DEFAULT'):
            kw['default'] = self.default
        return xrepr("Option", *opts, **kw)

    def __str__(self):
        opts = self._short_opts + self._long_opts
        opt_string = opts[0]
        if len(opts) > 1:
            opt_string += " " +  " ".join("[%s]" % opt for opt in opts[1:])
        if self.action == "store":
            opt_string += " " + self.dest
        return "%-32s: %s" % (opt_string, self.help)

def parse_docstring(docstring):
    r"""Parse docstring.

    >>> parse_docstring('''Parse file.
    ... 
    ... Options:
    ...     -q [--quiet]       : run in quiet mode, don't display any errors.
    ...     -l [--log] logfile : log file
    ... ''')
    ...
    ('Parse file.\n', [Option('-q', '--quiet', dest='quiet', help="run in quiet mode, don't display any errors."), Option('-l', '--log', dest='logfile', type='string', help='log file')])
    """
    docstring = docstring or ""
    lines = [line.strip() for line in docstring.splitlines()]
    lowerlines = [line.lower() for line in lines]

    if 'options:' in lowerlines:
        index = lowerlines.index('options:')
        help = "\n".join(lines[:index])
        options = [parse_option(line) for line in lines[index+1:] if line]
        return help, options
    else:
        return docstring, []

def parse_option(line):
    """Parse one option from docstring.

    >>> parse_option('-v [--verbose]    : Turn on verbose output')
    Option('-v', '--verbose', dest='verbose', help='Turn on verbose output')
    >>> parse_option('-f [--config] configfile   : config file')
    Option('-f', '--config', dest='configfile', type='string', help='config file')
    >>> parse_option('-p [--port] port  : port (type: int)')
    Option('-p', '--port', dest='port', type='int', help='port')
    >>> parse_option('-f [--config] configfile   : config file (default: hello.conf)')
    Option('-f', '--config', dest='configfile', default='hello.conf', type='string', help='config file')
    >>> parse_option('-p [--port] port : port (type: int)')
    Option('-p', '--port', dest='port', type='int', help='port')
    """
    options, help = line.split(':', 1)

    options = [x for x in re.split(" +|\[|\]", options) if x]
    options, option_desc = [x for x in options if x.startswith('-')], [x for x in options if not x.startswith('-')]

    tokens = re.split("\(([^\(\)]*)\)", help)
    help = tokens[0].strip()

    tokens = [t.split(':', 1) for t in tokens[1:] if ':' in t]
    kw = dict((k.strip(), v.strip()) for k, v in tokens)

    if 'default' in kw:
        help = help + " (default: %s)" % kw['default']

    opt = Option(help=help.strip(), *options, **kw)

    if option_desc:
        opt.dest = option_desc[0]
    else:
        opt.action = "store_true"
        opt.type = None
    return opt

def parse_options(options, args):
    """Parses args and returns option values and leftover args."""
    parser = optparse.OptionParser(option_list=options, add_help_option=False)
    parser.allow_interspersed_args = False

    parser.rargs = args
    parser.largs = []
    parser.values = parser.get_default_values()

    try:
        stop = parser._process_args(parser.largs, parser.rargs, parser.values)
    except (optparse.BadOptionError, optparse.OptionValueError), err:
        # TODO: customize this later
        parser.error(str(err))

    return (parser.values, parser.rargs)

def main(name=None, help=None, options=None):
    global prog
    prog = Program(name, help, options)
    return prog(sys.argv[1:])

@subcommand()
def help(options, *cmds):
    """Describe usage of this program and its subcommands.
    """
    if cmds:
        for cmd in cmds:
            subcommand_lookup[cmd].showhelp()
    else:
        print "usage: %s <subcommand> [options] [args]" % prog.name
        print
        print "Available subcommands:" 
        for cmd in sorted(subcommands, key=lambda cmd: cmd.name):
            print "   ", cmd
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
