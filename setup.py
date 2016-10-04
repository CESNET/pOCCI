# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

import pOCCI

here = path.abspath(path.dirname(__file__))
readme = path.join(here, 'README.md')

# Get the long description from the relevant file
# (convert to rst, if pandoc available)
try:
    import pypandoc
    long_description = pypandoc.convert(readme, 'rst')
except:
    long_description = open(readme, encoding='utf-8').read()

setup(
    name='pOCCI',

    version=pOCCI.__version__,

    description='OCCI Compliance Testing Tool',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/CESNET/pOCCI',

    # Author details
    author='CESNET',
    author_email='cloud@rt4.cesnet.cz',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: System :: Distributed Computing',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='OCCI cloud compliance testing pycurl',

    packages=find_packages(exclude=['doc', 'tests']),

    install_requires=['pycurl'],

    package_data={
        'pOCCI': [
            'pOCCI.cfg',
            'pOCCI.1',
            'pOCCI-parse.1',
        ],
        'tests': ['*/*.txt'],
    },

    entry_points={
        'console_scripts': [
            'pOCCI=pOCCI.pOCCI:main',
            'pOCCI-parse=pOCCI.pOCCI_parse:main',
        ],
    },

    test_suite='tests',

    use_2to3=True,
)
