#! /bin/sh -xe
version='1.0.3'

echo "__version__ = '${version}'" > pOCCI/version.py
vim LICENSE
git commit -m "Release ${version}"
python setup.py sdist
python setup.py test
twine upload dist/pOCCI-${version}.tar.gz
git tag -a v${version} -m "Release ${version}."
git push --tags origin HEAD

# documentation
pandoc -t rst < README.md > README.rst || :
make html || :
