#!/usr/bin/env python

from setuptools import setup

long_description = """
toot is a commandline tool for interacting with Mastodon social networks.
Allows posting text and media to the timeline, searching, following, muting
and blocking accounts and other actions.
Contains an experimental curses application for reading the timeline.
"""

setup(
    name='toot',
    version='0.22.0',
    description='Mastodon CLI client',
    long_description=long_description.strip(),
    author='Ivan Habunek',
    author_email='ivan@habunek.com',
    url='https://github.com/ihabunek/toot/',
    project_urls={
        'Documentation': 'https://toot.readthedocs.io/en/latest/',
        'Issue tracker': 'https://github.com/ihabunek/toot/issues/',
    },
    keywords='mastodon toot',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console :: Curses',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=['toot', 'toot.ui'],
    python_requires=">=3.4",
    install_requires=[
        "requests>=2.13,<3.0",
        "beautifulsoup4>=4.5.0,<5.0",
        "wcwidth>=0.1.7,<2.0",
    ],
    entry_points={
        'console_scripts': [
            'toot=toot.console:main',
        ],
    }
)
