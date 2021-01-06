# -*- coding: utf-8 -*-

import sys

import pytest

sys.path.insert(0, '..')

from monapy import Binder
from monapy import Step


class Iters(Step):
	def __init__(self, iterable, repeat=1):
		self._iterable = iterable
		self._repeat = repeat

	def make(self, value):
		for _ in range(self._repeat):
			yield from self._iterable


class ReturnEquals(Step):
	def __init__(self, values=[]):
		self._values = values

	def make(self, value):
		if value in self._values:
			yield value


class Repeat(Step):
	def __init__(self, value, repeats=1):
		self._val = value
		self._rep = repeats

	def make(self, value):
		for _ in range(self._rep):
			yield self._val


class RepeatOnce(Step):
	def __init__(self, value, repeats=1):
		self._val = value
		self._rep = repeats
		self._ret = True

	def make(self, value):
		if not self._ret:
			return
		for _ in range(self._rep):
			yield self._val
		self._ret = False


def test_binder():
	b = Binder() >> range << 1 >> map << (lambda i: i * 10) >> list

	assert b(5) == [10, 20, 30, 40]


def test_step():
	step = Repeat('t', 2)

	result = tuple(step.make(0))

	assert result == ('t',) * 2


def test_step_chain():
	step = Repeat('f', 2) >> Repeat('l', 3)

	result = tuple(step.make(0))

	assert result == ('l',) * 6


def test_loop_step():
	step = Repeat('1', 2) >> Repeat('2') << RepeatOnce('3') << RepeatOnce('4', 2)

	result = tuple(step.make(0))

	assert result == ('2',) * 5


def test_union_step():
	step = ~(Repeat('1', 2) >> Repeat('2')) << RepeatOnce('3')
	step1 = ~(Repeat('1', 2) >> Repeat('2')) << RepeatOnce('3') >> Repeat('4')

	result = tuple(step.make(0))
	result1 = tuple(step1.make(0))

	assert result == ('2',) * 4
	assert result1 == ('4',) * 4


def test_or_chain():
	step = Iters('abcdefghjk') >> (ReturnEquals('afzk') | ReturnEquals('bateh') | ReturnEquals('cbdjx'))

	result = tuple(step.make(0))

	assert result == tuple('abcdefhjk')


def test_tuple_step():
	step = Iters('abcdefghjk') >> (ReturnEquals('abc'), ReturnEquals('ab'), ReturnEquals('a'))

	result = tuple(step.make(0))

	assert result == (('a',)*3,)


def test_list_step():
	step = Iters('abcdefghjk') >> [ReturnEquals('abc'), ReturnEquals('ab'), ReturnEquals('a')]

	result = tuple(step.make(0))

	assert result == (['a']*3, ['b']*2, ['c'])


def test_dict_step():
	step = Iters('abcdefghjk') >> {
		'one': ReturnEquals('abc'),
		'two' :ReturnEquals('ab'),
		'three': ReturnEquals('a')
	}

	result = tuple(step.make(0))

	assert result == (
		{'one': 'a', 'two': 'a', 'three': 'a'},
		{'one': 'b', 'two': 'b'},
		{'one': 'c'},
	)


def test_set_step():
	step = Iters('abcdefghjk') >> {ReturnEquals('abc'), ReturnEquals('ab'), ReturnEquals('a')}

	result = tuple(step.make(0))

	assert result == ({'a'}, {'b'}, {'c'})
