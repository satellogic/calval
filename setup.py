import os
from setuptools import setup, find_packages

version = '0.1.0.dev0'

proj_dir = os.path.abspath(os.path.dirname(__file__))
reqs = [line.strip()
        for line in open(
                os.path.join(proj_dir, 'requirements.txt'), encoding='utf-8')]

setup(
    name='calval',
    version=version,
    author='Slava Kerner, Amit Aronovitch',
    url='https://github.com/satellogic/calval',
    author_email='amit@satellogic.com',
    description="""\
Python package for easy radiometric calibration&validation of satellite EO payloads
""",
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
    package_data = {
        'calval': ['site_data/*']
    },
    install_requires=reqs
)
