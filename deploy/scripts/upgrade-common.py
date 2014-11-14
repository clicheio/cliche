#!/usr/bin/python3
import errno
import pathlib
import platform
import sys
import subprocess

from yaml import load, dump


def main():
    dist = platform.dist()
    if dist[0] != 'debian' and dist[0] != 'Ubuntu':
        print('This script can only be run on Debian GNU/Linux or Ubuntu.')
        sys.exit(errno.EPERM)

    workdir = pathlib.Path(__file__).resolve().parent.parent
    with (workdir / 'etc' / 'revision.txt').open('r') as revision_file:
        revision = (revision_file.readline().strip())
    venv_dir = pathlib.Path('/home/cliche/venv_{}'.format(revision))

    subprocess.check_call(
        [
            'sudo',
            'mv',
            '/tmp/cliche-deploy-{}.tar.gz'.format(revision),
            '/home/cliche',
        ]
    )

    subprocess.check_call(
        [
            'sudo',
            '-ucliche',
            'virtualenv',
            '-p',
            subprocess.check_output(
                [
                    'sudo',
                    '-ucliche',
                    'which',
                    'python3.4',
                ],
                universal_newlines=True
            ).strip(),
            str(venv_dir),
        ]
    )

    subprocess.check_call(
        [
            'sudo',
            '-ucliche',
            'mkdir',
            '-p',
            str(venv_dir / 'etc'),
        ]
    )

    subprocess.check_call(
        [
            'sudo',
            '-ucliche',
            'cp',
        ] +
        [str(path) for path in (workdir / 'etc').glob('*')] +
        [
            str(venv_dir / 'etc'),
        ]
    )

    subprocess.check_call(
        [
            'sudo',
            '-ucliche',
            str(venv_dir / 'bin' / 'pip'),
            'install',
            'redis',
        ]
    )

    subprocess.check_call(
        [
            'sudo',
            '-ucliche',
            str(venv_dir / 'bin' / 'pip'),
            'install',
            str(list(workdir.glob('*.whl'))[0]),
        ]
    )

    with (venv_dir / 'etc' / 'prod.cfg.yml').open('r') as config_data:
        config = load(config_data)

    config['uwsgi']['virtualenv'] = str(venv_dir)

    with (venv_dir / 'etc' / 'prod.cfg.yml').open('w') as f:
        print(dump(config), file=f)


if __name__ == '__main__':
    main()
