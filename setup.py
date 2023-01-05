#!/usr/bin/env python3
#
import sys

from setuptools import setup

__doc__ = """

## SA818 Programming

Use this software to program the frequency, ctcss, dcs and filters ont
the radio module SA818

### Installation

```
$ pip install sa818
```

### Example

```
$ sa818 radio --frequency 145.230 --offset -.6 --ctcss 100
SA818: INFO: +DMOSETGROUP:0, RX frequency: 145.2300, TX frequency: 144.6300, ctcss: 100.0, squelch: 4, OK

$ sa818 volume --level 5
SA818: INFO: +DMOSETVOLUME:0 Volume level: 5
```

"""

__author__ = "Fred C. (W6BSD)"
__version__ = '0.2.2'
__license__ = 'BSD'

py_version = sys.version_info[:2]
if py_version < (3, 8):
  raise RuntimeError('SA818 requires Python 3.8 or later')

setup(
  name='sa818',
  version=__version__,
  description='SA818 Programming Software',
  long_description=__doc__,
  long_description_content_type='text/markdown',
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
    'Programming Language :: Python :: 3.8',
    'Topic :: Communications :: Ham Radio',
  ],
)
