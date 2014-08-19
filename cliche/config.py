""":mod:`cliche.config` --- Reading configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from yaml import load

__all__ = 'read_config_from_yaml',


def read_config_from_yaml(*, string=None, file=None, filename=None):
    """Read Cliche app configuration from YAML.  ::

        config = read_config_from_yaml(filename='dev.cfg.yml')

    Note that it takes only one keyword argument at a time.  All parameters
    are mutually exclusive for each other.

    :param string: read config from a yaml string
    :type string: :class:`str`
    :param file: read config from a *file object* of yaml
    :param filename: read config from a *filename* of yaml
    :type filename: :class:`str`
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
    return {k.upper(): v for k, v in dictionary.items()}
