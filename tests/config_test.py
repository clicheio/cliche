from pytest import mark, raises

from cliche.config import (ConfigDict, ConfigKeyError,
                           read_config, read_config_from_python,
                           read_config_from_yaml)


def test_config_dict():
    c = ConfigDict(A=1)
    assert c['A'] == 1
    with raises(ConfigKeyError):
        c['B']


def test_config_key_error():
    e = ConfigKeyError('key')
    assert isinstance(e, KeyError)
    assert str(e) == "missing configuration: 'key'"


config_yaml = '''
debug: true
secret_key: secret
database_url: sqlite:///
'''


def test_config_from_yaml_string():
    config = read_config_from_yaml(string=config_yaml)
    _assert_config(config)


def test_config_from_yaml_file(fx_tmpdir):
    f = fx_tmpdir / 'test_file.yml'
    with f.open('w') as fp:
        fp.write(config_yaml)
    with f.open() as stream:
        config = read_config_from_yaml(file=stream)
    _assert_config(config)


@mark.parametrize('read_func', [read_config_from_yaml, read_config])
def test_read_config_from_yaml_filename(read_func, fx_tmpdir):
    f = fx_tmpdir / 'test_filename.yml'
    with f.open('w') as fp:
        fp.write(config_yaml)
    config = read_func(filename=f)
    _assert_config(config)


config_py = '''
DEBUG = True
SECRET_KEY = 'secret'
DATABASE_URL = 'sqlite:///'
'''


def test_config_from_python_string():
    config = read_config_from_python(string=config_py)
    _assert_config(config)


def test_config_from_python_file(fx_tmpdir):
    f = fx_tmpdir / 'test_file.py'
    with f.open('w') as fp:
        fp.write(config_py)
    with f.open() as stream:
        config = read_config_from_python(file=stream)
    _assert_config(config)


@mark.parametrize('read_func', [read_config_from_python, read_config])
def test_read_config_from_python_filename(read_func, fx_tmpdir):
    f = fx_tmpdir / 'test_filename.py'
    with f.open('w') as fp:
        fp.write(config_py)
    config = read_func(filename=f)
    _assert_config(config)


def _assert_config(config):
    assert config['DEBUG']
    assert config['SECRET_KEY'] == 'secret'
    assert config['DATABASE_URL'] == 'sqlite:///'


def test_read_config(fx_tmpdir, recwarn):
    f = fx_tmpdir / 'test_filename.cfg'
    with f.open('w') as fp:
        fp.write(config_py)
    config = read_config(filename=f)
    _assert_config(config)
    w = recwarn.pop(RuntimeWarning)
    assert issubclass(w.category, RuntimeWarning)
