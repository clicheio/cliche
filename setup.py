import os.path

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


install_requires = [
    'SQLAlchemy >= 0.9.0'
]


setup(
    name='Cliche',
    description='An ontology of fictional works',
    long_description=readme(),
    url='https://bitbucket.org/clicheio/cliche',
    author='Hong Minhee',
    author_email='minhee' '@' 'dahlia.kr',
    maintainer='Hong Minhee',
    maintainer_email='minhee' '@' 'dahlia.kr',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
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
