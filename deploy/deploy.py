#!/usr/bin/python3
import argparse
import os
import pathlib
import shutil
import subprocess


tmp = pathlib.Path('/tmp')


def main():
    parser = argparse.ArgumentParser(description='Deploy cliche.io.')
    parser.add_argument('-b', '--build-number', nargs=1, required=True,
                        help='Build number which will be deployed.')
    parser.add_argument(
        '-c', '--crawler', action='append', nargs=1,
        help="""
             Server to be deployed as crawler.
             It should be declared with every other server.
             For example: -c user@server1
             -c user@server2...
             """
    )
    parser.add_argument(
        '-w', '--web-worker', action='append', nargs=1,
        help="""
             Server to be deployed as web worker.
             It should be declared with every other server.
             For example: -w user@server1
             -w user@server2...
             """
    )
    args = parser.parse_args()
    workdir = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(str(workdir))
    try:
        shutil.rmtree(str(workdir / 'dist'))
    except FileNotFoundError:
        pass
    gitdir = workdir / '.git'
    with (gitdir / 'HEAD').open('r') as head:
        with (gitdir / head.readline().split()[1]).open('r') as head_file:
            revision = (args.build_number[0] + '_' +
                        head_file.readline().strip())
    with (workdir / 'deploy' / 'revision.txt').open('w') as revision_file:
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

    for crawler in args.crawler or []:
        print('Uploading crawler to ' + crawler[0])
        upload(crawler[0], revision, workdir)
        execute_remote_script(crawler[0], revision, 'prepare.sh')
        execute_remote_script(crawler[0], revision, 'upgrade.sh')

    for web_worker in args.web_worker or []:
        print('Uploading web worker to ' + web_worker[0])
        upload(web_worker[0], revision, workdir)
        execute_remote_script(web_worker[0], revision, 'prepare.sh')
        execute_remote_script(web_worker[0], revision, 'upgrade.sh')

    for crawler in args.crawler or []:
        print('Promoting crawler at ' + crawler[0])
        execute_remote_script(crawler[0], revision, 'promote.py')

    for web_worker in args.web_worker or []:
        print('Promoting web worker at ' + web_worker[0])
        execute_remote_script(web_worker[0], revision, 'promote.py')


def upload(address, revision, workdir):
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
            'scp',
            str(workdir / 'deploy' / 'prepare.sh'),
            str(workdir / 'deploy' / 'upgrade.sh'),
            str(workdir / 'deploy' / 'promote.py'),
            str(workdir / 'deploy' / 'apt-requirements.txt'),
            str(workdir / 'deploy' / 'revision.txt'),
            str(workdir / 'deploy' / 'cliche.io'),
            str((workdir / 'dist').glob('*.whl')[0]),
            address + ':' + str(tmp / revision)
        ]
    )
    subprocess.check_call(
        [
            'ssh',
            address,
            'chmod',
            '+x',
            str(tmp / revision / 'prepare.sh'),
            str(tmp / revision / 'upgrade.sh'),
            str(tmp / revision / 'promote.py')
        ]
    )


def execute_remote_script(address, revision, script_name):
    subprocess.check_call(
        [
            'ssh',
            address,
            str(tmp / revision / script_name)
        ]
    )


if __name__ == '__main__':
    main()
