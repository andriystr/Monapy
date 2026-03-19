# -*- coding: utf-8 -*-

'''
### Package Step
Step is a functional unit, a step is binding with other step for making chain steps.
Class Step must be implemented, method 'make' is main that take value and generate iterator.
First step take value and generating iterator,
that iteratively by one values is passed other step,
this process continue while to the last step in the chain.
Bindings define which step the value is passed to.
Steps may be bind by next binding methods: bind, loop_bind, or_bind.

#### Bind
The values (in iterator) is passed to the next step.
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() >> Step()
    >>> chain2 = Step().bind( Step() )
    >>> chain3 = StepChain( [ Step(), Step() ] )
    >>> chain4 = Step() >> Step() >> Step()

#### Loop
This bind make loop, first step's values (in iterator) is passed to second step and out of this chain,
second step by each value is generating values (iterator),
and this values is passed to first step, then all repeat until empty iterator from second step.

(iter) --> value ------> First Step --> (iter) --> value ------>
                    ^                                       |
                    |                                       |
                     -- value <-- (iter) <-- Second Step <--

##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() << Step()
    >>> chain2 = Step().loop( Step() )
    >>> chain3 = LoopStep( Step(), Step() )

#### Or-Bind
It like 'or' logical expression, a first non-empty iterator is passed to out of this chain.
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() | Step()
    >>> chain2 = Step().or_bind( Step() )
    >>> chain3 = OrChain( [ Step(), Step() ] )
    >>> chain4 = Step() | Step() | Step()

#### Internal structure of chain
To view, how steps binded, call 'tree' method and print result.
##### Examples:
    >>> chain = Step() >> ~( Step() >> Step() >> Step() ) << Step() >> ( Step() | Step() | Step() )
    >>> print( chain.tree() )
    StepChain(3)
       |__Step()
       |__LoopStep()
       |     |__StepChain(3)
       |     |     |__Step()
       |     |     |__Step()
       |     |     |__Step()
       |     |
       |     |_<< Step()
       |
       |__OrChain(3)
              |__Step()
              |__Step()
              |__Step()

##### Detailed tree
    >>> print( chain.tree( full=True ) )
    StepChain(3)
       |__Step()
       |__LoopStep()
       |     |__UnitedSteps()
       |     |     |__StepChain(3)
       |     |            |__Step()
       |     |            |__Step()
       |     |            |__Step()
       |     |
       |     |_<< Step()
       |
       |__OrChain(3)
              |__Step()
              |__Step()
              |__Step()

#### Combining steps
Sometimes need to make a separate sub-chain, for this exists '~' expression.
##### Examples:
    >>> from monapy import Step
    >>> chain1 = ~( Step() >> Step() >> Step() ) << Step()
    >>> print( chain1.tree() )
    LoopStep()
       |__StepChain(3)
       |     |__Step()
       |     |__Step()
       |     |__Step()
       |
       |_<< Step()

    >>> chain2 = Step() >> Step() >> Step() << Step()
    >>> print( chain2.tree() )
    StepChain(3)
       |__Step()
       |__Step()
       |__LoopStep()
              |__Step()
              |_<< Step()

#### Show UnitedSteps in tree
    >>> print( chain1.tree( show_united=True ) )
    LoopStep()
       |__UnitedSteps()
       |     |__StepChain(3)
       |            |__Step()
       |            |__Step()
       |            |__Step()
       |
       |_<< Step()

#### Run chain
For run chain call 'make' method, that return iterator.
##### Examples:
    >>> from monapy import Step
    >>> chain = Step() >> Step() << Step() >> ( Step() | Step() | Step() )
    >>> for val in chain.make( value ):
    >>>     print( val )

    >>> for val in chain( value ):
    >>>     print( val )

#### Packing values in standard data structures
4 structures supported: tuple, list, dict, set.
Values pack the corresponding steps,
to create this step need bind the chain with corresponding structure of steps,
or call a corresponding class.
From each step, one value is taken and pack into structure.
##### Pack in tuple
> It's like 'zip' function,
> if every step returns a value then those values ​​are packed into a tuple,
> otherwise no packing happens and values ​​aren't returned.
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() >> ( Step(), Step(), Step() )
    >>> chain2 = TupleStep( ( Step(), Step(), Step() ) )
    >>> chain3 = to_step( ( Step(), Step(), Step() ) )

##### Pack in list
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() >> [ Step(), Step(), Step() ]
    >>> chain2 = ListStep( [ Step(), Step(), Step() ] )
    >>> chain3 = to_step( [ Step(), Step(), Step() ] )

##### Pack in dict
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() >> { 'key1': Step(), 'key2': Step(), 'key3': Step() }
    >>> chain2 = DictStep( { 'key1': Step(), 'key2': Step(), 'key3': Step() } )
    >>> chain3 = to_step( { 'key1': Step(), 'key2': Step(), 'key3': Step() } )

##### Pack in set
##### Examples:
    >>> from monapy import Step
    >>> chain1 = Step() >> { Step(), Step(), Step() }
    >>> chain2 = SetStep( { Step(), Step(), Step() } )
    >>> chain3 = to_step( { Step(), Step(), Step() } )

#### Step class implementation
Class Step has two methods to implement,
it's 'make' and 'make_all'.
The 'make' method takes a value and generates an iterator,
that is passed to the next step.
This method takes one positional argument to get the value,
and also accepts named arguments,
that are used to pass settings for all steps in the chain.
The method 'make_all' is taking an iterator of values that it passes to the 'make' method,
it could be used for paralleling.
'''

import logging

from itertools import chain
from functools import reduce
from itertools import tee


logger = logging.getLogger(__name__)


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
        raise TypeError(f'to_step({type(step)}), supports only tuple, list, dict and set.')


class Step:
    '''Abstract class must be implement'''
    def __repr__(self):
        return f'{self.__class__.__name__}()'

    def __rshift__(self, next_step):
        return self.bind(next_step)

    def __lshift__(self, step):
        return self.loop_bind(step)

    def __invert__(self):
        return self.unite_steps()

    def __or__(self, or_step):
        return self.or_bind(or_step)

    def __call__(self, value = object(), **kwargs):
        return self.make(value, **kwargs)

    def bind(self, next_step):
        '''Bind current step with other step'''
        return StepChain([self, next_step])

    def loop_bind(self, step):
        '''Make Loop Step from current step and other step'''
        return LoopStep(self, step)

    def unite_steps(self):
        '''Combining current steps'''
        return self

    def or_bind(self, or_step):
        '''Make Or Step from current step and other step'''
        return OrChain([self, or_step])

    def _raw_tree(self, **kwargs):
        return [f'{self.__class__.__name__}()']

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make_all(self, iterable, **kwargs):
        '''Method must be implement'''
        return (value
                for val in iterable
                for value in self.make(val, **kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step, must be implement'''
        logger.warning(f'Calling {self.__class__.__name__}.make')
        return iter([])


class StepChain(Step):
    '''Step related from other steps by 'bind', it is implementing chain'''
    def __init__(self, steps):
        if not steps:
            raise ValueError('steps is empty')
        self._chain = list(map(to_step, steps))

    def __repr__(self):
        chain_repr = ' >> '.join(map(repr, self._chain))
        return f'{self.__class__.__name__}({chain_repr})'

    def bind(self, next_step):
        '''Bind current step with other step'''
        self._chain.append(to_step(next_step))
        return self

    def loop_bind(self, step):
        '''Make Loop Step from current step and other step'''
        last_step = self._chain.pop()
        new_step = LoopStep(last_step, step)
        self._chain.append(new_step)
        return self
        
    def unite_steps(self):
        '''Combining current steps'''
        return UnitedSteps(self)

    def _raw_tree(self, **kwargs):
        start_row = f'{self.__class__.__name__}({len(self._chain)})'

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
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step'''
        if not self._chain:
            return

        yield from reduce(lambda iterable, step: step.make_all(iterable, **kwargs),
                          chain([[value]], self._chain))


class LoopStep(Step):
    '''Step related from other steps by 'loop', it is implementing chain'''
    def __init__(self, step, loop_step):
        self._step = to_step(step)
        self._loop_step = to_step(loop_step)

    def __repr__(self):
        chain_repr = f'{self._step} << {self._loop_step}'
        return f'{self.__class__.__name__}({chain_repr})'

    def bind(self, next_step):
        '''Bind current step with other step'''
        return StepChain([self, next_step])
        
    def unite_steps(self):
        '''Combining current steps'''
        return UnitedSteps(self)

    def _raw_tree(self, **kwargs):
        start_row = f'{self.__class__.__name__}()'

        rows = [start_row]

        last_step = self._loop_step

        center_pos = round(len(self.__class__.__name__) / 2)
        spaces = ' ' * (center_pos - 1)
        unders = '__'
        sep = '|'

        step = self._step
        _rows = step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        if len(_rows) > 1:
            rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
            rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        if self._loop_step:
            rows.append(f'{spaces}{sep}_<< {_rows[0]}')
        else:
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value = object(), **kwargs):
        '''Main method of Step'''
        iterable = self._step.make(value, **kwargs)

        result, iterable = tee(iterable, 2)
        for val in result:
            yield val

        while True:
            iterable = reduce(lambda iterable, step: step.make_all(iterable, **kwargs),
                              chain([iterable], [self._loop_step, self._step]))

            sentinel = object()
            value = next(iterable, sentinel)
            iterable = chain([value], iterable)
            if value is sentinel:
                return

            result, iterable = tee(iterable, 2)
            yield from result


class UnitedSteps(Step):
    def __init__(self, step):
        self._step = to_step(step)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self._step)})'

    def _raw_tree(self, **kwargs):
        if kwargs.get('full', False) or kwargs.get('show_united', False):
            rows = [f'{self.__class__.__name__}()']

            center_pos = round(len(self.__class__.__name__) / 2)
            spaces = ' ' * (center_pos - 1)
            unders = '__'
            sep = '|'

            _rows = self._step._raw_tree(**kwargs)
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

            return rows
        else:
            return self._step._raw_tree(**kwargs)

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        if kwargs.get('full', False) or kwargs.get('show_united', False):
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
        chain_repr = ' | '.join(map(repr, self._chain))
        return f'{self.__class__.__name__}({chain_repr})'

    def or_bind(self, or_step):
        '''Make Or Step from current step and other step'''
        self._chain.append(to_step(or_step))
        return self
        
    def unite_steps(self):
        '''Combining current steps'''
        return UnitedSteps(self)

    def _raw_tree(self, **kwargs):
        start_row = f'{self.__class__.__name__}({len(self._chain)})'

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
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
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
            yield from chain([val], iterator)
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
        items_repr = ', '.join((repr(step) for step in self._steps))
        return f'{self.__class__.__name__}(({items_repr}))'

    def _raw_tree(self, **kwargs):
        start_row = f'{self.__class__.__name__}({len(self._steps)})'

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
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(iter(step.make(value, **kwargs))
                          for step in self._steps)
        
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
        items_repr = ', '.join((repr(s) for s in self._steps))
        return f'{self.__class__.__name__}([{items_repr}])'

    def _raw_tree(self, **kwargs):
        start_row = f'{self.__class__.__name__}({len(self._steps)})'

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
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(iter(step.make(value, **kwargs))
                          for step in self._steps)

        sentinel = object()
        while True:
            result_list = [val
                           for val in (next(it, sentinel) for it in iterables)
                           if val is not sentinel]
            
            if len(result_list) > 0:
                yield result_list
            else:
                return


class DictStep(Step):
    def __init__(self, steps):
        self._steps = steps

        if not isinstance(steps, dict):
            raise TypeError('Must be dict of steps: {key1: step, ... key2: step}')

        for step in steps.values():
            if not isinstance(step, Step):
                raise TypeError('Must be dict of steps: {key1: step, ... key2: step}')

    def __repr__(self):
        items_repr = ', '.join(f'{repr(key)}: {repr(s)}' for key, s in self._steps.items())
        return f'{self.__class__.__name__}({{{items_repr}}})'

    def _raw_tree(self, **kwargs):
        start_row  = f'{self.__class__.__name__}({len(self._steps)})'
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
            rows.append(f'{spaces}{sep}{unders}{repr(key)}: {_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        key = last_step[0]
        _rows = last_step[1]._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{repr(key)}: {_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple([key, iter(step.make(value, **kwargs))]
                          for key, step in self._steps.items())

        sentinel = object()
        while True:
            result_dict = {key: val
                           for key, val in ([key, next(it, sentinel)] for key, it in iterables)
                           if val is not sentinel}
            
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
        items_repr = ', '.join((repr(step) for step in self._steps))
        return f'{self.__class__.__name__}({{{items_repr}}})'

    def _raw_tree(self, **kwargs):
        steps = tuple(self._steps)
        start_row = f'{self.__class__.__name__}({len(steps)})'

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
            rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
            if len(_rows) > 1:
                rows.extend(f'{spaces}{sep}  {row}' for row in _rows[1:])
                rows.append(f'{spaces}{sep}')

        _rows = last_step._raw_tree(**kwargs)
        rows.append(f'{spaces}{sep}{unders}{_rows[0]}')
        rows.extend(f'{spaces} {spaces}{row}' for row in _rows[1:])

        return rows

    def get_str_tree(self, **kwargs):
        '''Internal structure of chain'''
        return '\n'.join(self._raw_tree(**kwargs))

    def make(self, value, **kwargs):
        '''Main method of Step'''
        iterables = tuple(iter(step.make(value, **kwargs))
                          for step in self._steps)

        sentinel = object()
        while True:
            result_set = {val
                          for val in (next(it, sentinel) for it in iterables)
                          if val is not sentinel}
            
            if len(result_set) > 0:
                yield result_set
            else:
                return

