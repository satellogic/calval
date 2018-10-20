import os
import sys
from setuptools import setup, find_packages

version = '0.1.3'

proj_dir = os.path.abspath(os.path.dirname(__file__))
reqs = [line.strip()
        for line in open(
                os.path.join(proj_dir, 'requirements.txt'), encoding='utf-8')]
install_requires = [req.split('#egg=')[-1].replace('-', '==')
                    if '#egg=' in req else req
                    for req in reqs]
dependency_links = [req for req in reqs if 'git+' in req]
# Hack, for py37, use unreleased version of pyproj
# This also requires installing cython in the .travis.yml,
# and some `extras_require` entry (see below)
if sys.version_info[:2] == (3, 7):
    dependency_links.append(
        'git+https://github.com/jswhit/pyproj.git@master#egg=pyproj-1.9.5.2.dev11'
    )
print('install_requires=', install_requires)
print('dependency_links=', dependency_links)

setup(
    name='calval',
    version=version,
    author='Slava Kerner, Amit Aronovitch',
    url='https://github.com/satellogic/calval',
    author_email='amit@satellogic.com',
    description="Python package for easy radiometric calibration&validation of satellite EO payloads",
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    packages=find_packages(),
    package_data={
        'calval': ['site_data/*']
    },
    install_requires=install_requires,
    # hacks specific for python versions:
    extras_require={
        'azure_storage': [
            'azure-storage-blob'
        ],
        ':python_version == "3.7"': [
            # pypi version does not support py37
            # Note: 1.9.5.2 is not released yet: this is a hack to force usage of dependency-link
            'pyproj>=1.9.5.2.dev11'
        ]
    },
    dependency_links=dependency_links
)
