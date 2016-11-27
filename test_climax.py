from __future__ import print_function

import argparse
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import unittest
try:
    from unittest import mock
except ImportError:
    import mock
import sys

import coverage

cov = coverage.coverage()
cov.start()

import climax


class TestClips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        cov.stop()
        cov.report(include='climax.py')

    def setUp(self):
        self.stdout_patcher = mock.patch('argparse._sys.stdout',
                                         new_callable=StringIO)
        self.stdout = self.stdout_patcher.start()
        self.stderr_patcher = mock.patch('argparse._sys.stderr',
                                         new_callable=StringIO)
        self.stderr = self.stderr_patcher.start()

    def tearDown(self):
        self.stdout_patcher.stop()
        self.stderr_patcher.stop()

    def _reset_stdout(self):
        self.stdout.truncate(0)
        self.stdout.seek(0)

    def _reset_stderr(self):
        self.stderr.truncate(0)
        self.stderr.seek(0)

    def test_simple_command(self):
        @climax.command()
        def cmd():
            print('foo')
            return 123

        result = cmd([])
        self.assertEqual(self.stdout.getvalue(), 'foo\n')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertTrue(isinstance(cmd.parser, argparse.ArgumentParser))
        self.assertEqual(result, 123)

    def test_command_with_arguments(self):
        @climax.command()
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        @climax.argument('--long-name')
        @climax.argument('--other-name', dest='third_name')
        def cmd(repeat, name, long_name, third_name):
            for i in range(repeat):
                print(name, long_name, third_name)

        cmd(['--repeat', '3', 'foo', '--long-name', 'foobaz', '--other-name', 'baz'])
        self.assertEqual(self.stdout.getvalue(), 'foo foobaz baz\nfoo foobaz baz\nfoo foobaz baz\n')
        self.assertEqual(self.stderr.getvalue(), '')

    def test_subcommand_with_arguments(self):
        @climax.group()
        def grp():
            pass

        @grp.command()
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        @climax.argument('--long-name')
        @climax.argument('--other-name', dest='third_name')
        def cmd(repeat, name, long_name, third_name):
            for i in range(repeat):
                print(name, long_name, third_name)

        grp(['cmd', '--repeat', '3', 'foo', '--long-name', 'foobaz', '--other-name', 'baz'])
        self.assertEqual(self.stdout.getvalue(), 'foo foobaz baz\nfoo foobaz baz\nfoo foobaz baz\n')
        self.assertEqual(self.stderr.getvalue(), '')

    def test_group(self):
        @climax.group()
        @climax.argument('--foo', type=int)
        def grp(foo):
            print(foo)

        @grp.command()
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        def cmd1(repeat, name):
            for i in range(repeat):
                print(name)

        @grp.command('customname')
        def cmd2():
            print('cmd2')
            return 123

        result = grp(['--foo', '123', 'cmd1', '--repeat', '3', 'foo'])
        self.assertEqual(self.stdout.getvalue(), '123\nfoo\nfoo\nfoo\n')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result, None)

        self._reset_stdout()
        self._reset_stderr()

        result = grp(['--foo', '321', 'customname'])
        self.assertEqual(self.stdout.getvalue(), '321\ncmd2\n')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result, 123)

    def test_group_with_external_argparse(self):
        @climax.group()
        @climax.argument('--foo', type=int)
        def grp(foo):
            print(foo)
            return {'bar': foo}

        parser = argparse.ArgumentParser('cmd1.py')
        parser.add_argument('--repeat', type=int)
        parser.add_argument('name')

        @grp.command(parser=parser)
        def cmd1(**kwargs):
            for i in range(kwargs['repeat']):
                print(kwargs['name'])
            print(kwargs['bar'])

        @grp.command()
        def cmd2(bar):
            print(bar)

        parser3 = argparse.ArgumentParser('cmd3.py')
        parser3.add_argument('--repeat', type=int)
        parser3.add_argument('name')

        @grp.command(parser=parser3)
        def cmd3(repeat, name):
            for i in range(repeat):
                print(name)

        grp(['--foo', '123', 'cmd1', '--repeat', '3', 'foo'])
        self.assertEqual(self.stdout.getvalue(), '123\nfoo\nfoo\nfoo\n123\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        grp(['--foo', '321', 'cmd2'])
        self.assertEqual(self.stdout.getvalue(), '321\n321\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        self.assertRaises(TypeError, grp, ['--foo', '123', 'cmd3', '--repeat',
                                           '3', 'foo'])

    def test_multilevel_groups(self):
        @climax.group()
        def main():
            print('main')
            return {'main': True}

        @main.command()
        def cmd1(main):
            print('cmd1', main)

        @main.group('cmdtwo')
        @climax.argument('--foo', action='store_true')
        def cmd2(foo, main):
            print('cmd2', foo, main)
            return {'main': True, 'cmd2': True}

        @cmd2.command()
        @climax.argument('--bar', action='store_false')
        def cmd2a(bar, main, cmd2):
            print('cmd2a', bar, main, cmd2)

        @cmd2.command()
        def cmd2b(main, cmd2):
            print('cmd2b', main, cmd2)

        @main.group()
        def cmd3(main, cmd3):
            print('cmd3', main, cmd3)
            return {'main': True, 'cmd3': True}

        main(['cmd1'])
        self.assertEqual(self.stdout.getvalue(), 'main\ncmd1 True\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        self.assertRaises(SystemExit, main, ['cmdtwo'])
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertIn('too few arguments', self.stderr.getvalue())

        self._reset_stdout()
        self._reset_stderr()

        self.assertRaises(SystemExit, main, ['cmdtwo', '--foo'])
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertIn('too few arguments', self.stderr.getvalue())

        self._reset_stdout()
        self._reset_stderr()

        main(['cmdtwo', 'cmd2a'])
        self.assertEqual(self.stdout.getvalue(),
                         'main\ncmd2 False True\ncmd2a True True True\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        main(['cmdtwo', 'cmd2a', '--bar'])
        self.assertEqual(self.stdout.getvalue(),
                         'main\ncmd2 False True\ncmd2a False True True\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        main(['cmdtwo', '--foo', 'cmd2b'])
        self.assertEqual(self.stdout.getvalue(),
                         'main\ncmd2 True True\ncmd2b True True\n')
        self.assertEqual(self.stderr.getvalue(), '')

        self._reset_stdout()
        self._reset_stderr()

        self.assertRaises(SystemExit, main, ['cmdtwo', 'cmd2b', '--baz'])
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertIn('unrecognized arguments: --baz', self.stderr.getvalue())

    @unittest.skipIf(sys.version_info < (3, 3), 'only supported in Python 3.3+')
    def test_group_with_no_subcommand(self):
        @climax.group(required=False)
        @climax.argument('--foo', type=int)
        def grp(foo):
            print(foo)

        @grp.command()
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        def cmd1(repeat, name):
            for i in range(repeat):
                print(name)

        grp(['--foo', '123'])
        self.assertEqual(self.stdout.getvalue(), '123\n')
        self.assertEqual(self.stderr.getvalue(), '')

    @mock.patch('climax.getpass.getpass', return_value='secret')
    def test_password_prompt(self, getpass):
        @climax.command()
        @climax.argument('--password', action=climax.PasswordPrompt)
        def pw(password):
            print(password)

        pw(['--password'])
        self.assertEqual(self.stdout.getvalue(), 'secret\n')
        self.assertEqual(self.stderr.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
