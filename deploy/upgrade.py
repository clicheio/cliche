#!/usr/bin/python3
import errno
import platform
import sys


def main():
    dist = platform.dist()
    if dist[0] != 'debian' and dist[0] != 'Ubuntu':
        print('This script can only be run on Debian GNU/Linux or Ubuntu.')
        sys.exit(errno.EPERM)

    print('This is a stub.')


if __name__ == '__main__':
    main()
