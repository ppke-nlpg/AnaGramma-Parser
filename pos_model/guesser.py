#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Author: György Orosz
"""
from collections import Counter, defaultdict
from operator import itemgetter
from math import log


class Guesser(object):
    def __init__(self, max_length):
        """
        A node is: {suffix, ({tag, tag_count}, suffix_count)}
        """
        self.__max_length = max_length
        self.__repr = dict()
        self.__tags = defaultdict(int)
        self.__words_num = 0

    def train(self, taggedWords):
        taggedWords = Counter(taggedWords)
        for (word, tag), count in taggedWords.iteritems():
            self.__add_word(word, tag, count)
        self.finalize()

    def finalize(self):
        self.__tags = dict(self.__tags)
        self.__theta = self.__get_theta()

    def __word_suffixes(self, word):
        ppos = word.rfind(u"|")
        if ppos < 0:
            ppos = 0
        cut = min(len(word), self.__max_length)
        length = len(word)
        return map(lambda i: word[length - i:],
                   range(ppos, cut + 1))

    def add_word(self, word, tag, count):
        self.__add_word(word, tag, count)

    def __add_word(self, word, tag, count):
        self.__tags[tag] += count
        self.__words_num += 1

        for suffix in self.__word_suffixes(word):
            self.__increment(suffix, tag, count)

    def __increment(self, suffix, tag, count):
        if suffix in self.__repr:
            new_count = self.__repr[suffix][1] + count
            new_table = self.__repr[suffix][0]
            if tag not in new_table:
                new_table[tag] = 0
            new_table[tag] += count
            self.__repr[suffix] = (new_table, new_count)
        else:
            self.__repr[suffix] = ({tag: count}, count)

    def __get_theta(self):
        aprioriProbs = self.__get_apriori_probs()
        pAv = sum(map(lambda x: x ** 2, aprioriProbs.values()), 0)
        theta = sum(map(lambda prob: prob * ((prob - pAv) ** 2),
                        aprioriProbs.values()))
        return theta

    def __get_apriori_probs(self):
        sum_count = float(sum(self.__tags.values(), 0))
        return dict([(key, val / sum_count) \
                    for key, val in self.__tags.iteritems()])

    def get_probs(self, word):
        trie = self.__repr
        ret = defaultdict(int)
        for suffix in self.__word_suffixes(word):
            if suffix in trie:
                suffix_count = float(trie[suffix][1])
                for tag, count in trie[suffix][0].iteritems():
                    rel_freq = count / suffix_count
                    ret[tag] = (ret[tag] + rel_freq * self.__theta) / \
                                        (self.__theta + 1)
        return dict(ret)

    def get_prob(self, word, tag):
        return self.get_probs(word)[tag]


#def testSuffix():
#    g = Guesser(10)
#    print g._Guesser__word_suffixes("alma")
#
#def testBuild():
#    g = Guesser(3)
#    inp = [u"Aladar[FN][NOM]", u"Aladar[FN][NOM]", u"auto[FN][NOM]",
#           u"ad[IGE][Te3]", u"bar[IGE][Te3]"]
#    inp = [(x[:x.find("[")], x[x.find("["):]) for x in inp]
#    g.train(inp)
##    from pprint import pprint
##    pprint(g._Guesser__repr)
#    print g.get_probs("auto")
#    print g.get_probs("alma")
#

def read_file(infile, encoding):
    import codecs
    tokens = codecs.open(infile, encoding=encoding).read().split()
    return filter(len, [(x[:x.find(u"[")], x[x.find(u"["):]) for x in tokens])


def guess(guesser, word, max_guess, hide_score):
    guesses = sorted(guesser.get_probs(word).iteritems(), reverse=True,
                     key=itemgetter(1))[:max_guess]
    if not hide_score:
        guesses = map(lambda x: u"%s#%f" % (x[0], log(x[1])), guesses)
    else:
        guesses = map(lambda x: u"%s" % (x[0]), guesses)
    return word + u"\t" + u"\t".join(guesses)


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Part-of-speech tag guesser")
    parser.add_argument("training_data")
    parser.add_argument("-l", "--length", dest="length", default=10, type=int,
                        metavar="NUM", help="Maximum suffix length, used to \
                        build the model. The default is 10.")
    parser.add_argument("-m", "--max", dest="guesses", default=10, type=int,
                        metavar="NUM", help="Maximum number of guesses. \
                        The default is 10.")
    parser.add_argument("-s", "--hide-score", dest="hide_score", default=False,
                        type=bool, help="Hide the score given to each guess. \
                        The default is 'False'.")
    parser.add_argument("-e", "--encoding", dest="encoding", default="utf-8",
                        type=str, help="Encoding of the input/output stream \
                        and the training data. The default is UTF-8.")
    args = parser.parse_args()
    taggedWords = read_file(args.training_data, args.encoding)
    guesser = Guesser(args.length)
    guesser.train(taggedWords)
    for word in sys.stdin:
        word = word.strip().decode(args.encoding)
        print guess(guesser,
                    word,
                    args.guesses,
                    args.hide_score).encode(args.encoding)

if __name__ == "__main__":
    main()

