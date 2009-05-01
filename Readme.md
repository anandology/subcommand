# subcommand: Python library for creating command line applicaitons with subcommands

Subcommand is a function decorated with `subcommand.subcommand()` decorator.
Help message and options are specified in docstring. 

Hello world example:

    import subcommand

    @subcommand.subcommand()
    def hello(options, name='world'):
        """Display hello message.

        Usage: hello [options] [name]

        Options:

        -p [--prefix] prefix    : message prefix (default: hello)
        -n [--repeat] n         : repeat the message n times (type: int) (default: 1)
        """
        for i in range(options.n):
            print options.prefix + ",", name

    if __name__ == "__main__":
        subcommand.main()

And here is the response.

    $ python hello.py hello
    hello, world
    $ python hello.py hello subcommand
    hello, subcommand
    $ python hello.py hello -p bye subcommand
    bye, subcommand
    $ python hello.py hello --prefix bye subcommand
    bye, subcommand
    $ python hello.py hello -p bye -n 3 subcommand
    bye, subcommand
    bye, subcommand
    bye, subcommand

    $ python hello.py
    usage: python hello.py <subcommand> [options] [args]

    Available subcommands:
        hello       Displays hello message.
        help        Describe usage of this program and its subcommands.

    anand@bodhi subcommand$ python hello.py help hello
    hello: Displays hello message.

    Usage: hello [options] [name]

    Valid Options:
      -p [--prefix] prefix            : message prefix (default: hello)
      -n [--repeat] n                 : repeat the message n times (default: 1)

    
