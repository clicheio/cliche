from cliche.config import read_config_from_python, read_config_from_yaml


config_yaml = '''
debug: true
secret_key: secret
database_url: sqlite:///
'''


def test_config_from_yaml_string():
    config = read_config_from_yaml(string=config_yaml)
    _assert_config(config)


def test_config_from_yaml_file(tmpdir):
    f = tmpdir.join('test_file.yml')
    f.write(config_yaml)
    with f.open() as stream:
        config = read_config_from_yaml(file=stream)
    _assert_config(config)


def test_config_from_yaml_filename(tmpdir):
    f = tmpdir.join('test_filename.yml')
    f.write(config_yaml)
    config = read_config_from_yaml(filename=str(f))
    _assert_config(config)


config_py = '''
DEBUG = True
SECRET_KEY = 'secret'
DATABASE_URL = 'sqlite:///'
'''


def test_config_from_python_string():
    config = read_config_from_python(string=config_py)
    _assert_config(config)


def test_config_from_python_file(tmpdir):
    f = tmpdir.join('test_file.py')
    f.write(config_py)
    with f.open() as stream:
        config = read_config_from_python(file=stream)
    _assert_config(config)


def test_config_from_python_filename(tmpdir):
    f = tmpdir.join('test_filename.py')
    f.write(config_py)
    config = read_config_from_python(filename=str(f))
    _assert_config(config)


def _assert_config(config):
    assert config['DEBUG']
    assert config['SECRET_KEY'] == 'secret'
    assert config['DATABASE_URL'] == 'sqlite:///'
