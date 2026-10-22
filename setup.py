#! /usr/bin/env python3

from setuptools import setup, find_packages

version = {}
with open('cmscout/version.py') as f:
    exec(f.read(), version)

setup(
    name='cmscout',
    version=version['__version__'],
    description='CMS vulnerability scanner',
    author='Mike Manzotti',
    maintainer='Andrei Trimbitas',
    # author_email='',
    url='https://github.com/creativeheadz/cmscout',
    license='GPL',
    packages=find_packages(),
    package_data={'': ['*.conf', '*.txt', '*.zip']},
    entry_points={'console_scripts': [
        'cmscout = cmscout.main:main',
    ]},
    install_requires=[
        #'package>=version'
    ])
