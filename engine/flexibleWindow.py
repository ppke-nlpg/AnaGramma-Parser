#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from collections import deque
from itertools import islice


class FlexibleWindow:
    def __init__(self, input_text, n, padstr=lambda: '#'):
        self.paddtogo = 0  # Count remaining padding
        self.input_text = self._add_padding(input_text, 1, n, padstr)  # Make padding: 1 before, n after
        self.n = n  # default size
        self.deques = [deque() for _ in range(n)]  # deques storage
        # Makes n independent iterator from one and the the initial shift to get the window
        self.tee = [islice(self._gen(d), i, None) for i, d in enumerate(self.deques)]  # the iterator
        self.window = []  # Init the window
        # window oversize by m element
        self.oversize = 0

    def _gen(self, mydeque):
        """ From: https://docs.python.org/3/library/itertools.html#itertools.tee
        """
        while True:
            if not mydeque:  # when the local deque is empty
                try:
                    newval = next(self.input_text)  # fetch a new value and
                except StopIteration:
                    return
                for d in self.deques:  # load it to all the deques
                    d.append(newval)
            yield mydeque.popleft()

    def _add_padding(self, iterator, before, after, padstr=lambda: '#'):
        """
        Adds Padding to to the token sequence in a generator form...
        :param iterator: The actual token sequence
        :param before: Before padding length
        :param after: After padding length
        :param padstr:  The stirng to be padded
        :return: Generator: # # tokens # #
        """
        self.paddtogo = after
        for i in range(before):  # repeat(padstr, before)
                yield padstr()
        for j in iterator:
            yield j
        while self.paddtogo > 0:
            self.paddtogo -= 1  # Count down padding...
            yield padstr()

    def extend_window(self):
        """
        Add an other deque to the tee and updates the window if it can
        :return: True or False either on Success or Fail
        """
        try:
            # Make a new empty deque
            self.deques.append(deque())
            # Extend window with deuqe. Keep the new elem!
            self.tee.append(islice(self._gen(self.deques[-1]), 0, None))
            # Get the new extended element if there is any left
            new_elem = next(self.tee[-1])
        except StopIteration:
            return False  # The End no more extend...
        self.oversize += 1  # oversize added
        self.paddtogo += 1  # Increment needed padding
        self.window.append(new_elem)
        return True

    def __next__(self):
        self.window = list(next(zip(*self.tee)))
        return self, self.window

    def __iter__(self):
        return self

    def merge_elems(self, new_elem, from_n, to_n=0):
        if to_n == 0:
            to_n = len(self.window)-1  # No element to keep
        len_orig = to_n - from_n+1
        # FIRST GROUP: Before the selected elements
        # Backup and remove the elements to keep from all queue before the new element's place
        elems_to_keep = []
        for _ in range(from_n-1):                           # For all the elements to keep (before)
            elems_to_keep.append(self.deques[0].popleft())  # Store the last elements to keep from the first queue
            for d in self.deques[1:from_n-1]:               # Remove the last from the others
                d.pop()
        elems_to_keep.reverse()  # For easier pop()-ing...
        # Remove elements to be merged and push back the rest
        for i, d in enumerate(self.deques[0:from_n-1]):
            for _ in range(len_orig):
                d.popleft()
            d.appendleft(new_elem)  # add merged elem
            for e in elems_to_keep[i:]:  # push back the rest
                d.appendleft(e)
        # SECOND GROUP: The selected element is on left. Kill all deque but one
        self.tee[from_n-1:to_n-1] = []              # Kill all but one
        self.deques[from_n-1:to_n-1] = []           # Kill all but one
        self.deques[from_n-1].popleft()             # Remove the element from the last
        self.deques[from_n-1].appendleft(new_elem)  # Add the nem element to the last
        self.paddtogo = len(self.deques) - 1        # Manage the shrinkage of the window (padding)
        self.oversize = len(self.deques) - self.n   # Manage the shrinkage of the window (size)
        for _ in range(-self.oversize):
            self.extend_window()                    # If there is to few element left extend the window...
        # THIRD GROUP: After the merged element. Nothing to do... :)
        # FINALLY: Update window...
        self.window[from_n:to_n+1] = [new_elem]


if __name__ == '__main__':
    print('TEST')
    test = range(13)
    count = 3
    count2 = 7
    for c, (fw, window) in enumerate(FlexibleWindow(test, 3)):
        print(window)
        if c % count == 0:
            print(fw.extend_window())
            print(window)
        elif c == count2:
            print('merge')
            fw.merge_elems('8_9_10_11_12', 1)
            print(window)
    else:
        print('StopIteration as expected')
