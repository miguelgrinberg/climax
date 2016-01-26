#!/usr/bin/env python
import climax


@climax.group()
def main():
    pass


@main.command()
@climax.argument('values', type=int, nargs='+',
                 help='sequence of numbers to add')
def add(values):
    """add numbers"""
    print(sum(values))


@main.command()
@climax.argument('values', type=int, nargs='+',
                 help='sequence of numbers to average')
def avg(values):
    """average numbers"""
    print(sum(values) / len(values))


if __name__ == '__main__':
    main()
