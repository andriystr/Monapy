# -*- coding: utf-8 -*-

''' Foundation for creating declarative programming tools '''

import logging

from itertools import chain
from functools import reduce
from itertools import tee


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
fmt = logging.Formatter('%(name)s:line %(lineno)s:%(asctime)s:%(message)s')
handler.setFormatter(fmt)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


def to_step(step):
    '''
    Convert data structure to corresponding Step.
    '''
    if isinstance(step, Step):
        return step
    elif isinstance(step, tuple):
        return TupleStep(step)
    elif isinstance(step, list):
        return ListStep(step)
    elif isinstance(step, dict):
        return DictStep(step)
    elif isinstance(step, set):
        return SetStep(step)
    else:
        raise TypeError('to_step(%s), supports only tuple, list, dict and set.' % type(step))


class Step:
    '''Abstract class must be implement'''
    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __rshift__(self, next_step):
        return self.bind(next_step)

    def __lshift__(self, loop_step):
        return self.loop(loop_step)

    def __invert__(self):
        return self.union()

    def __or__(self, or_step):
        return self.or_bind(or_step)

    def __call__(self, value = object(), **kwargs):
        return self.make(value, **kwargs)

    def bind(self, next_step):
        '''Bind current step with other step'''
        return StepChain([self, next_step])

    def loop(self, loop_step):
        '''Make Loop Step from current step and other step'''
        return LoopStep(self, loop_step)

    def union(self):
        '''Combining current steps'''
        return self

    def or_bind(self, or_step):
        '''Make Or Step from current step and other step'''
        return OrChain([self, or_step])

    def _raw_tree(self, **kwargs):
        return ['%s()' % self.__class__.__name__]

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make_all(self, iterable, **kwargs):
        '''Method must be implement'''
        return (
            value
            for val in iterable
            for value in self.make(val, **kwargs)
        )

    def make(self, value = object(), **kwargs):
        '''Main method of Step, must be implement'''
        logger.warning('Calling %s.make' % self.__class__.__name__)
        return iter([])


class StepChain(Step):
    '''Step related from other steps by 'bind', it is implementing chain'''
    def __init__(self, steps):
        if not steps:
            raise ValueError('steps is empty')
        self._chain = list(map(to_step, steps))

    def __repr__(self):
        s = ' >> '.join(map(repr, self._chain))
        return '%s(%s)' % (self.__class__.__name__, s)

    def bind(self, next_step):
        '''Bind current step with other step'''
        self._chain.append(to_step(next_step))
        return self

    def loop(self, loop_step):
        '''Make Loop Step from current step and other step'''
        last_step = self._chain.pop()
        new_step = LoopStep(last_step, loop_step)
        self._chain.append(new_step)
        return self
        
    def union(self):
        '''Combining current steps'''
        return UnionStep(self)

    def _raw_tree(self, **kwargs):
        start_row = '%s(%s)' % (
            self.__class__.__name__,
            len(self._chain)
        )

        rows = [start_row]
        if not self._chain:
            return rows

        last_step = self._chain[-1]
        chain = self._chain[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step'''
        if not self._chain:
            return

        iterable = reduce(
            lambda iterable, step: step.make_all(iterable, **kwargs),
            chain([[value]], self._chain)
        )
        for val in iterable:
            yield val


class LoopStep(Step):
    '''Step related from other steps by 'loop', it is implementing chain'''
    def __init__(self, step, loop):
        self._step = to_step(step)
        self._loop_step = to_step(loop)

    def __repr__(self):
        s = '%s << %s' % (self._step, self._loop_step)
        return '%s(%s)' % (self.__class__.__name__, s)

    def bind(self, next_step):
        '''Bind current step with other step'''
        return StepChain([self, next_step])
        
    def union(self):
        '''Combining current steps'''
        return UnionStep(self)

    def _raw_tree(self, **kwargs):
        start_row = '%s()' % self.__class__.__name__

        rows = [start_row]

        last_step = self._loop_step

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        step = self._step
        _rows = step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        if len(_rows) > 1:
            rows.extend(
                '%s%s%s%s' % (spaces, sep, '  ', row)
                for row in _rows[1:]
            )
            rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        if self._loop_step:
            rows.append('%s%s%s%s' % (spaces, sep, '_<< ', _rows[0]))
        else:
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step'''
        iterable = self._step.make(value, **kwargs)

        result, iterable = tee(iterable, 2)
        for val in result:
            yield val

        while True:
            iterable = reduce(
                lambda iterable, step: step.make_all(iterable, **kwargs),
                chain([iterable], [self._loop_step, self._step])
            )

            sentinel = object()
            value = next(iterable, sentinel)
            iterable = chain([value], iterable)
            if value is sentinel:
                return

            result, iterable = tee(iterable, 2)
            for val in result:
                yield val


class UnionStep(Step):
    def __init__(self, step):
        self._step = to_step(step)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self._step))

    def _raw_tree(self, **kwargs):
        if kwargs.get('full', False) or kwargs.get('show_union', False):
            rows = ['%s()' % self.__class__.__name__]

            center_pos = round(len(self.__class__.__name__) / 2)
            spaces = ' ' * (center_pos - 1)
            unders = '__'
            sep = '|'

            _rows = self._step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, ' ', spaces, row)
                    for row in _rows[1:]
                )

            return rows
        else:
            return self._step._raw_tree(**kwargs)

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        if kwargs.get('full', False) or kwargs.get('show_union', False):
            return '\n'.join(self._raw_tree(**kwargs))
        else:
            return self._step.tree(**kwargs)

    def make(self, value, **kwargs):
        '''Main method of Step'''
        return self._step.make(value, **kwargs)


class OrChain(Step):
    '''Step related from other steps by 'or_bind', it is implementing chain'''
    def __init__(self, steps):
        self._chain = list(map(to_step, steps))

    def __repr__(self):
        s = ' | '.join(map(repr, self._chain))
        return '%s(%s)' % (self.__class__.__name__, s)

    def or_bind(self, or_step):
        '''Make Or Step from current step and other step'''
        self._chain.append(to_step(or_step))
        return self
        
    def union(self):
        '''Combining current steps'''
        return UnionStep(self)

    def _raw_tree(self, **kwargs):
        start_row = '%s(%s)' % (self.__class__.__name__, len(self._chain))

        rows = [start_row]
        if not self._chain:
            return rows

        last_step = self._chain[-1]
        chain = self._chain[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step'''
        for step in self._chain:
            iterator = iter(step.make(value, **kwargs))
            sentinel = object()
            val = next(iterator, sentinel)
            if val is sentinel:
                continue
            # yield from chain([val], iterator)
            for val in chain([val], iterator):
                yield val
            return


class TupleStep(Step):
    def __init__(self, steps):
        self._steps = steps

        if not isinstance(steps, tuple):
            raise TypeError('Must be tuple of Steps')

        for step in steps:
            if not isinstance(step, Step):
                raise TypeError('Must be tuple of steps')

    def __repr__(self):
        return '%s((%s))' % (
            self.__class__.__name__,
            ', '.join(
                (repr(s) for s in self._steps)
            )
        )

    def _raw_tree(self, **kwargs):
        start_row = '%s(%s)' % (
            self.__class__.__name__,
            len(self._steps)
        )

        rows = [start_row]
        if not self._steps:
            return rows

        last_step = self._steps[-1]
        chain = self._steps[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(
            iter(step.make(value, **kwargs))
            for step in self._steps
        )
        return (tuple(it) for it in zip(*iterables))


class ListStep(Step):
    def __init__(self, steps):
        self._steps = steps

        if not isinstance(steps, list):
            raise TypeError('Must be list of steps')

        for step in steps:
            if not isinstance(step, Step):
                raise TypeError('Must be list of steps')

    def __repr__(self):
        return '%s([%s])' % (
            self.__class__.__name__,
            ', '.join(
                (repr(s) for s in self._steps)
            )
        )

    def _raw_tree(self, **kwargs):
        start_row = '%s(%s)' % (
            self.__class__.__name__,
            len(self._steps)
        )

        rows = [start_row]
        if not self._steps:
            return rows

        last_step = self._steps[-1]
        chain = self._steps[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(
            iter(step.make(value, **kwargs))
            for step in self._steps
        )

        sentinel = object()
        while True:
            result_list = [
                val
                for val in
                (next(it, sentinel) for it in iterables)
                if val is not sentinel
            ]
            if len(result_list) > 0:
                yield result_list
            else:
                return


class DictStep(Step):
    def __init__(self, steps):
        self._steps = steps

        if not isinstance(steps, dict):
            raise TypeError(
                'Must be dict of steps: {key1: step, ... key2: step}'
            )

        for step in steps.values():
            if not isinstance(step, Step):
                raise TypeError(
                    'Must be dict of steps: {key1: step, ... key2: step}'
                )

    def __repr__(self):
        return '%s({%s})' % (
            self.__class__.__name__,
            ', '.join(
                '%s: %s' % (repr(key), repr(s))
                for key, s in self._steps.items()
            )
        )

    def _raw_tree(self, **kwargs):
        start_row  = '%s(%s)' % (
            self.__class__.__name__,
            len(self._steps)
        )
        rows = [start_row]
        if not self._steps:
            return rows

        steps = tuple(self._steps.items())

        last_step = steps[-1]
        chain = steps[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for key, step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append(
                '%s%s%s%s: %s' % 
                (spaces,sep, unders, repr(key), _rows[0])
            )
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        key = last_step[0]
        _rows = last_step[1]._raw_tree(**kwargs)
        rows.append(
            '%s%s%s%s: %s' % 
            (spaces,sep, unders, repr(key), _rows[0])
        )
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(
            (
                key,
                iter(step.make(value, **kwargs))
            )
            for key, step in self._steps.items()
        )

        sentinel = object()
        while True:
            result_dict = {
                key: val
                for key, val in
                ((key, next(it, sentinel)) for key, it in iterables)
                if val is not sentinel
            }
            if len(result_dict) > 0:
                yield result_dict
            else:
                return


class SetStep(Step):
    def __init__(self, steps):
        self._steps = steps

        if not isinstance(steps, set):
            raise TypeError('Must be set of steps')

        for step in steps:
            if not isinstance(step, Step):
                raise TypeError('Must be set of steps')

    def __repr__(self):
        return '%s({%s})' % (
            self.__class__.__name__,
            ', '.join(
                (repr(s) for s in self._steps)
            )
        )

    def _raw_tree(self, **kwargs):
        steps = tuple(self._steps)
        start_row = '%s(%s)' % (
            self.__class__.__name__,
            len(steps)
        )

        rows = [start_row]
        if not steps:
            return rows

        last_step = steps[-1]
        chain = steps[:-1]

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        for step in chain:
            _rows = step._raw_tree(**kwargs)
            rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
            if len(_rows) > 1:
                rows.extend(
                    '%s%s%s%s' % (spaces, sep, '  ', row)
                    for row in _rows[1:]
                )
                rows.append('%s%s' % (spaces, sep))

        _rows = last_step._raw_tree(**kwargs)
        rows.append('%s%s%s%s' % (spaces, sep, unders, _rows[0]))
        rows.extend(
            '%s%s%s%s' % (spaces, ' ', spaces, row)
            for row in _rows[1:]
        )

        return rows

    def tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(
            iter(step.make(value, **kwargs))
            for step in self._steps
        )

        sentinel = object()
        while True:
            result_set = {
                val
                for val in
                (next(it, sentinel) for it in iterables)
                if val is not sentinel
            }
            if len(result_set) > 0:
                yield result_set
            else:
                return
