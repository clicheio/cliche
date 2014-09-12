from alembic.util import CommandError
from click import echo

from cliche.cli import cli, crawl, runserver, shell, upgrade


def test_cli(fx_cli_runner):
    # case 1: empty command
    result = fx_cli_runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Usage: cli' in result.output


def test_upgrade(fx_cli_runner, fx_cfg_py_file, monkeypatch):
    def fine_get_database_engine():
        return object

    def fail_get_database_engine():
        raise RuntimeError('works!')

    def fine_upgrade_database(a, b):
        echo('upgrade_database works!')

    def fail_upgrade_database(a, b):
        raise CommandError('revision is head')

    def fine_downgrade_database(a, b):
        echo('downgrade_database works!')

    def fail_downgrade_database(a, b):
        raise CommandError('downgrade fail')

    # case 1: empty command
    result = fx_cli_runner.invoke(upgrade, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output

    # case 2: give -c/--config but wrong path
    result = fx_cli_runner.invoke(upgrade, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output

    # case 3: give -c/--config and correct path
    # case 3: raise RuntimeError
    monkeypatch.setattr('cliche.web.db.get_database_engine',
                        fail_get_database_engine)
    result = fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_py_file)])
    # assert result.exit_code == 0
    # assert 'RuntimeError: works!' in result.output

    # case 4: work normally
    monkeypatch.setattr('cliche.web.db.get_database_engine',
                        fine_get_database_engine)
    monkeypatch.setattr('cliche.orm.upgrade_database',
                        fine_upgrade_database)
    result = fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_py_file)])
    # assert result.exit_code == 0
    # assert 'upgrade_database works!' in result.output

    # case 5: work incorrectly
    monkeypatch.setattr('cliche.orm.upgrade_database',
                        fail_upgrade_database)
    result = fx_cli_runner.invoke(upgrade, ['-c', str(fx_cfg_py_file)])
    # assert result.exit_code == 0
    # assert 'CommandError: revision is head' in result.output

    # case 6: work normally - downgrade
    monkeypatch.setattr('cliche.orm.downgrade_database',
                        fine_downgrade_database)
    result = fx_cli_runner.invoke(upgrade,
                                  ['-c', str(fx_cfg_py_file), 'zzzzzzzzzzz'])
    # assert result.exit_code == 0
    # assert 'downgrade_database works!' in result.output

    # case 7: work incorrectly - downgrade
    monkeypatch.setattr('cliche.orm.downgrade_database',
                        fail_downgrade_database)
    result = fx_cli_runner.invoke(upgrade,
                                  ['-c', str(fx_cfg_py_file), 'zzzzzzzzzzz'])
    # assert result.exit_code == 0
    # assert 'CommandError: downgrade fail' in result.output


def test_crawl(fx_cli_runner, fx_cfg_py_file, monkeypatch):
    def fake_crawl(conf):
        echo('crawl works!')

    monkeypatch.setattr('cliche.services.tvtropes.crawler.crawl', fake_crawl)
    # case 1: empty command
    result = fx_cli_runner.invoke(crawl, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output

    # case 2: give -c/--config but wrong path
    result = fx_cli_runner.invoke(crawl, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output

    # case 3: give -c/--config and correct path
    result = fx_cli_runner.invoke(crawl, ['-c', str(fx_cfg_py_file)])
    # assert result.exit_code == 0  #  fix me!: expect
    # assert 'crawl works!' in result.output


def test_shell(fx_cli_runner, fx_cfg_py_file, monkeypatch):
    def code_interact(**kwargs):
        echo('code.interact works!')

    monkeypatch.setattr('code.interact', code_interact)

    # case 1: empty command
    result = fx_cli_runner.invoke(shell, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output

    # case 2: give -c/--config but wrong path
    result = fx_cli_runner.invoke(shell, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output

    # case 3: give -c/--config and correct path
    result = fx_cli_runner.invoke(shell, ['-c', str(fx_cfg_py_file),
                                          '--no-ipython', '--no-bpython'])
    assert result.exit_code == 0
    assert 'code.interact works!' in result.output


def test_runserver(fx_cli_runner, fx_cfg_py_file, monkeypatch):
    def run(*args, **kwargs):
        echo('flask.Flask.run works!')

    monkeypatch.setattr('flask.Flask.run', run)

    # case 1: empty command
    result = fx_cli_runner.invoke(runserver, [])
    assert result.exit_code == 1
    assert 'The -c/--config' in result.output

    # case 2: give -c/--config but wrong path
    result = fx_cli_runner.invoke(runserver, ['-c', 'invalid.cfg.py'])
    assert result.exit_code == 2
    assert 'Invalid value for "--config"' in result.output

    # case 3: give -c/--config and correct path
    result = fx_cli_runner.invoke(runserver, ['-c', str(fx_cfg_py_file)])
    assert result.exit_code == 0
    assert 'flask.Flask.run works!' in result.output
