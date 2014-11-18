import subprocess

from cliche.cli import cli, runserver, shell, upgrade
from cliche.orm import Base
from cliche.web.app import app


def test_cli(fx_cli_runner):
    """empty command"""
    result = fx_cli_runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Usage: cli' in result.output


def test_upgrade_empty_cmd(fx_cli_runner):
    result = fx_cli_runner.invoke(upgrade, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output


def test_upgrade_wrong_path():
    """wrong path"""
    p = subprocess.Popen(
        ['cliche', 'upgrade', '-c', 'invalid.cfg.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert 'Invalid value for "--config"' in err.decode('u8')
    assert exit_code == 2


def test_upgrade_fine_use_metadata(fx_cfg_yml_file_use_db_url):
    """work normally, no additional options"""
    Base.metadata.drop_all(bind=app.config['DATABASE_ENGINE'])
    app.config['DATABASE_ENGINE'].execute(
        "drop table if exists alembic_version;"
    )
    p = subprocess.Popen(
        ['cliche', 'upgrade', '-c', str(fx_cfg_yml_file_use_db_url)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert 'INFO  [alembic.migration]' in err.decode('u8')
    assert exit_code == 0


def test_upgrade_fine_use_alembic(fx_cfg_yml_file_use_db_url,
                                  fx_only_support_pgsql):
    """work normally, no additional options"""
    Base.metadata.drop_all(bind=app.config['DATABASE_ENGINE'])
    app.config['DATABASE_ENGINE'].execute(
        "drop table if exists alembic_version;"
    )
    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url),
            '27e81ea4d86'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert 'Running upgrade None -> 27e81ea4d86, Add people table' in \
        err.decode('u8')
    assert exit_code == 0

    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert 'Running upgrade 27e81ea4d86 -> 2d8b17e13d1, Add teams table' in \
        err.decode('u8')
    assert exit_code == 0


def test_upgrade_downgrade_fine_after_upgrade(fx_cfg_yml_file_use_db_url,
                                              fx_only_support_pgsql):
    """downgrade work normally after upgrade"""
    Base.metadata.drop_all(bind=app.config['DATABASE_ENGINE'])
    app.config['DATABASE_ENGINE'].execute(
        "drop table if exists alembic_version;"
    )
    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url),
            '27e81ea4d86'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.communicate()

    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.communicate()

    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url),
            '27e81ea4d86'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert 'Running downgrade 2d8b17e13d1 -> 27e81ea4d86, Add teams table' in \
           err.decode('u8')
    assert exit_code == 0


def test_upgrade_downgrade_fail_after_upgrade(fx_cfg_yml_file_use_db_url,
                                              fx_only_support_pgsql):
    """downgrade work incorrectly after upgrade"""
    Base.metadata.drop_all(bind=app.config['DATABASE_ENGINE'])
    app.config['DATABASE_ENGINE'].execute(
        "drop table if exists alembic_version;"
    )
    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url),
            '27e81ea4d86'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.communicate()

    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.communicate()

    p = subprocess.Popen(
        [
            'cliche',
            'upgrade',
            '-c',
            str(fx_cfg_yml_file_use_db_url),
            'zzzzzzzzzzz'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    exit_code = p.returncode
    assert "No such revision 'zzzzzzzzzzz'" in err.decode('u8')
    assert exit_code == 1


def test_shell_empty_cmd(fx_cli_runner):
    """empty command"""
    result = fx_cli_runner.invoke(shell, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output


def test_shell_wrong_path(fx_cli_runner):
    """give -c/--config but wrong path"""
    result = fx_cli_runner.invoke(shell, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output


def test_shell_fine(fx_cli_runner, fx_cfg_yml_file):
    # case 3: give -c/--config and correct path
    result = fx_cli_runner.invoke(shell, ['-c', str(fx_cfg_yml_file)])
    assert result.exit_code == 0
    assert '(InteractiveConsole)' in result.output


def test_runserver_empty_cmd(fx_cli_runner):
    """empty command"""
    result = fx_cli_runner.invoke(runserver, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output


def test_runserver_wrong_path(fx_cli_runner):
    """give -c/--config but wrong path"""
    result = fx_cli_runner.invoke(runserver, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output
