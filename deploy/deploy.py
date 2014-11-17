#!/usr/bin/env python3
import argparse
import errno
import os
import pathlib
import shutil
import subprocess
import sys

from yaml import load, dump


tmp = pathlib.Path('/tmp')


def main():
    parser = argparse.ArgumentParser(description='Deploy cliche.io.')
    parser.add_argument('-b', '--build-number', nargs=1, required=True,
                        help='Build number which will be deployed.')
    parser.add_argument('-c', '--config-template', nargs=1, required=True,
                        help='Template of config file to be deployed.')
    parser.add_argument('-d', '--db-host', nargs=1, required=True,
                        help='Database host address to use.')
    parser.add_argument('--db-username', nargs=1,
                        help='OPTIONAL: Database username to use.')
    parser.add_argument('--db-password', nargs=1,
                        help='OPTIONAL: Database password to use.')
    parser.add_argument('-i', '--identity', nargs=1,
                        help='SSH identity file to use.')
    parser.add_argument('-r', '--redis-host', nargs=1, required=True,
                        help='Redis cache host address to use.')
    parser.add_argument('--redis-password', nargs=1,
                        help='OPTIONAL: Redis cache host password to use.')
    parser.add_argument('--sentry-dsn', nargs=1,
                        help='OPTIONAL: Sentry DSN to use.')
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
        config = load(config_data)

    config['database_url'] = 'postgresql+psycopg2://'
    if args.db_username is not None and args.db_username[0] is not None:
        config['database_url'] += args.db_username[0]
    if args.db_password is not None and args.db_password[0] is not None:
        config['database_url'] += ':' + args.db_password[0]
    if (args.db_username is not None and args.db_username[0] is not None) or \
       (args.db_password is not None and args.db_password[0] is not None):
        config['database_url'] += '@'
    config['database_url'] += '{}/cliche?sslmode=require' \
                              .format(args.db_host[0].rpartition('@')[2])

    config['broker_url'] = 'redis://'
    if args.redis_password is not None and \
       args.redis_password[0] is not None:
        config['broker_url'] += ':' + args.redis_password[0] + '@'
    config['broker_url'] += '{}/1' \
                            .format(args.redis_host[0].rpartition('@')[2])

    if args.sentry_dsn is not None and \
       args.sentry_dsn[0] is not None:
        config['SENTRY_DSN'] = args.sentry_dsn[0]
        config['uwsgi']['env'] = 'SENTRY_DSN={}'.format(args.sentry_dsn[0])

    if args.identity is not None and args.identity[0] is not None:
        args.identity[0] = os.path.abspath(args.identity[0])

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
            str(workdir / 'deploy' / 'tmp' / 'etc'),
            str(workdir / 'deploy' / 'tmp' / 'scripts'),
        ]
    )

    gitdir = workdir / '.git'

    with (gitdir / 'HEAD').open('r') as head:
        content = head.readline()
        if content.startswith('ref:'):
            with (gitdir / content.split()[1]).open('r') as head_file:
                revision = (args.build_number[0] + '_' +
                            head_file.readline().strip())
        else:
            revision = args.build_number[0] + '_' + content.strip()

    with (workdir /
          'deploy' /
          'tmp' /
          'etc' /
          'revision.txt').open('w') as revision_file:
        revision_file.write(revision + '\n')

    venv_dir = pathlib.Path('/home/cliche/venv_{}'.format(revision))

    subprocess.check_call(
        [
            'python',
            'setup.py',
            'egg_info',
            '-b',
            '_{}'.format(revision),
            'bdist_wheel',
        ]
    )

    if args.beat is not None and args.beat[0] is not None:
        print('Uploading beat to ' + args.beat[0])
        upload(args.beat[0], revision, config, workdir, args.identity)
        execute_remote_script(
            args.beat[0], revision, 'prepare-common.sh', args.identity
        )
        execute_remote_script(
            args.beat[0], revision, 'upgrade-common.py', args.identity
        )

    for crawler in args.crawler or []:
        print('Uploading crawler to ' + crawler[0])
        upload(crawler[0], revision, config, workdir, args.identity)
        execute_remote_script(
            crawler[0], revision, 'prepare-common.sh', args.identity
        )
        execute_remote_script(
            crawler[0], revision, 'upgrade-common.py', args.identity
        )

    for web_worker in args.web_worker or []:
        print('Uploading web worker to ' + web_worker[0])
        upload(web_worker[0], revision, config, workdir, args.identity)
        execute_remote_script(
            web_worker[0], revision, 'prepare-common.sh', args.identity
        )
        execute_remote_script(
            web_worker[0], revision, 'prepare-web.sh', args.identity
        )
        execute_remote_script(
            web_worker[0], revision, 'upgrade-common.py', args.identity
        )
        execute_remote_script(
            web_worker[0], revision, 'upgrade-web.py', args.identity
        )

    if args.beat is not None and args.beat[0] is not None:
        print('Stopping beat at ' + args.beat[0])
        ssh(
            args.beat[0],
            [
                'stop',
                'cliche-celery-beat',
            ],
            args.identity
        )

    for crawler in args.crawler or []:
        print('Stopping crawler on ' + crawler[0])
        ssh(
            crawler[0],
            [
                'stop',
                'cliche-celery-worker',
            ],
            args.identity
        )

    for web_worker in args.web_worker or []:
        print('Stopping web worker on ' + web_worker[0])
        ssh(
            web_worker[0],
            [
                'stop',
                'cliche-uwsgi',
            ],
            args.identity
        )

    if args.beat is not None and args.beat[0] is not None:
        print('Migrating database on beat at ' + args.beat[0])
        check_ssh(
            args.beat[0],
            [
                'sudo',
                '-ucliche',
                str(venv_dir / 'bin' / 'cliche'),
                'upgrade',
                '-c',
                str(venv_dir / 'etc' / 'prod.cfg.yml'),
            ],
            args.identity
        )

    for crawler in args.crawler or []:
        print('Migrating database on crawler at ' + crawler[0])
        check_ssh(
            crawler[0],
            [
                'sudo',
                '-ucliche',
                str(venv_dir / 'bin' / 'cliche'),
                'upgrade',
                '-c',
                str(venv_dir / 'etc' / 'prod.cfg.yml'),
            ],
            args.identity
        )

    for web_worker in args.web_worker or []:
        print('Migrating database on web worker at ' + web_worker[0])
        check_ssh(
            web_worker[0],
            [
                'sudo',
                '-ucliche',
                str(venv_dir / 'bin' / 'cliche'),
                'upgrade',
                '-c',
                str(venv_dir / 'etc' / 'prod.cfg.yml'),
            ],
            args.identity
        )

    for web_worker in args.web_worker or []:
        print('Starting web worker on ' + web_worker[0])
        ssh(
            web_worker[0],
            [
                'start',
                'cliche-uwsgi',
            ],
            args.identity
        )

    if args.beat is not None and args.beat[0] is not None:
        print('Starting beat at ' + args.beat[0])
        ssh(
            args.beat[0],
            [
                'start',
                'cliche-celery-beat',
            ],
            args.identity
        )

    for crawler in args.crawler or []:
        print('Starting crawler on ' + crawler[0])
        ssh(
            crawler[0],
            [
                'start',
                'cliche-celery-worker',
            ],
            args.identity
        )

    if args.beat is not None and args.beat[0] is not None:
        print('Promoting beat at ' + args.beat[0])
        execute_remote_script(
            args.beat[0], revision, 'promote-common.py', args.identity
        )
        execute_remote_script(
            args.beat[0], revision, 'promote-beat.py', args.identity
        )

    for crawler in args.crawler or []:
        print('Promoting crawler at ' + crawler[0])
        execute_remote_script(
            crawler[0], revision, 'promote-common.py', args.identity
        )
        execute_remote_script(
            crawler[0], revision, 'promote-crawler.py', args.identity
        )

    for web_worker in args.web_worker or []:
        print('Promoting web worker at ' + web_worker[0])
        execute_remote_script(
            web_worker[0], revision, 'promote-common.py', args.identity
        )
        execute_remote_script(
            web_worker[0], revision, 'promote-web.py', args.identity
        )


def upload(address, revision, config, workdir, identity):
    with (workdir /
          'deploy' /
          'tmp' /
          'etc' /
          'prod.cfg.yml').open('w') as f:
        print(dump(config), file=f)
    subprocess.check_call(
        [
            'cp',
            str(list((workdir / 'dist').glob('*.whl'))[0]),
            str(workdir / 'deploy' / 'tmp'),
        ]
    )
    subprocess.check_call(
        [
            'cp',
        ] +
        [str(path) for path in ((workdir / 'deploy' / 'scripts').glob('*'))] +
        [
            str(workdir / 'deploy' / 'tmp' / 'scripts'),
        ]
    )
    subprocess.check_call(
        [
            'cp',
        ] +
        [str(path) for path in ((workdir / 'deploy' / 'etc').glob('*'))] +
        [
            str(workdir / 'deploy' / 'tmp' / 'etc'),
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
    check_scp(
        [
            str(workdir /
                'deploy' /
                'cliche-deploy-{}.tar.gz'.format(revision)),
            address + ':' + str(tmp),
        ],
        identity
    )
    check_ssh(
        address,
        [
            'mkdir',
            '-p',
            str(tmp / revision),
        ],
        identity
    )
    check_ssh(
        address,
        [
            'tar',
            'Cxvf',
            str(tmp / revision),
            str(tmp / 'cliche-deploy-{}.tar.gz'.format(revision)),
        ],
        identity
    )
    check_ssh(
        address,
        [
            'chmod',
            '+x',
            str(tmp / revision / 'scripts' / '*.sh'),
            str(tmp / revision / 'scripts' / '*.py'),
        ],
        identity
    )


def execute_remote_script(address, revision, script_name, identity):
    check_ssh(
        address,
        [
            str(tmp / revision / 'scripts' / script_name)
        ],
        identity
    )


def ssh(address, command_list, identity):
    return subprocess.call(
        build_ssh_command(address, command_list, identity)
    )


def check_ssh(address, command_list, identity):
    return subprocess.check_call(
        build_ssh_command(address, command_list, identity)
    )


def build_ssh_command(address, command_list, identity):
    command = [
        'ssh',
        '-o',
        'StrictHostKeyChecking=no',
    ]
    if identity is not None and identity[0] is not None:
        command += ['-i', identity[0]]
    return command + [address] + command_list


def check_scp(args, identity):
    command = [
        'scp',
        '-o',
        'StrictHostKeyChecking=no',
    ]
    if identity is not None and identity[0] is not None:
        command += ['-i', identity[0]]
    return subprocess.check_call(command + args)


if __name__ == '__main__':
    main()
