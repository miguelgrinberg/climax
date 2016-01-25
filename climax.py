import argparse
from functools import wraps
from functools import partial


class _CopiedArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that copies everything from an existing
    ArgumentParser object. Used as a helper when building groups with
    sub-commands.
    """
    def __init__(self, *args, **kwargs):
        parser = kwargs.pop('parser')
        super(_CopiedArgumentParser, self).__init__(*args, **kwargs)
        for k,v in vars(parser).items():
            setattr(self,k,v)


def command(*args, **kwargs):
    """Decorator to define a command.

    The arguments to this decorator are those of the
    `ArgumentParser <https://docs.python.org/3/library/argparse.html\
#argumentparser-objects>`_
    object constructor.
    """
    def decorator(f):
        if 'description' not in kwargs:
            kwargs['description'] = f.__doc__
        f.parser = argparse.ArgumentParser(*args, **kwargs)
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])

        @wraps(f)
        def wrapper(args=None):
            kwargs = f.parser.parse_args(args)
            return f(**vars(kwargs))
        return wrapper
    return decorator


def _subcommand(group=None, *args, **kwargs):
    """Decorator to define a subcommand.

    This decorator is used for the group's @command decorator.
    """
    def decorator(f):
        if 'help' not in kwargs:
            kwargs['help'] = f.__doc__
        _parser_class = group._subparsers._parser_class
        if 'parser' in kwargs:
            # use a copy of the given parser
            group._subparsers._parser_class = _CopiedArgumentParser
        f.parser = group._subparsers.add_parser(*args, **kwargs)
        group._subparsers._parser_class = _parser_class
        f.parser.set_defaults(_func=f)
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])
        return f
    return decorator


def group(*args, **kwargs):
    """Decorator to define a command group.

    The arguments to this decorator are those of the
    `ArgumentParser <https://docs.python.org/3/library/argparse.html\
#argumentparser-objects>`_
    object constructor.
    """
    def decorator(f):
        f.parser = argparse.ArgumentParser(*args, **kwargs)
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])
        f._subparsers = f.parser.add_subparsers()
        f.command = partial(_subcommand, f)

        @wraps(f)
        def wrapper(args=None):
            parsed_args = vars(f.parser.parse_args(args))

            # call the group function
            filtered_args = {arg: parsed_args[arg] for arg in f._argnames
                             if arg in parsed_args}
            f(**filtered_args)

            # call the sub-command function
            _func = parsed_args.pop('_func')
            try:
                # try with all the arguments first
                _func(**parsed_args)
            except TypeError:
                # else send only the sub-command arguments if they are known
                if not isinstance(_func.parser, _CopiedArgumentParser):
                    filtered_args = {arg: parsed_args[arg]
                                     for arg in getattr(_func, '_argnames', [])
                                     if arg in parsed_args}
                    _func(**filtered_args)
                else:
                    # we don't know the list of arguments for this parser,
                    # probably because it is an external one
                    raise
        return wrapper
    return decorator


def argument(*args, **kwargs):
    """Decorator to define an argparse option or argument.

    The arguments to this decorator are the same as the
    `ArgumentParser.add_argument <https://docs.python.org/3/library/\
argparse.html#the-add-argument-method>`_
    method.
    """
    def decorator(f):
        if getattr(f, '_arguments', None) is None:
            f._arguments = []
        if getattr(f, '_argnames', None) is None:
            f._argnames = []
        f._arguments.append((args, kwargs))
        for argname in args:
            if argname.startswith('--'):
                f._argnames.append(argname[2:])
            else:
                f._argnames.append(argname)
        return f
    return decorator


def option(*args, **kwargs):
    """Decorator define an argparse option or argument.

    Functionally equivalent to the ``argument`` decorator.
    """
    return argument(*args, **kwargs)