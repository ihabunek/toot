#!/usr/bin/env python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name='toot',
    version='0.15.0',
    description='Interact with Mastodon social networks from the command line.',
    long_description=long_description,
    author='Ivan Habunek',
    author_email='ivan@habunek.com',
    url='https://github.com/ihabunek/toot/',
    keywords='mastodon toot',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['toot'],
    install_requires=[
        "requests>=2.13,<3.0",
        "beautifulsoup4>=4.5.0,<5.0",
        "future>=0.16",
    ],
    entry_points={
        'console_scripts': [
            'toot=toot.console:main',
        ],
    }
)
