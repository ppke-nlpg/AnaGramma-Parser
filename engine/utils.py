#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from itertools import chain
from nltk.featstruct import FeatStruct, CustomFeatureValue, UnificationFailure

from typing import Any


def update_nested_frozen_fs(fs, dictinoary):
    fs = {k: v for k, v in fs.items() if k not in dictinoary.keys()}
    fs.update(dictinoary)
    return nested_frozen_fs(fs)


def nested_frozen_fs(dictionary):
    if not isinstance(dictionary, FeatStruct):
        ret = FeatStruct()
        for k, v in dictionary.items():
            v_new = v
            if isinstance(v_new, set):
                v_new = frozenset(v_new)
            elif isinstance(v_new, dict):
                v_new = nested_frozen_fs(v_new)
            ret[k] = v_new
        ret.freeze()
        return ret
    else:
        dictionary.freeze()
    return dictionary


class UnifiableSet(CustomFeatureValue):
    """
    Simple Set union on unify() the internal unification is handled elsewhere. TODO: Maybe do it here?
    """
    def __init__(self, data):
        self.data = frozenset([data])
        self._frozen = True
        super().__init__()

    def unify(self, other):
        if not isinstance(other, self.__class__):
            return UnificationFailure

        data = [i for i in sorted(chain(self.data, other.data))]
        self.data = frozenset(unify_till_pass(data))  # Union
        return self

    def pop(self):
        return set(self.data).pop()

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.data == other.data

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return True
        return self.data < other.data  # isSubset

    def __hash__(self):
        return hash(self.data)

    def __iter__(self):
        return iter(self.data)

    def frozen(self):
        return self._frozen


def flatten(it: [[Any]]) -> [Any]:
    return list(chain.from_iterable(it))


def unify_till_pass(actions):
    actions.sort()
    passed_actions = []
    while len(actions) > 1:  # There is something to unify...
        first = actions.pop(0)
        to_pop = None
        new = None
        for second in actions:  # Unify with all the remaining...
            success, new = first.unify_searchers(second)
            if success:
                to_pop = second  # When succeded, remember to remove from the list of actions
                break
        else:
            passed_actions.append(first)  # One round "Pass" completed for this element...
        if to_pop is not None:  # Unification success...
            actions.remove(to_pop)  # Remove the one which has been unified
            actions.append(new)     # Add the newly created one
            # actions.extend(passed_actions)  # todo: Reuse "passed" actions until every action is "passed"...
            # passed_actions = []
    if len(actions) == 1:
        passed_actions.append(actions.pop())
    actions = passed_actions
    return actions
