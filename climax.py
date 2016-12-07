import argparse
from functools import wraps
from functools import partial
import getpass
from gettext import gettext as _


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


def _get_parent_parsers(parents):
    """
    Return ArgumentParser instances from list of climax
    commands or ArgumentParser instances

    """
    return [f.parser if hasattr(f, 'parser') else f for f in parents]


def _get_climax_parents(parents):
    """
    Return list of climax commands

    """
    return [f for f in parents if hasattr(f, 'parser')]


def _get_args(f, parsed_args):
    """
    Return arguments that apply to f and remainder arguments that don't

    """
    filtered_args = {arg: parsed_args[arg]
                     for arg in parsed_args.keys()
                     if arg in getattr(f, '_argnames', [])}
    remainder_args = {arg: parsed_args[arg] for arg in parsed_args.keys()
                   if arg not in filtered_args}
    return filtered_args, remainder_args


def _process_parents(f, parents):
    """
    Attach parents to the command or group and append raw parser
    arguments to the command's argnames

    """
    f.parents = _get_climax_parents(parents)
    # allow passing climax commands instead of ArgumentParser
    parent_parsers = _get_parent_parsers(parents)
    if getattr(f, '_argnames', None) is None:
        f._argnames = []
    f._argnames += [action.dest
                    for parent_parser in parent_parsers
                    for action in parent_parser._actions
                    if parent_parser not in {fp.parser for fp in f.parents}]
    return parent_parsers


def _get_parents_context(f, parsed_args):
    """
    Call climax parent commands and return a dict of contexts

    """
    ctx = {}
    if hasattr(f, 'parents'):
        for parent in f.parents:
            filtered_args, parsed_args = _get_args(parent, parsed_args)
            ctx[parent.__name__] = parent(filtered_args)
    return {k: v for k, v in ctx.items() if v is not None}


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
        if 'parents' in kwargs:
            f.parents = _get_climax_parents(kwargs['parents'])
            # allows passing climax commands instead of ArgumentParser
            kwargs['parents'] = _get_parent_parsers(kwargs['parents'])
        f.parser = argparse.ArgumentParser(*args, **kwargs)
        f.climax = True

        for arg in getattr(f, '_arguments', []):
            f.parser.add_argument(*arg[0], **arg[1])

        @wraps(f)
        def wrapper(args=None):
            parsed_args = args if isinstance(args, dict) else vars(f.parser.parse_args(args))
            filtered_args, parsed_args = _get_args(f, parsed_args)
            parent_ctx = _get_parents_context(f, parsed_args)
            filtered_args.update(parent_ctx)
            return f(**filtered_args)

        wrapper.func = f
        return wrapper
    return decorator


def parent(*args, **kwargs):
    """Decorator to define a parent command.

    This decorator provides a way to distinguish commands intended to be
    used as parents, and automatically removes help arguments.
    """
    kwargs['add_help'] = False
    return command(*args, **kwargs)


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
        if 'parents' in kwargs:
            kwargs['parents'] = _process_parents(f, kwargs['parents'])
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
        if 'parents' in kwargs:
            kwargs['parents'] = _process_parents(f, kwargs['parents'])
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
        if 'parents' in kwargs:
            kwargs['parents'] = _process_parents(f, kwargs['parents'])
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
            filtered_args, parsed_args = _get_args(f, parsed_args)
            parent_ctx = _get_parents_context(f, parsed_args)
            filtered_args.update(parent_ctx or {})
            group_ctx = f(**filtered_args)

            # call the sub-command function (or chain)
            func = f
            while '_func_' + func.__name__ in parsed_args:
                func = parsed_args.pop('_func_' + func.__name__)
                if getattr(func, 'climax', False):
                    filtered_args, parsed_args = _get_args(func, parsed_args)
                else:
                    # we don't have our metadata for this subparser, so we
                    # send all remaining args to it
                    filtered_args = parsed_args
                    parsed_args = {}
                parent_ctx = _get_parents_context(func, parsed_args)
                filtered_args.update(group_ctx or {})
                filtered_args.update(parent_ctx)
                group_ctx = func(**filtered_args)
            return group_ctx
        return wrapper
    return decorator


def _get_dest(*args, **kwargs):  # pragma: no cover
    """
    Duplicate argument names processing logic from argparse.

    argparse stores the variable in the namespace using the provided dest name,
    the first long option string, or the first short option string

    """
    prefix_chars = kwargs.get('prefix_chars', '-')
    # determine short and long option strings
    option_strings = []
    long_option_strings = []

    for option_string in args:
        # strings starting with two prefix characters are long options
        option_strings.append(option_string)
        if option_string[0] in prefix_chars:
            if len(option_string) > 1:
                if option_string[1] in prefix_chars:
                    long_option_strings.append(option_string)

    # infer destination, '--foo-bar' -> 'foo_bar' and '-x' -> 'x'
    dest = kwargs.get('dest', None)
    if dest is None:
        if long_option_strings:
            dest_option_string = long_option_strings[0]
        else:
            dest_option_string = option_strings[0]
        dest = dest_option_string.lstrip(prefix_chars)
        if not dest:
            msg = _('dest= is required for options like %r')
            raise ValueError(msg % option_string)
        dest = dest.replace('-', '_')

    # return the updated dest name
    return dest


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
        f._argnames.append(_get_dest(*args, **kwargs))
        return f
    return decorator


def option(*args, **kwargs):
    """Decorator define an argparse option or argument.

    Functionally equivalent to the ``argument`` decorator.
    """
    return argument(*args, **kwargs)
