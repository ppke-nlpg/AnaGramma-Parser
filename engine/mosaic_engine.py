#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import sys


# The source code of SetTrie and Node classes is borrowed from: https://github.com/dlazesz/pysettrie/


class Node:
    """Node object used by SetTrie."""

    def __init__(self, data=None, value=None):
        self.children = []  # child nodes a.k.a. children
        # if True, this is the last element of
        #  a) a set in the set-trie use this to store user data (a set element).
        #  b) a key set store a member element of the key set.
        self.flag_last = False
        # Must be a hashable (i.e. hash(data) should work) and comparable/orderable
        # (i.e. data1 < data2 should work; see https://wiki.python.org/moin/HowTo/Sorting/) type.
        self.data = data
        self.value = value  # the value/list of values associated to the key set if flag_last == True, otherwise None

    def __repr__(self):
        return 'Node[{0}, {1}, {2}]'.format(self.data, self.value, self.flag_last)

    # comparison operators to support rich comparisons, sorting etc. using self.data as key
    def __eq__(self, other):
        if self.value == other.value:  # RE vs. RE
            return self.data == other.data
        else:                          # RE vs. STR or STR vs. RE
            if self.flag_last != other.flag_last:
                return False
            #  Regex match
            if self.value == 'RE':
                regex = self.data
                patt = other.data
            else:
                regex = other.data
                patt = self.data
            for r, p in zip(regex, patt):
                if not r.fullmatch(p):
                    return False
            return True


class SetTrie:
    def __init__(self, iterable=None):
        """
         Initialize this set-trie. If iterable is specified, set-trie is populated from its items.
        """
        self.root = Node()
        if iterable is not None:
            for s in iterable:
                self.add(s)

    def contains(self, aset, allow_partial=False):
        """
        Returns True iff this set-trie contains element aset.
        """
        return self.r_contains(self.root, aset, 0, allow_partial)

    def __contains__(self, aset):
        """
           Returns True iff this set-trie contains the elements in aset.
           This method definition allows the use of the 'in' operator
        """
        return self.contains(aset)

    def r_contains(self, node, it, i, allow_partial=False):
        """
        Recursive function used by self.contains().
        """
        try:
            data = it[i]
            try:
                temp_node = Node(data, 'STR')
                temp_node.flag_last = len(it) <= i + 1
                matchnode = node.children[node.children.index(temp_node)]  # find first child with this data
                return self.r_contains(matchnode, it, i + 1, allow_partial)  # recurse
            except ValueError:  # not found
                return False
        except IndexError:  # Iterator empty: Full match -> True when flag_last true, Partial match -> always True
            return node.flag_last or allow_partial

    def iter(self, mode=None):
        """
           Returns an iterator over the elems stored in this set-trie (with pre-order tree traversal).
           The elems are returned in sorted order.
        """
        path = []
        yield from self._iter(self.root, path, mode)

    def __iter__(self):
        """
           Returns an iterator over the elements stored in this set-trie (with pre-order tree traversal).
           The elements are returned in sorted order with their elements sorted.
        """
        return self.keys()

    def _iter(self, node, path, mode=None):
        """
        Recursive function used by self.iter().
        """
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            yield from self.yield_last(path, node, mode)
        for child in node.children:
            yield from self._iter(child, path, mode)
        if node.data is not None:
            path.pop()

    def aslist(self):
        """
           Return a list containing all the elements stored.
           The elements are returned in sorted order.
        """
        return list(self.iter())

    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """
           Print a mirrored 90-degree rotation of the nodes in this trie to stream (default: sys.stdout).
           Nodes marked as flag_last are trailed by the '#' character.
           tabchr and tabsize determine the indentation: at tree level n, n*tabsize tabchar characters will be used.
        """
        self.r_printtree(self.root, 0, tabchr, tabsize, stream)

    def r_printtree(self, node, level, tabchr, tabsize, stream):
        """
        Used by self.printTree(), recursive preorder traverse and printing of trie node
        """
        print(str(node.data).rjust(len(repr(node.data))+level*tabsize, tabchr) + self.print_last(node), file=stream)
        for child in node.children:
            self.r_printtree(child, level+1, tabchr, tabsize, stream)

    def __str__(self):
        """
        Returns str(self.aslist()).
        """
        return str(self.aslist())

    def __repr__(self):
        """
        Returns str(self.aslist()).
        """
        return str(self.aslist())

    # Above this line all function is common to all set-trie types
    # ------------------------------------------------------------------------------------------------------------------
    # Below this line is the differences among the functionality
    def keys(self):
        return self.iter()

    @staticmethod
    def print_last(node):
        """
        Last element is denoted by a '#' character.
        """
        return '#' if node.flag_last else ''

    @staticmethod
    def yield_last(path, node, mode):
        _ = node  # Dummy command to silence the IDE
        _ = mode  # Dummy command to silence the IDE
        return [path]

    def add(self, aset):
        """
           Add set aset to the container.
           aset must be a sortable and iterable container type.
        """
        self._add(self.root, iter(aset))

    def _add(self, node, it):
        """
           Recursive function used by self.insert().
           node is a SetTrieNode object
           it is an iterator over a sorted set
        """
        try:
            data = next(it)
            try:
                nextnode = node.children[node.children.index(Node(data, value='RE'))]  # find first child with this data
            except ValueError:  # not found
                nextnode = Node(data, value='RE')  # create new node
                node.children.append(nextnode)  # add to children & sort
            self._add(nextnode, it)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True


class Mosaic:
    def __init__(self, mosaic_list):
        compiled_mosaic_list = self._compile_mosaics(mosaic_list)
        self._trie = SetTrie(compiled_mosaic_list)

    @staticmethod
    def _compile_mosaics(mosaic_list):
        return [[[re.compile(field) for field in token] for token in mosaic] for mosaic in mosaic_list]

    @staticmethod
    def _preprocess_raw_text(tokens):
        return [token.split('#') for token in tokens]

    @staticmethod
    def _postprocess_raw_text(token_list):
        return ['#'.join(token) for token in token_list]

    def merge_mosaic_tokens(self, text):
        preprocessed = self._preprocess_raw_text(text)
        if not self._trie.contains(preprocessed, allow_partial=True):
            return self._postprocess_raw_text(self._r_merge_mosaic_tokens(preprocessed)), False
        return text, True  # When partial match at the end wait for an extra token!

    def _r_merge_mosaic_tokens(self, token_list):
        # If no token left for merge, done...
        if len(token_list) < 2:
            return token_list
        # Try finding patterns from the start to the end, end -1, end -2, etc...
        for i in range(len(token_list), 1, -1):
            if token_list[:i] in self._trie:
                break
        else:
            i = 1  # Strip first token and
        # Merge from start to i and continue with the rest...
        return self._merge_part(token_list[:i]) + self._r_merge_mosaic_tokens(token_list[i:])

    @staticmethod
    def _merge_part(partial_list):
        tokens, lemmas, tags = zip(*partial_list)
        return [('_'.join(tokens), '_'.join(lemmas), tags[-1])]
