from monapy import Step
class Split(Step):
	def __init__(self, char):
		self._ch = char

	def make(self, val, **kw):
		return val.split(self._ch)

class Numbering(Step):
	def __init__(self, fmt):
		self._fmt = fmt
		self._num = 0

	def make(self, val, **kw):
		self._num += 1
		return [
			''.join([
				self._fmt % self._num,
				val
			])
		]

text = '''Python is an interpreted, high-level
and general-purpose programming language.
Python's design philosophy emphasizes
code readability with its notable use of
significant whitespace. Its language
constructs and object-oriented approach
aim to help programmers write clear,
logical code for small and large-scale
projects.
'''

chain = Split('\n') >> Numbering('%d. ')
print(*chain(text), sep='\n')

# Result:
# 1. Python is an interpreted, high-level
# 2. and general-purpose programming language.
# 3. Python's design philosophy emphasizes
# 4. code readability with its notable use of
# 5. significant whitespace. Its language
# 6. constructs and object-oriented approach
# 7. aim to help programmers write clear,
# 8. logical code for small and large-scale
# 9. projects.
# 10.