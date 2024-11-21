#!/usr/bin/env python3
#
# BSD 2-Clause License
#
# Copyright (c) 2022-2023 Fred W6BSD
# All rights reserved.
#

import sys

from setuptools import setup

__doc__ = """

## SA818 Programming

Use this software to program the frequency, ctcss, dcs and filters on
the radio module SA818

"""

__author__ = "Fred C. (W6BSD)"
__version__ = '0.2.9'
__license__ = 'BSD'

py_version = sys.version_info[:2]
if py_version < (3, 8):
  raise RuntimeError('SA818 requires Python 3.8 or later')


def readme():
  return open('README.md', 'r', encoding='utf-8').read()


def main():
  setup(
    name='sa818',
    version=__version__,
    description='SA818 Programming Software',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/0x9900/SA818/',
    license=__license__,
    author=__author__,
    author_email='w6bsd@bsdworld.org',
    py_modules=['sa818'],
    install_requires=['pyserial'],
    entry_points={
      'console_scripts': ['sa818 = sa818:main'],
    },
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.8',
      'Topic :: Communications :: Ham Radio',
    ],
  )


if __name__ == "__main__":
  main()
