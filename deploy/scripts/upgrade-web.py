#!/usr/bin/python3
import errno
import pathlib
import platform
import sys
import subprocess


def main():
    dist = platform.dist()
    if dist[0] != 'debian' and dist[0] != 'Ubuntu':
        print('This script can only be run on Debian GNU/Linux or Ubuntu.')
        sys.exit(errno.EPERM)

    workdir = pathlib.Path(__file__).resolve().parent.parent

    subprocess.check_call(
        [
            'cp'
        ] +
        [str(path) for path in ((workdir / 'scripts').glob('*'))] +
        [
            str(workdir / 'deploy' / 'tmp' / 'scripts')
        ]
    )


if __name__ == '__main__':
    main()
