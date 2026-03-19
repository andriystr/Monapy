# -*- coding: utf-8 -*-

'''
Python Library for declarative programming.
'''

import sys

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise ImportError('Python < 3.6 is unsupported.')

from .binding import Binder
from .step import Step

__all__ = ['Step', 'Binder']
