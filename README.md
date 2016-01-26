# climax

[![Build Status](https://travis-ci.org/miguelgrinberg/climax.svg?branch=master)](https://travis-ci.org/miguelgrinberg/climax)

A lightweight argparse wrapper inspired by click.

Climax is a little argparse wrapper, with a decorator based syntax heavily
inspired by Armin Ronacher's [click](http://click.pocoo.org/). Climax can
import native argparse parsers as sub-commands, and can also export itself as
a native parser, providing full interoperability with existing argparse
based solutions.

## Getting Started

The following example should give you a pretty good idea of how climax works:

    import climax

    @climax.command()
    @climax.argument('--count', type=int, help="how many times to repeat")
    @climax.argument('name', help="the name to repeat")
    def repeat(count, name):
        """This silly program repeats a name the given number of times."""
        for i in range(count):
            print(name)

    if __name__ == '__main__':
        repeat()

In the script above, the arguments to the `@climax.argument` decorator are
anything you would send to the `ArgumentParser.add_argument` method. In
fact, climax passes these arguments to it untouched. The `@climax.command`
decorator takes optional arguments, which are passed to the `ArgumentParser`
constructor. For example, to set a custom program name, you can pass
`prog='my_command_name'`.

When you run the above script, you get a functional command line parser:

    $ python repeat.py
    usage: repeat.py [-h] [--count COUNT] name

The `--help` option is automatically generated by argparse, from the
information passed on the decorators:

    $ python repeat.py --help
    usage: repeat.py [-h] [--count COUNT] name

    This silly program repeats a name the given number of times.

    positional arguments:
      name           the name to repeat

    optional arguments:
      -h, --help     show this help message and exit
      --count COUNT  how many times to repeat

If you provide valid arguments, then the command function runs:

    $ python repeat.py --count 3 foo
    foo
    foo
    foo

And if anything in the command line is incorrect, you get an error:

    $ python repeat.py --count not-a-number foo
    usage: repeat.py [-h] [--count COUNT] name
    repeat.py: error: argument --count: invalid int value: 'not-a-number'

## Building Command Groups

One of the nicest features of argparse is the ability to build complex command
lines by grouping multiple commands under a single top-level parser. Climax
support these easily:

    import climax

    @climax.group()
    def main():
        pass

    @main.command()
    @climax.argument('values', type=int, nargs='+', help='sequence of numbers to add')
    def add(values):
        """add numbers"""
        print(sum(values))

    @main.command()
    @climax.argument('values', type=int, nargs='+', help='sequence of numbers to average')
    def avg(values):
        """average numbers"""
        print(sum(values) / len(values))

    if __name__ == '__main__':
        main()

Note that to link a command to its parent group, the `command` decorator is
obtained from the group function (i.e. `@main.command` instead of
`@climax.command`).

Without any arguments, this script generates the following output:

    $ python sumavg.py
    usage: sumavg.py [-h] {add,avg} ...
    sumavg.py: error: too few arguments

The `--help` now generates information about the group of commands:

    $ python sumavg.py --help
    usage: sumavg.py [-h] {add,avg} ...

    positional arguments:
      {add,avg}
        add       add numbers
        avg       average numbers

    optional arguments:
      -h, --help  show this help message and exit

And each command generates its own help messages as well:

    $ python sumavg.py add
    usage: sumavg.py add [-h] values [values ...]
    sumavg.py add: error: the following arguments are required: values

    $ python sumavg.py add --help
    usage: sumavg.py add [-h] values [values ...]

    positional arguments:
      values      sequence of numbers to add

    optional arguments:
      -h, --help  show this help message and exit

## Other Useful Features

### Options vs. Arguments

Argparse does not make a distinction between options and arguments, positional
and optional arguments are considered arguments. In climax, the
`@climax.argument` and `@climax.option` decorators are equivalent, so they can
be used according to your preference.

### Contexts

In the command group example above, there is a function associated with the
group, called `main`. If arguments are defined at this level, they will apply
to all the commands in the group. When a command is invoked, climax first
calls the group function with its arguments, and then calls the appropriate
command function.

Consider, for example, a `--verbose` option, which applies to all commands in
a group:

    @climax.group()
    @climax.argument('--verbose', action='store_true')
    def main(verbose):
        return {'verbose': verbose}

After the group function processes its arguments, it may need to communicate
some state to the command function that will run after it. For this purpose,
the group function can return a dictionary with values that will be sent as
arguments into the command function, in addition to the arguments generated
by argparse.

To support verbosity, the sum function can then be coded as follows:

    @main.command()
    @climax.argument('values', type=int, nargs='+', help='sequence of numbers to add')
    def add(values, verbose):
        """add numbers"""
        if verbose:
            print('The input values are: ', str(values))
        print(sum(values))

### Return Values

You have seen in the previous section that the return value from a group
function is the context that is passed as arguments to the command function.
A command function can also return a value, which is returned to the caller.

    import climax

    @climax.command()
    @climax.argument('--count', type=int, help="how many times to repeat")
    @climax.argument('name', help="the name to repeat")
    def repeat(count, name):
        """This silly program repeats a name the given number of times."""
        for i in range(count):
            print(name)
        return count

    if __name__ == '__main__':
        result = main()
        # result now has the return value from the command

### Optional Commands

In Python 3.2 and older, argparse requires that a command name is specified
when using groups. Due to a bug, argparse versions that ship with Python 3.3
and newer lift that requirement, making it possible to specify a command line
in which no command from the group is selected.

If you are using Python 3.2, climax makes group commands required, like in the
older Python releases. To make commands in a group optional, the group can
be given the `required=False` argument:

    import climax

    @climax.group(required=False)
    def main():
        print('this is main')

    @main.command()
    def cmd()
        print('this is cmd')

With this example, the following command is valid:

    $ python main.py
    this is main

Note that optional commands do not work in Python releases before 3.3.

### Recursive Groups

Argparse supports multiple levels of commands and sub-commands. In climax,
multiple levels of groups can be built using the familiar decorator syntax.
Consider the following example:

    @climax.group()
    def main():
        pass

    @main.group()
    def level2a():
        pass

    @level2.command()
    def cmd1():
        pass

    @level2.command()
    def l2cmd2():
        pass

    @main.command()
    def level2b():
        pass

### Integration with argparse parsers

Climax's use of argparse is not magical. In fact, it is possible to attach a
regular argparse parser as a command in a climax group, by passing a `parser`
argument to the group decorator:

    @climax.group()
    def grp():
        pass

    parser = argparse.ArgumentParser('cmd1.py')
    parser.add_argument('--repeat', type=int)
    parser.add_argument('name')

    @grp.command(parser=parser)
    def cmd1(repeat, name):
        pass

The reverse is also possible. If you need to obtain the argparse parser
generated by climax to integrate it with another parser or to make custom
modifications to it, you can simply obtain it by invoking the `parser`
attribute on the corresponding function. In the above example, `grp.parser`
returns a fully built and ready to use parser.

## Advanced Features

Sorry to dissappoint you, but that's it. The goal of climax is to be simple
and lightweight, there are no advanced features. :) 
