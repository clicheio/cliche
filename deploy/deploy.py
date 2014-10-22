#!/usr/bin/env python3
import argparse
import errno
import os
import pathlib
import shutil
import subprocess
import sys

import yaml


tmp = pathlib.Path('/tmp')


def main():
    parser = argparse.ArgumentParser(description='Deploy cliche.io.')
    parser.add_argument('-b', '--build-number', nargs=1, required=True,
                        help='Build number which will be deployed.')
    parser.add_argument('-c', '--config-template', nargs=1, required=True,
                        help='Template of config file to be deployed.')
    parser.add_argument('-d', '--db-host', nargs=1, required=True,
                        help='Database host address to use. '
                             'Username for db installation may also be '
                             'provided with.')
    parser.add_argument('-r', '--redis-host', nargs=1, required=True,
                        help='Redis cache host address to use. '
                             'Username for redis installation may also be '
                             'provided with.')
    parser.add_argument(
        '--crawler', action='append', nargs=1,
        help="""
             Server to be deployed as crawler.
             It should be declared with every other server.
             For example: --crawler user@server1
             -c user@server2...
             """
    )
    parser.add_argument(
        '--web-worker', action='append', nargs=1,
        help="""
             Server to be deployed as web worker.
             It should be declared with every other server.
             For example: --web-worker user@server1
             -w user@server2...
             """
    )
    parser.add_argument(
        '--beat', nargs=1,
        help="""
             Server to be deployed as beat server.
             It should be declared only once.
             For example: --beat user@server1
             """
    )
    args = parser.parse_args()

    workdir = pathlib.Path(__file__).resolve().parent.parent

    try:
        config_file = pathlib.Path(args.config_template[0]).resolve()
        if not config_file.is_file():
            raise FileNotFoundError
    except FileNotFoundError:
        print('Config file given does not exist.')
        sys.exit(errno.EPERM)

    with config_file.open('r') as config_data:
        config = yaml.load(config_data)

    config['database_url'] = 'postgres://{}/cliche' \
                             .format(args.db_host[0].rpartition('@')[2])

    config['broker_url'] = 'redis://{}/1' \
                           .format(args.redis_host[0].rpartition('@')[2])

    os.chdir(str(workdir))

    subprocess.check_call(
        [
            'python',
            'setup.py',
            'clean',
        ]
    )

    try:
        shutil.rmtree(str(workdir / 'dist'))
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(str(workdir / 'deploy' / 'tmp'))
    except FileNotFoundError:
        pass

    subprocess.check_call(
        [
            'mkdir',
            '-p',
            str(workdir / 'deploy' / 'tmp' / 'etc')
        ]
    )

    gitdir = workdir / '.git'

    with (gitdir / 'HEAD').open('r') as head:
        with (gitdir / head.readline().split()[1]).open('r') as head_file:
            revision = (args.build_number[0] + '_' +
                        head_file.readline().strip())

    with (workdir /
          'deploy' /
          'tmp' /
          'etc' /
          'revision.txt').open('w') as revision_file:
        revision_file.write(revision + '\n')

    subprocess.check_call(
        [
            'python',
            'setup.py',
            'egg_info',
            '-b',
            '_{}'.format(revision),
            'bdist_wheel'
        ]
    )

    if args.beat is not None and args.beat[0] is not None:
        print('Uploading beat to ' + args.beat[0])
        upload(args.beat[0], revision, config, workdir)
        execute_remote_script(args.beat[0], revision, 'prepare.sh')
        execute_remote_script(args.beat[0], revision, 'upgrade.py')

    for crawler in args.crawler or []:
        print('Uploading crawler to ' + crawler[0])
        upload(crawler[0], revision, config, workdir)
        execute_remote_script(crawler[0], revision, 'prepare.sh')
        execute_remote_script(crawler[0], revision, 'upgrade.py')

    for web_worker in args.web_worker or []:
        print('Uploading web worker to ' + web_worker[0])
        upload(web_worker[0], revision, config, workdir)
        execute_remote_script(web_worker[0], revision, 'prepare.sh')
        execute_remote_script(web_worker[0], revision, 'upgrade.py')

    if args.beat is not None and args.beat[0] is not None:
        print('Promoting beat at ' + args.beat[0])
        execute_remote_script(args.beat[0], revision, 'promote.py')

    for crawler in args.crawler or []:
        print('Promoting crawler at ' + crawler[0])
        execute_remote_script(crawler[0], revision, 'promote.py')

    for web_worker in args.web_worker or []:
        print('Promoting web worker at ' + web_worker[0])
        execute_remote_script(web_worker[0], revision, 'promote.py')


def upload(address, revision, config, workdir):
    with (workdir /
          'deploy' /
          'tmp' /
          'etc' /
          'prod.cfg.yml').open('w') as f:
        print(yaml.dump(config), file=f)
    subprocess.check_call(
        [
            'cp',
            str(list((workdir / 'dist').glob('*.whl'))[0]),
            str(workdir / 'deploy' / 'tmp')
        ]
    )
    subprocess.check_call(
        [
            'cp'
        ] +
        [str(path) for path in ((workdir / 'deploy' / 'scripts').glob('*'))] +
        [
            str(workdir / 'deploy' / 'tmp' / 'scripts')
        ]
    )
    subprocess.check_call(
        [
            'cp'
        ] +
        [str(path) for path in ((workdir / 'deploy' / 'etc').glob('*'))] +
        [
            str(workdir / 'deploy' / 'tmp' / 'etc')
        ]
    )
    subprocess.check_call(
        [
            'tar',
            'cvfz',
            str(workdir /
                'deploy' /
                'cliche-deploy-{}.tar.gz'.format(revision))
        ] + [str(path.relative_to(workdir / 'deploy' / 'tmp'))
             for path in ((workdir / 'deploy' / 'tmp').glob('*'))],
        cwd=str(workdir / 'deploy' / 'tmp')
    )
    subprocess.check_call(
        [
            'scp',
            str(workdir /
                'deploy' /
                'cliche-deploy-{}.tar.gz'.format(revision)),
            address + ':' + str(tmp)
        ]
    )
    subprocess.check_call(
        [
            'ssh',
            address,
            'mkdir',
            '-p',
            str(tmp / revision)
        ]
    )
    subprocess.check_call(
        [
            'ssh',
            address,
            'tar',
            'Cxvf',
            str(tmp / revision),
            str(tmp /
                'cliche-deploy-{}.tar.gz'.format(revision))
        ]
    )
    subprocess.check_call(
        [
            'ssh',
            address,
            'chmod',
            '+x',
            str(tmp / revision / 'scripts' / 'prepare.sh'),
            str(tmp / revision / 'scripts' / 'upgrade.py'),
            str(tmp / revision / 'scripts' / 'promote.py')
        ]
    )


def execute_remote_script(address, revision, script_name):
    subprocess.check_call(
        [
            'ssh',
            address,
            str(tmp / revision / 'scripts' / script_name)
        ]
    )


if __name__ == '__main__':
    main()
