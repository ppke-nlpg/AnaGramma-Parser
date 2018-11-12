#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

morphology = {'Az': [0], 'alma,': [1, 2], 'de': [3], 'a': [4], 'körte': [5], 'nem.': [6, 7]}


class morphology_generator:
    """
    Using the generator pattern (an iterable)
    """
    def __init__(self, iterable, morph):
        self.morphology = morph
        self.iterable = iterable
        self._token = []

    def __iter__(self):
        return self

    # Python 3 compatibility
    def __next__(self):
        if len(self._token) == 0:
            nexti = next(self.iterable)
            self._token = self.morphology[nexti]
        return self._token.pop(0)

    # def next(self):
    #     if len(self._token) == 0:
    #         try:
    #             nexti = next(self.iterable)
    #             self._token = self.morphology[nexti]
    #         except StopIteration:
    #             return
    #     yield self._token.pop(0)


def morphology_generator2(iterable, morph):
    token = []
    i = iter(iterable)
    while True:
        if len(token) == 0:
            nexti = next(i)
            token = morph[nexti]
        yield token.pop(0)

"""
import collections
test = range(10)
print("range")
print(isinstance(test, collections.Iterable))
print(isinstance(test, collections.Iterator))
test = list(range(10))
print("list(range)")
print(isinstance(test, collections.Iterable))
print(isinstance(test, collections.Iterator))
test = iter('alma')
print("iter(str)")
print(isinstance(test, collections.Iterable))
print(isinstance(test, collections.Iterator))
test = iter(range(10))
print("iter(range)")
print(isinstance(test, collections.Iterable))
print(isinstance(test, collections.Iterator))
test = "alma"
print("str")
print(isinstance(test, collections.Iterable))
print(isinstance(test, collections.Iterator))

test = (i for i in [1,2,3,4])
print(test)
if isinstance(test, collections.Iterator) or isinstance(test, range):
    # iterator
    print('iterator')
elif isinstance(test, collections.Iterable):
    # iterable
    print('iterable')
else:
    print('not iterable')
    # not iterable
"""

# for i in morphology_generator2('Az alma, de a körte nem.'.split(), morphology):
#    print(i)

# >>> g = _morphology_generator('Az alma, de a körte nem.'.split(), morphology)

from types import MethodType
class valami:
    def __init__(self, alma):
        self.alma = MethodType(alma, self)
        self.korte = "aa"


def alma_fun(self):
    print("alma"+self.korte)

a = valami(alma_fun)
a.alma()
