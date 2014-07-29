import distutils.core
import os.path
import sys
import warnings

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
from setuptools.command.test import test


if sys.version_info < (3, 3, 0):
    warnings.warn(
        'Cliche requires Python 3.3 or higher; the currently running '
        'Python version is: ' + sys.version
    )


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


install_requires = {
    # Entity classes
    'SQLAlchemy >= 0.9.0',
    'alembic >= 0.6.0',
    # Configuration
    'PyYAML >= 3.10',
    # Web
    'Flask >= 0.10',
    'Werkzeug >= 0.9'
}

tests_require = {
    'pytest >= 2.5.0'
}

docs_require = {
    'Sphinx >= 1.2'
}


class BaseAlembicCommand(distutils.core.Command):
    """Base class for commands provided by Alembic."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            from cliche.cli import get_database_engine
            from cliche.orm import get_alembic_config, import_all_modules
            import_all_modules()
        except ImportError as e:
            raise ImportError('dependencies are not resolved yet; run '
                              '"setup.py develop" first\n' + str(e))
        engine = get_database_engine()
        config = get_alembic_config(engine)
        self.alembic_process(config)

    def alembic_process(self, config):
        raise NotImplementedError('override alembic_process() method')


class revision(BaseAlembicCommand):
    """Adds a new revision to the database migration history."""

    description = __doc__
    user_options = BaseAlembicCommand.user_options + [
        ('message=', 'm', 'Message string'),
        ('autogenerate', None, 'Populates revision script with candidate '
                               'migration operations, based on comparison '
                               'of database to model.')
    ]

    def initialize_options(self):
        BaseAlembicCommand.initialize_options(self)
        self.message = None
        self.autogenerate = False

    def alembic_process(self, config):
        from alembic.command import revision
        revision(config, self.message, self.autogenerate)


class history(BaseAlembicCommand):
    """List revisions of the database migration history."""

    description = __doc__

    def alembic_process(self, config):
        from alembic.command import history
        history(config)


class pytest(test):

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main
        errno = main(self.test_args)
        raise SystemExit(errno)


cmdclass = {}

try:
    __import__('pytest')
except ImportError:
    pass
else:
    cmdclass['test'] = pytest

try:
    __import__('alembic')
except ImportError:
    pass
else:
    cmdclass.update(
        revision=revision,
        history=history
    )


setup(
    name='Cliche',
    description='An ontology of fictional works',
    long_description=readme(),
    url='https://bitbucket.org/clicheio/cliche',
    author='Hong Minhee',
    author_email='minhee' '@' 'dahlia.kr',
    maintainer='Hong Minhee',
    maintainer_email='minhee' '@' 'dahlia.kr',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'cliche-migrate = cliche.cli:migrate'
        ]
    },
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'docs': docs_require,
        'tests': tests_require
    },
    cmdclass=cmdclass,
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Documentation',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ]
)
