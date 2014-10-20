from cliche.cli import cli, runserver, shell, upgrade


def test_cli(fx_cli_runner):
    """empty command"""
    result = fx_cli_runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Usage: cli' in result.output


def test_upgrade_empty_cmd(fx_cli_runner):
    result = fx_cli_runner.invoke(upgrade, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output


def test_upgrade_wrong_path(fx_cli_runner):
    """wrong path"""
    result = fx_cli_runner.invoke(upgrade, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output


def test_upgrade_fine(fx_cli_runner, fx_cfg_yml_file):
    """work normally, no additional options"""
    result = fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_yml_file)])
    assert result.exit_code == 0
    assert 'INFO  [alembic.migration]' in result.output


def test_upgrade_downgrade_fine(fx_cli_runner, fx_cfg_yml_file):
    """downgrade work normally"""
    result = fx_cli_runner.invoke(upgrade,
                                  ['-c', str(fx_cfg_yml_file), '27e81ea4d86'])
    assert result.exit_code == 0
    assert 'Running upgrade None -> 27e81ea4d86' in result.output


def test_upgrade_downgrade_fail(fx_cli_runner, fx_cfg_yml_file):
    """downgrade work incorrectly"""
    result = fx_cli_runner.invoke(upgrade,
                                  ['-c', str(fx_cfg_yml_file), 'zzzzzzzzzzz'])
    assert result.exit_code == 1
    assert "No such revision 'zzzzzzzzzzz'" in result.output


def test_upgrade_downup_fine(fx_cli_runner, fx_cfg_yml_file):
    """down/upgrade work normally"""
    fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_yml_file), '27e81ea4d86'])
    result = fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_yml_file)])
    assert result.exit_code == 0
    assert 'INFO  [alembic.migration]' in result.output


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
