import os
import pathlib
import shutil
import sys

from invoke import task, run
from invoke.exceptions import Failure
from yaml import load, dump
from yaml.parser import ParserError

NO_CONFIG_MESSAGE = '{key} is not provided in deploy config.'
tmp = pathlib.Path('/tmp')
script_dir = pathlib.Path(__file__).resolve().parent


@task
def clean():
    run('python {setup_py} clean'.format(
        setup_py=str(script_dir / 'setup.py')
    ))
    try:
        shutil.rmtree(str(script_dir / 'dist'))
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(str(script_dir / 'deploy' / 'tmp'))
    except FileNotFoundError:
        pass


@task
def deploy(build_number, deploy_config_file=None):
    """Deploy cliche.io via ssh."""
    clean()
    if deploy_config_file is None:
        deploy_config_file = str((script_dir / 'deploy.yml').resolve())

    deploy_config = retrieve_yml(deploy_config_file, "deploy config")

    ensure_key_exists('database_server', deploy_config, NO_CONFIG_MESSAGE)
    ensure_key_exists('redis_server', deploy_config, NO_CONFIG_MESSAGE)
    ensure_key_exists('config_template', deploy_config, NO_CONFIG_MESSAGE)

    config_file = pathlib.Path(deploy_config['config_template'])
    if deploy_config['config_template'][0] != '/':
        config_file = script_dir / config_file

    config = retrieve_yml(config_file, "config template")

    config['database_url'] = 'postgresql+psycopg2://'
    if 'database_user' in deploy_config:
        credentials_present = True
        config['database_url'] += deploy_config['database_user']
    if 'database_password' in deploy_config:
        credentials_present = True
        config['database_url'] += ':' + deploy_config['database_password']
    if credentials_present:
        config['database_url'] += '@'
    config['database_url'] += '{}/cliche?sslmode=require'.format(
        deploy_config['database_server'].rpartition('@')[2]
    )

    config['broker_url'] = 'redis://'
    if 'redis_password' in deploy_config:
        config['broker_url'] += ':' + deploy_config['redis_password'] + '@'
    config['broker_url'] += '{}/1'.format(
        deploy_config['redis_server'].rpartition('@')[2]
    )

    if 'sentry_dsn' in deploy_config:
        config['SENTRY_DSN'] = deploy_config['sentry_dsn']

    if 'ssh_identity' in deploy_config:
        deploy_config['ssh_identity'] = \
            os.path.abspath(deploy_config['ssh_identity'])
    else:
        deploy_config['ssh_identity'] = None

    os.chdir(str(script_dir))

    run('mkdir -p {}'.format(' '.join([
        str(script_dir / 'deploy' / 'tmp' / 'etc'),
        str(script_dir / 'deploy' / 'tmp' / 'scripts'),
    ])))

    with (script_dir / '.git' / 'HEAD').open('r') as head:
        content = head.readline()
        if content.startswith('ref:'):
            with (script_dir / '.git' / content.split()[1])\
                    .open('r') as head_file:
                revision = '{}_{}'.format(
                    build_number,
                    head_file.readline().strip()
                )
        else:
            revision = '{}_{}'.format(build_number, content.strip())

    with (script_dir /
          'deploy' /
          'tmp' /
          'etc' /
          'revision.txt').open('w') as revision_file:
        revision_file.write(revision + '\n')

    venv_dir = pathlib.Path('/home/cliche/venv_{}'.format(revision))

    run('python {setup_py} egg_info -b _{revision} bdist_wheel'.format(
        setup_py=str(script_dir / 'setup.py'),
        revision=revision,
    ))

    with (script_dir /
          'deploy' /
          'tmp' /
          'etc' /
          'prod.cfg.yml').open('w') as f:
        print(dump(config, default_flow_style=False), file=f)
    run('cp {} {}'.format(
        str(script_dir / 'dist' / '*.whl'),
        str(script_dir / 'deploy' / 'tmp'),
    ))
    run('cp {} {}'.format(
        str(script_dir / 'deploy' / 'scripts' / '*'),
        str(script_dir / 'deploy' / 'tmp' / 'scripts'),
    ))
    run('cp {} {}'.format(
        str(script_dir / 'deploy' / 'etc' / '*'),
        str(script_dir / 'deploy' / 'tmp' / 'etc'),
    ))
    run('tar cvfz {} -C {} {}'.format(
        str(script_dir / 'deploy' /
            'cliche-deploy-{}.tar.gz'.format(revision)),
        str(script_dir / 'deploy' / 'tmp'),
        '.'
    ))

    if 'beat_server' in deploy_config:
        print('Uploading beat to ' + deploy_config['beat_server'])
        upload(
            deploy_config['beat_server'],
            revision,
            config,
            script_dir,
            deploy_config['ssh_identity'],
        )
        execute_remote_script(
            deploy_config['beat_server'],
            revision,
            'prepare-common.sh',
            deploy_config['ssh_identity'],
        )
        execute_remote_script(
            deploy_config['beat_server'],
            revision,
            'upgrade-common.py',
            deploy_config['ssh_identity'],
        )

    if 'crawler' in deploy_config:
        for crawler in deploy_config['crawler']:
            print('Uploading crawler to ' + crawler)
            upload(
                crawler,
                revision,
                config,
                script_dir,
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                crawler,
                revision,
                'prepare-common.sh',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                crawler,
                revision,
                'upgrade-common.py',
                deploy_config['ssh_identity'],
            )

    if 'web' in deploy_config:
        for web_worker in deploy_config['web']:
            print('Uploading web worker to ' + web_worker)
            upload(
                web_worker,
                revision,
                config,
                script_dir,
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                web_worker,
                revision,
                'prepare-common.sh',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                web_worker,
                revision,
                'prepare-web.sh',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                web_worker,
                revision,
                'upgrade-common.py',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                web_worker,
                revision,
                'upgrade-web.py',
                deploy_config['ssh_identity'],
            )

    if 'beat_server' in deploy_config:
        print('Stopping beat at ' + deploy_config['beat_server'])
        ssh(
            deploy_config['beat_server'],
            'stop cliche-celery-beat',
            deploy_config['ssh_identity'],
        )

    if 'crawler' in deploy_config:
        for crawler in deploy_config['crawler']:
            print('Stopping crawler on ' + crawler)
            ssh(
                crawler,
                'stop cliche-celery-worker',
                deploy_config['ssh_identity'],
            )

    if 'web' in deploy_config:
        for web_worker in deploy_config['web']:
            print('Stopping web worker on ' + web_worker)
            ssh(
                web_worker,
                'stop cliche-uwsgi',
                deploy_config['ssh_identity'],
            )

    if 'beat_server' in deploy_config:
        print('Migrating database on beat at ' + deploy_config['beat_server'])
        check_ssh(
            deploy_config['beat_server'],
            'sudo -ucliche {} upgrade -c {}'.format(
                str(venv_dir / 'bin' / 'cliche'),
                str(venv_dir / 'etc' / 'prod.cfg.yml'),
            ),
            deploy_config['ssh_identity'],
        )

    if 'crawler' in deploy_config:
        for crawler in deploy_config['crawler']:
            print('Migrating database on crawler at ' + crawler)
            check_ssh(
                crawler,
                'sudo -ucliche {} upgrade -c {}'.format(
                    str(venv_dir / 'bin' / 'cliche'),
                    str(venv_dir / 'etc' / 'prod.cfg.yml'),
                ),
                deploy_config['ssh_identity'],
            )

    if 'web' in deploy_config:
        for web_worker in deploy_config['web']:
            print('Migrating database on web worker at ' + web_worker)
            check_ssh(
                web_worker,
                'sudo -ucliche {} upgrade -c {}'.format(
                    str(venv_dir / 'bin' / 'cliche'),
                    str(venv_dir / 'etc' / 'prod.cfg.yml'),
                ),
                deploy_config['ssh_identity'],
            )

    if 'web' in deploy_config:
        for web_worker in deploy_config['web']:
            print('Starting web worker on ' + web_worker)
            ssh(
                web_worker,
                'start cliche-uwsgi',
                deploy_config['ssh_identity'],
            )

    if 'beat_server' in deploy_config:
        print('Starting beat at ' + deploy_config['beat_server'])
        ssh(
            deploy_config['beat_server'],
            'start cliche-celery-beat',
            deploy_config['ssh_identity'],
        )

    if 'crawler' in deploy_config:
        for crawler in deploy_config['crawler']:
            print('Starting crawler on ' + crawler)
            ssh(
                crawler,
                'start cliche-celery-worker',
                deploy_config['ssh_identity'],
            )

    if 'beat_server' in deploy_config:
        print('Promoting beat at ' + deploy_config['beat_server'])
        execute_remote_script(
            deploy_config['beat_server'],
            revision, 'promote-common.py',
            deploy_config['ssh_identity'],
        )
        execute_remote_script(
            deploy_config['beat_server'],
            revision, 'promote-beat.py',
            deploy_config['ssh_identity'],
        )

    if 'crawler' in deploy_config:
        for crawler in deploy_config['crawler']:
            print('Promoting crawler at ' + crawler)
            execute_remote_script(
                crawler,
                revision,
                'promote-common.py',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                crawler,
                revision,
                'promote-crawler.py',
                deploy_config['ssh_identity'],
            )

    if 'web' in deploy_config:
        for web_worker in deploy_config['web']:
            print('Promoting web worker at ' + web_worker)
            execute_remote_script(
                web_worker,
                revision,
                'promote-common.py',
                deploy_config['ssh_identity'],
            )
            execute_remote_script(
                web_worker,
                revision,
                'promote-web.py',
                deploy_config['ssh_identity'],
            )


def upload(address, revision, config, workdir, identity):
    check_scp(
        '{} {}'.format(
            str(workdir / 'deploy' /
                'cliche-deploy-{}.tar.gz'.format(revision)),
            '{}:{}'.format(address, str(tmp))
        ),
        identity
    )
    check_ssh(
        address,
        'mkdir -p {}'.format(str(tmp / revision)),
        identity
    )
    check_ssh(
        address,
        'tar Cxvf {} {}'.format(
            str(tmp / revision),
            str(tmp / 'cliche-deploy-{}.tar.gz'.format(revision)),
        ),
        identity
    )
    check_ssh(
        address,
        'chmod +x {} {}'.format(
            str(tmp / revision / 'scripts' / '*.sh'),
            str(tmp / revision / 'scripts' / '*.py'),
        ),
        identity
    )


def execute_remote_script(address, revision, script_name, identity):
    return check_ssh(
        address,
        str(tmp / revision / 'scripts' / script_name),
        identity
    )


def ssh(address, command, identity=None):
    identity_option = ''
    if identity is not None:
        identity_option = '-i {identity}'.format(identity)
    return run(
        'ssh -o StrictHostKeyChecking=no '
        '{identity} {address} {command}'.format(
            identity=identity_option,
            address=address,
            command=command,
        )
    )


def check_ssh(address, command, identity=None):
    try:
        return ssh(address, command, identity)
    except Failure as e:
        print(e.result, file=sys.stderr)
        raise SystemExit(e.result.return_code)


def check_scp(args, identity):
    identity_option = ''
    if identity is not None:
        identity_option = '-i {identity}'.format(identity)
    return run('scp -o StrictHostKeyChecking=no {identity} {args}'.format(
        identity=identity_option,
        args=args,
    ))


def retrieve_yml(path, file_description):
    try:
        with pathlib.Path(path).open('r') as f:
            return load(f)
    except FileNotFoundError:
        print('The {} file you provided does not exist.'
              .format(file_description),
              file=sys.stderr)
        raise SystemExit(1)
    except IsADirectoryError:
        print('The {} file path you provided is a directory.'
              .format(file_description),
              file=sys.stderr)
        raise SystemExit(1)
    except ParserError:
        print('Error occured while parsing provided {} file.'
              .format(file_description),
              file=sys.stderr)
        raise SystemExit(1)
    except:
        print('Error occured while retrieving {}.'.format(file_description),
              file=sys.stderr)
        raise SystemExit(1)


def ensure_key_exists(key, set, message_template):
    if key not in set:
        print(message_template.format(key=key))
        raise SystemExit(1)
