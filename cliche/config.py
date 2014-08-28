""":mod:`cliche.config` --- Reading configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import errno
import pathlib
import warnings

from yaml import load

__all__ = ('ConfigDict', 'ConfigKeyError', 'read_config',
           'read_config_from_python', 'read_config_from_yaml')


class ConfigDict(dict):
    """Almost the same to the built-in :class:`dict` except it raises
    :exc:`ConfigKeyError` instead of :exc:`KeyError` with finer error
    message.

    """

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise ConfigKeyError(key)


class ConfigKeyError(KeyError):
    """The exception raised when there's no such configured key, that
    is a subtype of built-in :exc:`KeyError`.

    """

    def __str__(self):
        return 'missing configuration: ' + super().__str__()


def read_config(filename):
    """Read Cliche app configuration from the given filename.  ::

        config = read_config(filename='dev.cfg.yml')

    Note that it takes only one keyword argument at a time.  All parameters
    are mutually exclusive for each other.

    :param filename: read config from a *filename* of yaml or
                     python source code
    :type filename: :class:`pathlib.Path`
    :returns: the parsed dictionary with uppercase keys
    :rtype: :class:`ConfigDict`

    """
    if not isinstance(filename, pathlib.Path):
        raise TypeError(
            'expected an instance of {0.__module__}.{0.__qualname__}'
            ', not {1!r}'.format(pathlib.Path, filename)
        )
    if filename.suffix in ('.yml', '.yaml'):
        return read_config_from_yaml(filename=filename)
    if filename.suffix != '.py':
        warnings.warn(
            'the suffix of {0} represents niether Python (.py) nor '
            'YAML (.yml/.yaml);  treat it as Python',
            RuntimeWarning, stacklevel=2
        )
    return read_config_from_python(filename=filename)


def read_config_from_yaml(*, string=None, file=None, filename=None):
    """Read Cliche app configuration from YAML.  ::

        config = read_config_from_yaml(filename='dev.cfg.yml')

    Note that it takes only one keyword argument at a time.  All parameters
    are mutually exclusive for each other.

    :param string: read config from a yaml string
    :type string: :class:`str`
    :param file: read config from a *file object* of yaml
    :param filename: read config from a *filename* of yaml
    :type filename: :class:`pathlib.Path`
    :returns: the parsed dictionary with uppercase keys
    :rtype: :class:`ConfigDict`

    """
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
        if not isinstance(filename, pathlib.Path):
            raise TypeError(
                'expected an instance of {0.__module__}.{0.__qualname__}'
                ', not {1!r}'.format(pathlib.Path, filename)
            )
        with filename.open() as f:
            dictionary = load(f)
    return ConfigDict((k.upper(), v) for k, v in dictionary.items())


def read_config_from_python(*, string=None, file=None, filename=None):
    """Read Cliche app configuration from Python code i.e. Flask-style
    configuration::

        config = read_config_from_python(filename='dev.cfg.py')

    Note that it takes only one keyword argument at a time.  All parameters
    are mutually exclusive for each other.

    :param string: read config from a python source code string
    :type string: :class:`str`
    :param file: read config from a *file object* of python source code
    :param filename: read config from a *filename* of python source code
    :type filename: :class:`pathlib.Path`
    :returns: the parsed dictionary with uppercase keys
    :rtype: :class:`collections.abc.Mapping`

    """
    args_number = sum(a is not None for a in {string, file, filename})
    if args_number > 1:
        raise TypeError('it takes a keyword at a time; keywords are '
                        'exclusive to each other')
    elif not args_number:
        raise TypeError('missing keyword')
    elif string is not None:
        if not isinstance(string, str):
            raise TypeError('expected a string, not ' + repr(string))
        filename = '<string>'
    elif file is not None:
        filename = getattr(file, 'name', '<file>')
        string = file.read()
    else:
        if not isinstance(filename, pathlib.Path):
            raise TypeError(
                'expected an instance of {0.__module__}.{0.__qualname__}'
                ', not {1!r}'.format(pathlib.Path, filename)
            )
        try:
            with filename.open() as f:
                string = f.read()
        except IOError as e:
            if e.errno in (errno.ENOENT, errno.EISDIR):
                e.strerror = 'unable to load configuration file ({})'.format(
                    e.strerror
                )
                raise
    config = {}
    exec(compile(string, str(filename), 'exec'), config)
    return ConfigDict((k, v) for k, v in config.items() if k.isupper())
