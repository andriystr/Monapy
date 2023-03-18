# -*- coding: utf-8 -*-

'''
Python Library for declarative programming.
'''

import sys

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise ImportError('Python < 3.6 is unsupported.')

from .binding import Binder
from .step import Step

__title__ = 'Monapy'
__description__ = 'Python Library for declarative programming.'
__version__ = '0.6.0'
__author__ = 'Andriy Stremeluk'
__license__ = 'MIT'
__copyright__ = 'Copyright © 2020-2023 Andriy Stremeluk'

__all__ = ['Step', 'Binder']
