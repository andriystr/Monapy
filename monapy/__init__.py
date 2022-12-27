# -*- coding: utf-8 -*-

'''
Python Library for build declarative tools.
'''

import sys

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise ImportError('Python < 3.6 is unsupported.')

from .binding import Binder
from .step import Step

__title__ = 'monapy'
__description__ = 'Foundation for creating declarative programming tools'
__version__ = '0.5.0'
__author__ = 'Andriy Stremeluk'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020 Andriy Stremeluk'

__all__ = ['Step', 'Binder']
