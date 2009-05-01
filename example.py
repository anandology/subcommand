"""Subcommand example.

Options:
    -v [--verbose]      : verbose
"""
import subcommand

@subcommand.subcommand(aliases=["co"])
def checkout(options, *args):
    """Check out a working copy from a repository.

    Fake subcommand to demonstrate subcommand functionality.

    Options:
        -r [--revision] revision int    : revision to checkout
        --username username             : username
        --password password             : password
    """
    print "dummy checkout."
    print "options:", options
    print "args:", args
    print "global options:", subcommand.global_options

if __name__ == "__main__":
    subcommand.main()
