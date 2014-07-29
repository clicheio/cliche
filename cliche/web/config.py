""":mod:`cliche.web.config` --- Reading configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Config
from yaml import load

__all__ = {'config_from_yaml'}


def config_from_yaml(config, *, string=None, file=None, filename=None):
    """Read Flask app configuration from YAML.  ::

        config_from_yaml(app.config, filename='dev.yml')

    :param config: pass :attr:`Flask.config <flask.Flask.config>` attribute
                   to this parameter
    :type config: :class:`flask.Config`

    """
    if not isinstance(config, Config):
        raise TypeError('expected a {0.__module__}.{0.__qualname__}, not '
                        '{1!r}'.format(Config, config))
    args_number = sum(a is not None for a in {string, file, filename})
    if args_number > 1:
        raise TypeError('it takes a keyword at a time; keywords are '
                        'exclusive to each other')
    elif not args_number:
        raise TypeError('missing keyword')
    elif string is not None:
        if not isinstance(string, str):
            raise TypeError('expected a string, not ' + repr(string))
        dictionary = load(string)
    elif file is not None:
        if not callable(getattr(file, 'read', None)):
            raise TypeError('expected a file-like object, not ' + repr(file))
        dictionary = load(file)
    else:
        if not isinstance(filename, str):
            raise TypeError('expected a filename string, not ' +
                            repr(filename))
        with open(filename) as f:
            dictionary = load(f)
    config.update((k.upper(), v) for k, v in dictionary.items())
