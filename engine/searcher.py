#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from itertools import repeat, chain

from engine.utils import nested_frozen_fs, unify_till_pass


class Searcher:
    def __init__(self, name, condition, max_words_in_direction, unique, direction, border, hit_function=None,
                 ballast=nested_frozen_fs({}), initiator=None, hit=None):
        if initiator is not None:
            init = initiator.index()
        else:
            init = None
        if condition is not None and 'main' in condition:
            cond = condition['main']
        else:
            cond = None
        print('searcher', name, cond, max_words_in_direction, direction, init, file=sys.stderr)
        self.name = name
        if isinstance(condition, dict):
            condition = nested_frozen_fs(condition)
        elif isinstance(condition, set):
            condition = frozenset(condition)
        self.condition = condition
        self.max_words_in_direction = max_words_in_direction
        self.unique = unique
        if direction is not None:
            direction = direction[:]  # Needed because Python
        self.direction = direction
        self.border = border
        self.hit_function_unbound = hit_function

        if isinstance(ballast, dict):
                ballast = nested_frozen_fs(ballast)
        self.ballast = ballast
        self.initiator = initiator
        self.hit = hit

    def hit_function(self):
        return self.hit_function_unbound(self)  # Call unbound method as it were bound

    def _unify_condition(self, other):
        if (self.condition is None) ^ (other.condition is None):
            if self.condition is not None:
                return self.condition
            else:
                return other.condition
        if self.condition == other.condition is None:
            return None

        if isinstance(self.condition, frozenset):
            condition = [i for i in sorted(chain(self.condition, other.condition))]
            unified = frozenset(unify_till_pass(condition))
            if len(unified) == len(condition):
                unified = None
        else:
            unified = self.condition.unify(other.condition)
            if unified is not None:
                unified.freeze()

        if unified is None:
            return 'NOT_UNIFIABLE'
        else:
            return unified

    def _unify_max_words_in_direction(self, other):
        if (self.max_words_in_direction is None) ^ (other.max_words_in_direction is None):
            if self.max_words_in_direction is not None:
                return self.max_words_in_direction
            else:
                return other.max_words_in_direction
        elif (self.max_words_in_direction is None) and (other.max_words_in_direction is None):
            return None
        else:
            return min(self.max_words_in_direction, other.max_words_in_direction)

    def _unify_direction(self, other):
        # Equality
        if self.direction == other.direction:
            return self.direction
        # Direction restrictor left Ex. PART
        elif (self.direction == ['<'] and other.direction == ['<', '>']) or\
             (self.direction == ['<', '>'] and other.direction == ['<']):
            return ['<']
        # Direction restrictor window Ex. ???
        elif (self.direction == ['>]'] and other.direction == ['>]', '>']) or \
             (self.direction == ['>]', '>'] and other.direction == ['>]']):
            return ['>]']
        # One of them is None -> The other
        elif (self.direction is None) ^ (other.direction is None):
            if self.direction is not None:
                return self.direction
            else:
                return other.direction
        else:
            raise KeyError  # SHOULD NOT END UP HERE!  # <, >, >]

    def _unify_border(self, other):
        if (self.border is None) ^ (other.border is None):
            if self.border is not None:
                return self.border
            else:
                return other.border
        elif (self.border == '||') ^ (other.border == '||'):
            if self.border == '||':
                return self.border
            else:
                return other.border
        return self.border  # Both | or both || or None -> ok

    def _unify_hit_function(self, other):
        if (self.hit_function_unbound is None) ^ (other.hit_function_unbound is None):
            if self.hit_function_unbound is not None:
                return self.hit_function_unbound
            else:
                return other.hit_function_unbound
        elif self.hit_function_unbound == other.hit_function_unbound:
            return self.hit_function_unbound
        else:
            return 'NOT_UNIFIABLE'

    def _unify_ballast(self, other):
        if (self.ballast is None) ^ (other.ballast is None):
            if self.ballast is not None:
                return self.ballast
            else:
                return other.ballast
        if self.ballast == other.ballast is None:
            return None
        # TODO: Investigate NLTK
        """
        from nltk.featstruct import FeatStruct
        e = FeatStruct(other.ballast)
        fs = hash(e['postponed-searchers'].pop())
        # e['postponed-searchers'] = frozenset()
        unified = self.ballast.unify(e)
        """
        unified = self.ballast.unify(other.ballast)
        if unified is None:
            return 'NOT_UNIFIABLE'
        else:
            unified.freeze()
            return unified

    def _unify_initiator(self, other):
        success, new = self.initiator.unify_tokens(other.initiator)
        if success:
            return new
        else:
            raise KeyError

    def _unify_hit(self, other):
        if self.hit == other.hit or\
                (self.hit is None and other.hit is not None) or\
                (self.hit is not None and other.hit is None):
            return self.hit
        else:
            raise KeyError

    def unify_searchers(self, other):
        if self.name == other.name:
            new_name = self.name
            new_condition = self._unify_condition(other)        # May not unify 'NOT_UNIFIABLE'
            new_max_words_in_direction = self._unify_max_words_in_direction(other)
            new_unique = self.unique or other.unique
            new_direction = self._unify_direction(other)        # May not unify 'NOT_UNIFIABLE'
            new_border = self._unify_border(other)
            new_hit_function = self._unify_hit_function(other)  # May not unify 'NOT_UNIFIABLE'
            new_ballast = self._unify_ballast(other)            # May not unify 'NOT_UNIFIABLE'
            new_initiator = self._unify_initiator(other)
            new_hit = self._unify_hit(other)
            if (new_direction != 'NOT_UNIFIABLE' and new_hit_function != 'NOT_UNIFIABLE' and
               new_condition != 'NOT_UNIFIABLE' and new_ballast != 'NOT_UNIFIABLE'):
                return True, Searcher(new_name, new_condition, new_max_words_in_direction, new_unique, new_direction,
                                      new_border, new_hit_function, new_ballast, new_initiator, new_hit)
        return False, None

    def search(self, current_tok, pool, is_rightmost=False) -> (bool, list):  # Reuse, list of searchers
        if self.direction is None:
            raise TypeError(current_tok, self)
        direction = self.direction.pop(0) if len(self.direction) > 0 else None
        till_index = None
        if self.max_words_in_direction is not None:  # Blocked will not find anything...

            if direction == '<':
                # Inlcude the max_words_in_direction index
                till_index = self.initiator.index() - self.max_words_in_direction
            else:
                till_index = self.initiator.index() + self.max_words_in_direction

        # This won't cause infinite loop because the token stepping mechanism one level above...
        if self.initiator == current_tok and direction != '<':  # e.g. direction is >] or >
            self.direction.insert(0, direction)
            return False, [self]  # Skip if on the initiator token and not checking pool...
        elif direction == '<':
            # Focus + any other... If Unique, then elem else [elem]...
            self.hit = pool.search_by_condition(self.initiator, self.condition, self.border, till_index, self.unique)

            reuse, ret = self.hit_function()  # Handle if something is (not) found...

            # Non uniq or not found and has direction to search
            if ret is None and len(self.direction) > 0 and (self.hit is None or not self.unique):
                return True, [self]

            return reuse, ret
        elif direction == '>]':  # In the window search...
            # Restrict to the farthest index
            if till_index is None or current_tok.index() <= till_index:
                if isinstance(self.condition, frozenset):  # Ex: Prev or Inf search
                    conds = self.condition
                else:
                    conds = repeat(self.condition, 1)
                for cond in conds:
                    if current_tok.unifies_w_token(cond) is not None:
                        self.hit = current_tok
                        break
            else:  # Reached till_index limit in this direction. Other directions wellcome!
                is_rightmost = True          # And is reached the rightmost for this searcher...

            # There is window to the right...still searching
            if (self.hit is None or not self.unique) and not is_rightmost:
                self.direction.insert(0, '>]')
                return False, [self]
            # Found or this is the end...
            elif (self.hit is not None and self.unique) or len(self.direction) == 0:
                reuse, ret = self.hit_function()  # Handle if something is (not) found...
                return reuse, ret
            else:  # Not found or not uniq, but there an other direction
                return True, [self]
        elif direction == '>':
            pool.put_searcher(self)  # Right search...
            return False, None  # Put into the pool no return searcher nothing to do...
        elif direction is None:
            print('Error: Runaway restrictor {0}!'.format(self.__repr__()), file=sys.stderr, flush=True)
            exit(1)
        else:
            raise KeyError

    def __lt__(self, other):  # Because everywhere unify_till_pass should be used before comparsion!
        return self.name < other.name

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        if not self.condition.frozen():
            self.condition.freeze()  # TODO: Why it became unfrozen? Possibly an NLTK bug triggered by ballast.unify()

        direct = self.direction
        if isinstance(self.direction, list):
            direct = tuple(self.direction)

        name = hash(self.name)
        cond = hash(self.condition)
        direct = hash(direct)
        init = hash(self.initiator)
        unique = hash(self.unique)

        return name ^ cond ^ direct ^ init ^ unique

    def __repr__(self):
        return 'Searcher({0})'.format(',\n'.join(['Name: {0}'.format(self.name),
                                                  'Condition: {0}'.format(self.condition),
                                                  'Direction: {0}'.format(self.direction),
                                                  'Initator: {0}'.format(self.initiator),
                                                  'Is Unique: {0}'.format(self.unique)]))
