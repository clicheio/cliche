from setuptools import find_packages, setup


setup(
    name='cliche',
    version='0.1.0',
    author='The Cliche team',
    url='http://cliche.io/',
    license='AGPLv3 or later',
    packages=find_packages(),
    install_requires=['lxml >= 3.3.5'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: '
        'GNU Affero General Public License v3 or later (AGPLv3+)',
    ]
)
