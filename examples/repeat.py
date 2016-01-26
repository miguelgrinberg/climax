#!/usr/bin/env python
import climax


@climax.command()
@climax.argument('--count', type=int, help="how many times to repeat")
@climax.argument('name', help="the name to repeat")
def repeat(count, name):
    "This silly program repeats a name the given number of times."""
    for i in range(count):
        print(name)

if __name__ == '__main__':
    repeat()
