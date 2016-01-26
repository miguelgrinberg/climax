#!/usr/bin/env python
import climax


@climax.group()
def fakegit():
    pass


@fakegit.command()
@climax.argument('repo', help='the repository URL')
def clone(repo):
    """Clone a repository."""
    print('Cloning ' + repo)


@fakegit.command()
@climax.argument('--message', '-m', help='the commit message')
def commit(message):
    """Make a commit."""
    print('Committing with message ' + message)


@fakegit.group()
def remote():
    """Manage remotes."""
    pass


@remote.command('list')
def remote_list():
    """List remotes."""
    print('Listing remotes.')


@remote.command('add')
@climax.argument('name', help='the remote name')
@climax.argument('url', help='the remote url')
def remote_add(name, url):
    """Add a git remote."""
    print('Adding remote ' + name + ', ' + url)


@remote.command('remove')
@climax.argument('name', help='the remote name')
def remote_remove(name):
    """Remove a git remote."""
    print('Removing remote ' + name)


if __name__ == '__main__':
    fakegit()
