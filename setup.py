"""Packaging settings."""
import sys
import re
from codecs import open
from os.path import abspath, dirname, join

from setuptools import setup, find_packages


# check python version
if not sys.version_info >= (3, 5):
    sys.exit("Sorry, but this tool can be used with Python 3.5 or more")

# current path
this_dir = abspath(dirname(__file__))

# grab project version
with open(join(this_dir, 'ncsales', '__init__.py'), 'r', 'utf-8') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

# read long description
with open(join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='ncsales',
    version=version,
    description=('NCSales is a hypothetical scoring engine for sales leads.'),
    long_description=long_description,
    url='https://github.com/AlexLisovoy/ncsales.git',
    author='Alex Lisovoy',
    author_email='lisovoy.a.s@gmail.com',
    license='MIT',
    packages=find_packages('ncsales'),
    tests_require=['nose'],
    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'ncsales=ncsales.cli:main',
        ],
    },
    include_package_data=True,
)
