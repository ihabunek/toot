#!/usr/bin/env python

from setuptools import setup

long_description = """
Toot is a CLI and TUI tool for interacting with Mastodon instances from the
command line.

Allows posting text and media to the timeline, searching, following, muting
and blocking accounts and other actions.
"""

setup(
    name='toot',
    version='0.32.1',
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
    ],
    packages=['toot', 'toot.tui', 'toot.utils'],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.13,<3.0",
        "beautifulsoup4>=4.5.0,<5.0",
        "wcwidth>=0.1.7",
        "urwid>=2.0.0,<3.0",
    ],
    entry_points={
        'console_scripts': [
            'toot=toot.console:main',
        ],
    }
)
