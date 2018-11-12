#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from itertools import count

from nltk.featstruct import FeatStruct

from engine.utils import nested_frozen_fs


class Token:
    tok_num = count().__next__

    def __init__(self, token, attrs, n=None, purepos_anal=''):
        if n is None:
            n = Token.tok_num()
        self.n = n
        self.tok = token
        self.purepos_anal = purepos_anal
        self.attrs = {'anal': token, 'stem': token, 'anal_parts': []}
        if len(attrs) > 0:
            self.attrs.update(attrs)
        if len(self.attrs['anal_parts']) > 0:
            self.main, *self.other = self.attrs['anal_parts']  # Firts main from the second... other...
            self.other = set(self.other)
            self.stem = self.attrs['stem']

    def _make_repr(self):  # XXX Itt valami FeatStruct féle kiírás kellene...
        ret = nested_frozen_fs({'tok': self.tok, 'stem': self.stem, 'anal': self.attrs['anal'], 'main': self.main,
                               'other': self.other})
        # attrs = {k: v for k, v in self.attrs.items() if k not in {'anal', 'stem', 'anal_parts'}}
        # attrs['tok'] = self.tok
        # str('{{{0}}}'.format(', '.join("'{0}': '{1}'".format(k, v) for k, v in sorted(attrs.items()))))
        return ret

    def __str__(self):
        return str(self._make_repr())

    def __repr__(self):
        return str(self.tok)

    def __hash__(self):
        return hash(self._make_repr())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    # todo: REMÉLEM EZ JÓ ÍGY...
    def inherit_attrs(self, other):
        other.attrs.update({key: value for key, value in self.attrs.items() if key not in {'anal', 'stem'}})

    def index(self):
        return self.n

    def WLT_from(self):
        return self.tok, self.purepos_anal, self.attrs['anal']

    def _main_unifiable(self, other):
        # None If
        # 1) main not equals other['main'] (which is not joker or a set)
        # 2) other['main'] is a set and main is not an element of it.
        if 'main' in other:  # Have main...
            if isinstance(other['main'], frozenset):
                return self.main in other['main']  # Set conainment if is set...
            elif other['main'] != '*' and isinstance(other['main'], str):
                return self.main == other['main']  # Stringwise equality check...
            elif other['main'] == '*':
                return True  # main is joker
            else:
                print('Error: Unify ({0}) with empty FeatStruct not possible!'.format(str(self)), file=sys.stderr,
                      flush=True)
                exit(1)
        else:
            print('Error: Unify ({0}) with empty FeatStruct not possible!'.format(str(self)), file=sys.stderr,
                  flush=True)
            exit(1)

    def _subcond_unifiable_rigorous(self, other):
        # Rigorous checking (Missing attribute is NOT ok.)
        if 'subcond' in other:
            for subcond, val in other['subcond'].items():
                if subcond in self.attrs:
                    if isinstance(val, frozenset):
                        if self.attrs[subcond] not in val:
                            return False  # One elem NOT IN set
                    elif val != self.attrs[subcond]:
                        return False  # One Value not equal
                else:
                    return False  # No such subcond key in Token
            return True
        else:
            return True

    def _subcond_unifiable_unification(self, other):
        # Unification style checking... (Missing attribute is ok.)
        if 'subcond' in other:
            for subcond, val in other['subcond'].items():
                if subcond in self.attrs:
                    if isinstance(val, frozenset):
                        if self.attrs[subcond] not in val:
                            return False  # One elem NOT IN set
                    elif val != self.attrs[subcond]:
                        return False  # One Value not equal
                else:
                    return True  # No such subcond key in Token
            return True
        else:
            return True

    def _stem_unifiable(self, other):
        if 'stem' in other:
            if isinstance(other['stem'], frozenset):
                return self.stem in other['stem']  # One elem IN set
            else:
                return other['stem'] == self.stem  # One Value equal
        return True  # No stem, OK.

    def _other_unifiable(self, other):
        # Token has every 'other' feature or there is no other at all -> True!
        if 'other' in other:
            return self.other.issuperset(other['other'])
        return True  # No other, OK.

    def unifies_w_token(self, other):
        if not isinstance(other, FeatStruct):
            raise TypeError
        if other == FeatStruct():
            print('Error: Unify ({0}) with empty FeatStruct not possible!'.format(str(self)), file=sys.stderr,
                  flush=True)
            exit(1)
        if self._main_unifiable(other):
            if other['main'] == '*':
                ret_main = self._subcond_unifiable_rigorous(other)
            else:
                ret_main = self._subcond_unifiable_unification(other)
        else:
            ret_main = False

        ret_stem = self._stem_unifiable(other)
        ret_other = self._other_unifiable(other)
        if ret_main and ret_stem and ret_other:
            return True
        else:
            return None

    def unify_tokens(self, other):
        if not isinstance(other, self.__class__) or self.n != other.n or self.tok != other.tok or\
                self.purepos_anal != other.purepos_anal or self.main != other.main or self.stem != other.stem:
            return False, None

        if self.other != other.other:
            self.other = self.other | other.other

        if self.attrs != other.attrs:
            self.attrs.update(other.attrs)

        return True, self
