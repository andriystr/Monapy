Monapy
===

Python Library for build declarative tools.
---

### Binder - simple monad implementation.
Binder is binding functions to chain.
The result of the previous function is passed to next function as positional argument.
Right arrows bind functions into chain.
Left arrows set positional argument for last function in chain.
##### Examples:
```python
>>> from monapy import Binder
>>> binder = Binder() >> range >> map << ( lambda i: i * 10 )
>>> list( binder( 10 ) )
[0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
>>> binder >> filter << ( lambda i: not i % 20 ) >> list
>>> binder( 10 )
[0, 20, 40, 60, 80]
```

### Package Step
Step is a functional unit, a step is binding with other step for making chain steps.
Class Step must be implemented, method 'make' is main that take value and generate iterator.
First step take value and generating iterator,
that iteratively by one values is passed other step,
this process continue while to last step in the chain.
Bindings define which step the value is passed to.
Steps may be bind by next bindings: bind, loop, or_bind.

#### Bind
The values (in iterator) is passed to next step.
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() >> Step()
>>> chain2 = Step().bind( Step() )
>>> chain3 = StepChain( [ Step(), Step() ] )
>>> chain4 = Step() >> Step() >> Step()
```

#### Loop
This bind make loop, first steps values (in iterator) is passed to second step and out of this chain,
second step by each value generate values (iterator),
and this values is passed to first step, then all repeat until empty iterator from second step.
```
(iter) --> value ------> First Step --> (iter) --> value ------>
                    ^                                       |
                    |                                       |
                     -- value <-- (iter) <-- Second Step <--
```
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() << Step()
>>> chain2 = Step().loop( Step() )
>>> chain3 = LoopStep( Step(), Step() )
```

#### Or-Bind
It like 'or' logical expression, first non empty iterator is passed to out of this chain.
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() | Step()
>>> chain2 = Step().or_bind( Step() )
>>> chain3 = OrChain( [ Step(), Step() ] )
>>> chain4 = Step() | Step() | Step()
```

#### Internal structure of chain
For view how steps binded call 'tree' method and print result.
##### Examples:
```python
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
```
##### Detailed tree
```python
>>> print( chain.tree( full=True ) )
StepChain(3)
   |__Step()
   |__LoopStep()
   |     |__UnionStep()
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
```

#### Combining steps
Sometimes need make separate chain, for this exists '~' expresion.
##### Examples:
```python
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
```

#### Show UnionStep in tree
```python
>>> print( chain1.tree( show_union=True ) )
LoopStep()
   |__UnionStep()
   |     |__StepChain(3)
   |            |__Step()
   |            |__Step()
   |            |__Step()
   |
   |_<< Step()
```

#### Run chin
For run chain call 'make' method, that return iterator.
##### Examples:
```python
>>> from monapy import Step
>>> chain = Step() >> Step() << Step() >> ( Step() | Step() | Step() )
>>> for val in chain.make( value ):
>>>     print( val )

>>> for val in chain( value ):
>>>     print( val )
```

#### Packing values in standard data structures
4 structures supported: tuple, list, dict, set.
Values pack the corresponding steps,
for create this step need bind chain with corresponding structure of steps,
or call corresponding class.
From each step, one value is taken and pack into structure.
##### Pack in tuple
> It's like 'zip' function,
> if every step returns a value then those values ​​are packed into a tuple,
> otherwise no packing happens and values ​​aren't returned.
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() >> ( Step(), Step(), Step() )
>>> chain2 = TupleStep( ( Step(), Step(), Step() ) )
>>> chain3 = to_step( ( Step(), Step(), Step() ) )
```
##### Pack in list
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() >> [ Step(), Step(), Step() ]
>>> chain2 = ListStep( [ Step(), Step(), Step() ] )
>>> chain3 = to_step( [ Step(), Step(), Step() ] )
```
##### Pack in dict
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() >> { 'key1': Step(), 'key2': Step(), 'key3': Step() }
>>> chain2 = DictStep( { 'key1': Step(), 'key2': Step(), 'key3': Step() } )
>>> chain3 = to_step( { 'key1': Step(), 'key2': Step(), 'key3': Step() } )
```
##### Pack in set
##### Examples:
```python
>>> from monapy import Step
>>> chain1 = Step() >> { Step(), Step(), Step() }
>>> chain2 = SetStep( { Step(), Step(), Step() } )
>>> chain3 = to_step( { Step(), Step(), Step() } )
```

#### Step class implementation
Class Step has two methods to implement,
it's 'make' and 'make_all'.
The 'make' method takes a value and generates an iterator,
that is passed to the next step.
This method takes one positional argument to get the value,
and also accepts named arguments,
that are used to pass settings for all steps in the chain.
Method 'make_all' is taking iterator of values that it passes to the 'make' method,
it could be used for paralleling.