#!/usr/bin/env python3
#
import sys

from setuptools import setup, find_packages

__doc__ = """
Use this software to program the frequency, ctcss, dcs and filters ont
the radio module SA818
"""
__author__ = "Fred C. (W6BSD)"
__version__ = '0.1.1'
__license__ = 'BSD'

py_version = sys.version_info[:2]
if py_version < (3, 5):
  raise RuntimeError('SA818 requires Python 3.5 or later')

setup(
  name='sa818',
  version=__version__,
  description='SA818 Programming Software',
  long_description=__doc__,
  url='https://github.com/0x9900/SA818/',
  license=__license__,
  author=__author__,
  author_email='w6bsd@bsdworld.org',
  py_modules=['sa818'],
  install_requires=['pyserial'],
  entry_points = {
    'console_scripts': ['sa818 = sa818:main'],
  },
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5'
  ],
)
