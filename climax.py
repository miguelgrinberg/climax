import argparse
from functools import wraps
from functools import partial
import getpass


class _CopiedArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that copies everything from an existing
    ArgumentParser object. Used as a helper when building groups with
    sub-commands.
    """
    def __init__(self, *args, **kwargs):
        parser = kwargs.pop('parser')
        super(_CopiedArgumentParser, self).__init__(*args, **kwargs)
        for k, v in vars(parser).items():
            setattr(self, k, v)


class PasswordPrompt(argparse.Action):
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 0
        super(PasswordPrompt, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        setattr(namespace, self.dest, getpass.getpass())


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
        f.climax = True
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])

        @wraps(f)
        def wrapper(args=None):
            kwargs = f.parser.parse_args(args)
            return f(**vars(kwargs))

        wrapper.func = f
        return wrapper
    return decorator


def _subcommand(group, *args, **kwargs):
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
        if args == ():
            f.parser = group._subparsers.add_parser(f.__name__, **kwargs)
        else:
            f.parser = group._subparsers.add_parser(*args, **kwargs)
        f.parser.set_defaults(**{'_func_' + group.__name__: f})
        f.climax = 'parser' not in kwargs
        group._subparsers._parser_class = _parser_class
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])
        return f
    return decorator


def _subgroup(group, *args, **kwargs):
    """Decorator to define a subgroup.

    This decorator is used for the group's @group decorator.
    """
    def decorator(f):
        f.required = kwargs.pop('required', True)
        if 'help' not in kwargs:
            kwargs['help'] = f.__doc__
        if args == ():
            f.parser = group._subparsers.add_parser(f.__name__, **kwargs)
        else:
            f.parser = group._subparsers.add_parser(*args, **kwargs)
        f.parser.set_defaults(**{'_func_' + group.__name__: f})
        f.climax = True
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])
        f._subparsers = f.parser.add_subparsers()
        f.command = partial(_subcommand, f)
        f.group = partial(_subgroup, f)
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
        f.required = kwargs.pop('required', True)
        f.parser = argparse.ArgumentParser(*args, **kwargs)
        f.climax = True
        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])
        f._subparsers = f.parser.add_subparsers()
        f.command = partial(_subcommand, f)
        f.group = partial(_subgroup, f)

        @wraps(f)
        def wrapper(args=None):
            parsed_args = vars(f.parser.parse_args(args))

            # in Python 3.3+, sub-commands are optional by default
            # so required parsers need to be validated by hand here by
            func = f
            while '_func_' + func.__name__ in parsed_args:
                func = parsed_args.get('_func_' + func.__name__)
            if getattr(func, 'required', False):
                f.parser.error('too few arguments')

            # call the group function
            filtered_args = {arg: parsed_args[arg]
                             for arg in parsed_args.keys()
                             if arg in getattr(f, '_argnames', [])}
            parsed_args = {arg: parsed_args[arg] for arg in parsed_args.keys()
                           if arg not in filtered_args}
            ctx = f(**filtered_args)

            # call the sub-command function (or chain)
            func = f
            while '_func_' + func.__name__ in parsed_args:
                func = parsed_args.pop('_func_' + func.__name__)
                if getattr(func, 'climax', False):
                    filtered_args = {arg: parsed_args[arg]
                                     for arg in parsed_args.keys()
                                     if arg in getattr(func, '_argnames', [])}
                    parsed_args = {arg: parsed_args[arg]
                                   for arg in parsed_args.keys()
                                   if arg not in filtered_args}
                else:
                    # we don't have our metadata for this subparser, so we
                    # send all remaining args to it
                    filtered_args = parsed_args
                    parsed_args = {}
                filtered_args.update(ctx or {})
                ctx = func(**filtered_args)
            return ctx
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
