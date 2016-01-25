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
        self.exit_patcher = mock.patch('argparse._sys.exit')
        self.exit = self.exit_patcher.start()

        self.stdout_patcher = mock.patch('argparse._sys.stdout',
                                         new_callable=StringIO)
        self.stdout = self.stdout_patcher.start()
        self.stderr_patcher = mock.patch('argparse._sys.stderr',
                                         new_callable=StringIO)
        self.stderr = self.stderr_patcher.start()

    def tearDown(self):
        self.exit_patcher.stop()
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

        cmd([])
        self.assertEqual(self.stdout.getvalue(), 'foo\n')
        self.assertTrue(isinstance(cmd.parser, argparse.ArgumentParser))

    def test_command_with_arguments(self):
        @climax.command()
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        def cmd(repeat, name):
            for i in range(repeat):
                print(name)

        cmd(['--repeat', '3', 'foo'])
        self.assertEqual(self.stdout.getvalue(), 'foo\nfoo\nfoo\n')

    def test_group(self):
        @climax.group()
        @climax.argument('--foo', type=int)
        def grp(foo):
            print(foo)

        @grp.command('cmd1')
        @climax.option('--repeat', type=int)
        @climax.argument('name')
        def cmd1(repeat, name):
            for i in range(repeat):
                print(name)

        @grp.command('cmd2')
        def cmd2():
            print('cmd2')

        grp(['--foo', '123', 'cmd1', '--repeat', '3', 'foo'])
        self.assertEqual(self.stdout.getvalue(), '123\nfoo\nfoo\nfoo\n')

        self._reset_stdout()
        self._reset_stderr()

        grp(['--foo', '321', 'cmd2'])
        self.assertEqual(self.stdout.getvalue(), '321\ncmd2\n')

    def test_group_with_external_argparse(self):
        @climax.group()
        @climax.argument('--foo', type=int)
        def grp(foo):
            print(foo)

        parser = argparse.ArgumentParser('cmd1.py')
        parser.add_argument('--repeat', type=int)
        parser.add_argument('name')

        @grp.command('cmd1', parser=parser)
        def cmd1(**kwargs):
            for i in range(kwargs['repeat']):
                print(kwargs['name'])
            print(kwargs['foo'])

        @grp.command('cmd2')
        def cmd2():
            print('cmd2')

        parser3 = argparse.ArgumentParser('cmd3.py')
        parser3.add_argument('--repeat', type=int)
        parser3.add_argument('name')

        @grp.command('cmd3', parser=parser3)
        def cmd3(repeat, name):
            for i in range(repeat):
                print(name)

        grp(['--foo', '123', 'cmd1', '--repeat', '3', 'foo'])
        self.assertEqual(self.stdout.getvalue(), '123\nfoo\nfoo\nfoo\n123\n')

        self._reset_stdout()
        self._reset_stderr()

        grp(['--foo', '321', 'cmd2'])
        self.assertEqual(self.stdout.getvalue(), '321\ncmd2\n')

        self._reset_stdout()
        self._reset_stderr()

        self.assertRaises(TypeError, grp, ['--foo', '123', 'cmd3', '--repeat',
                                           '3', 'foo'])


if __name__ == '__main__':
    unittest.main()
