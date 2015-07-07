# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pOCCI',

    version='0.0.1',

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

    packages=find_packages(),

    install_requires=['pycurl'],

    entry_points={
        'console_scripts': [
            'pOCCI=pOCCI.CORE:main',
        ],
    },
)
