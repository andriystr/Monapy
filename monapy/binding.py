# -*- coding: utf-8 -*-
''' Simple monad implementation. '''

from itertools import chain
from functools import partial
from functools import reduce


class Binder:
    '''
    Binder is binding functions to chain.
    The result of the previous function is passed to a next function as positional argument.
    Right arrows bind functions into the chain.
    Left arrows set positional argument for last function in chain.
    ##### Examples:
        >>> from monapy import Binder
        >>> binder = Binder() >> range >> map << ( lambda i: i * 10 )
        >>> list( binder( 10 ) )
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        >>> binder >> filter << ( lambda i: not i % 20 ) >> list
        >>> binder( 10 )
        [0, 20, 40, 60, 80]
    '''
    def __init__(self):
        self._func_chain = []

    def __rshift__(self, obj):
        ''' call to Binder.bind '''
        return self.bind(obj)

    def __lshift__(self, obj):
        ''' call to Binder.lbind '''
        return self.lbind(obj)

    def __call__(self, *args, **kwargs):
        ''' call to Binder.call '''
        return self.call(*args, **kwargs)

    def bind(self, obj):
        ''' bind a function (callable object) with last function in the chain '''
        if hasattr(obj, '__call__'):
            self._func_chain.append(obj)
        else:
            raise TypeError('Must be callable')
        return self

    def lbind(self, obj):
        ''' set positional argument for last function in the chain '''
        _func = self._func_chain.pop()
        self._func_chain.append(partial(_func, obj))
        return self

    def call(self, *args, **kwargs):
        ''' call to functions chain '''
        if not self._func_chain:
            if args:
                return args[0]
            else:
                return
        first_func = self._func_chain[0]
        other_funcs = self._func_chain[1:]
        return reduce(
            lambda val, func: func(val),
            chain(
                [first_func(*args, **kwargs)],
                other_funcs
            )
        )
