from flask import Flask

from cliche.web.config import config_from_yaml


config_yaml = '''
debug: true
secret_key: secret
database_url: sqlite:///
'''


def test_config_from_yaml_string():
    app = Flask(__name__)
    config_from_yaml(app.config, string=config_yaml)
    _assert_config(app)


def test_config_from_yaml_file(tmpdir):
    app = Flask(__name__)
    f = tmpdir.join('test_file.yml')
    f.write(config_yaml)
    with f.open() as stream:
        config_from_yaml(app.config, file=stream)
        _assert_config(app)


def test_config_from_yaml_filename(tmpdir):
    app = Flask(__name__)
    f = tmpdir.join('test_filename.yml')
    f.write(config_yaml)
    config_from_yaml(app.config, filename=str(f))
    _assert_config(app)


def _assert_config(app):
    assert app.debug
    assert app.secret_key == 'secret'
    assert app.config['DATABASE_URL'] == 'sqlite:///'
