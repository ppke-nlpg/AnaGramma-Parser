#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-


class Pool:
    def __init__(self):
        self.tokens = []
        self.borders = {'|': [], '||': []}
        self.searchers = []

    def set_border(self, border_type, border_index):
        self.borders[border_type].append(border_index)

    # Add searcher to searchers
    def put_searcher(self, searcher):
        self.searchers.append(searcher)

    # Calculate the appropriate border for left search
    def _calculate_border_index(self, border, initiator):
        if len(self.borders[border]) == 0:  # No borders yet -> border_index = 0
            border_index = 0
        else:
            border_index = self.borders[border][-1]  # Last border.
        if border_index == initiator.index():        # Only if not the same token
            if len(self.borders[border]) <= 1:       # If it is check the previous border if any
                border_index = -1
            else:
                border_index = self.borders[border][-2]

        return border_index

    # maincond, subcond
    def search_by_condition(self, initiator, cond, border, back_till_index, unique):
        border_index = self._calculate_border_index(border, initiator)

        if back_till_index is not None:
            back_till = max(border_index + 1, back_till_index)  # Calculate back window size...
        else:
            back_till = border_index + 1  # By condition

        hits = []
        for t in reversed(self.tokens[back_till:-1]):  # Check every token for condition
            if t.unifies_w_token(cond):
                if unique:
                    return t  # Need only one
                else:
                    hits.append(t)
        if len(hits) > 0:
            return hits
        else:
            return None

    # A Token matches any searcher in the pool
    def check_searchers(self, tok):
        keep = []
        for s in self.searchers:
            border_index = self._calculate_border_index(s.border, s.initiator)

            if tok.unifies_w_token(s.condition):
                if s.unique:
                    s.hit = tok  # Need only one
                    reuse, ret = s.hit_function()  # Handle if something is (not) found...
                    if reuse:
                        keep.extend(ret)
                    continue  # Delete it from the pool...

                else:
                    if s.hit is None:
                        s.hit = []
                    s.hit.append(tok)
                    reuse, ret = s.hit_function()  # Handle if something is (not) found...
                    if reuse:
                        keep.extend(ret)  # Here we keep the original searcher too!

            elif border_index == tok.index():
                reuse, ret = s.hit_function()  # Handle if something is (not) found...  # Border!
                if reuse:
                    keep.extend(ret)
                continue  # Delete it from the pool...

            keep.append(s)  # Keep this searcher...
        self.searchers = keep

    def __repr__(self):
        return 'Pool({0})'.format(', '.join([str(self.tokens), str(self.borders), str(self.searchers)]))
