#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Counter, defaultdict
from operator import itemgetter
from math import log
import os
import sys
import pickle
import argparse


class MorphologicalGuesser(object):
    def __init__(self, max_length):
        """
        A node is: {suffix, ({tag, tag_count}, suffix_count)}
        """
        self.__max_length = max_length
        self.__repr = dict()
        self.__tags = defaultdict(int)
        self.__words_num = 0

    def __del__(self):
        sys.stdout.flush()
        sys.stderr.flush()

    def train(self, taggedWords):
        taggedWords = Counter(taggedWords)
        for (word, tag), count in taggedWords.iteritems():
            self.__add_word(word, tag, count)
        self.__tags = dict(self.__tags)
        self.__theta = self.__get_theta()

    def __word_suffixes(self, word):
        cut = min(len(word), self.__max_length)
        length = len(word)
        return map(lambda i: word[length - i:],
                   range(cut + 1))

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
                    decoded_tag = decode(word, tag)
                    rel_freq = count / suffix_count
                    ret[decoded_tag] = (ret[decoded_tag] + rel_freq * \
                      self.__theta) / (self.__theta + 1)
        return dict(ret)

    def get_prob(self, word, tag):
        res = self.get_probs(word)
        ret = {}
        for k, val in res.iteritems():
            if k[2] == tag:
                ret[k[1]] = val
        return ret


#def testSuffix():
#   g = Guesser(10)
#   print g._Guesser__word_suffixes("alma")
#
#def testBuild():
#   g = Guesser(3)
#   inp = [u"Aladar[FN][NOM]", u"Aladar[FN][NOM]", u"auto[FN][NOM]",
#          u"ad[IGE][Te3]", u"bar[IGE][Te3]"]
#   inp = [(x[:x.find("[")], x[x.find("["):]) for x in inp]
#   g.train(inp)
##  from pprint import pprint
##  pprint(g._Guesser__repr)
#   print g.get_probs("auto")
#   print g.get_probs("alma")
#
def coding_test():
    print decode(*encode((u"almája", u"alma", u"T")))
    print decode(*encode((u"alma", u"alma", u"T")))
    print decode(*encode((u"fázik", u"fázni", u"T")))


def encode(tok):
    word = tok[0]
    lemma = tok[1]
    i = 0
    for c1, c2 in zip(word, lemma):
        if c1 != c2:
            break
        i += 1
    remove = len(word) - i
    add = lemma[i:]
    return tok[0], (remove, add, tok[2])


def decode(tok, code):
    remove, add, tag = code
    lemma = tok[:len(tok) - remove] + add
    return tok, lemma, tag


def read_file(infile, encoding):
    import codecs
    tokens = codecs.open(infile, encoding=encoding).read().split()
    ret = filter(len, [tuple(x.split(u"#")) for x in tokens])
    return map(encode, ret)


def guess(guesser, word, max_guess, hide_score):
    guesses = sorted(guesser.get_probs(word).iteritems(), reverse=True,
                     key=itemgetter(1))[:max_guess]

    if not hide_score:
        guesses = map(lambda x: u"%s#%f" % (u"#".join(list(x[0])),
                                            log(x[1])),
                                            guesses)
    else:
        guesses = map(lambda x: u"#".join(list(x[0])), guesses)
    return u"\t".join(guesses)


def train(training_data, encoding="UTF-8", length=10):
    taggedWords = read_file(training_data, encoding)
    g = MorphologicalGuesser(length)
    g.train(taggedWords)
    return g


class word_guesser:
    g = None

    def __init__(self, training_data):
        self.g = train(training_data)

    def guess(self, word):
        return map(lambda x: x.split("#")[1] + x.split("#")[2],
                             guess(self.g, word, 10, True).split("\t"))


def main():
    parser = argparse.ArgumentParser(description="Morphological guesser")
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
    g = train(args.training_data, args.encoding, args.length)
    for word in sys.stdin:
        word = word.strip().decode(args.encoding)
        print guess(g,
                    word,
                    args.guesses,
                    args.hide_score).encode(args.encoding)


# Module init
def init_MGuesser(model_file):
    return pickle.load(open(model_file, "rb"))


# For External use
def pickle_MGuesser(model_file, training_data_file):
    model = word_guesser(training_data_file)
    pickle.dump(model, open(model_file, "wb"))


# Kiíró függvény, ami magában foglalja az encode-olást.
def printout(text, newline=u"\n"):
    sys.stdout.write((text + newline).encode('utf-8'))
    sys.stdout.flush()


def load_model(MGuesser):
    if not os.path.isfile(MGuesser['model_file']):
        printout(u"Creating pickle of the Morphological guesser model...", u"")
        pickle_MGuesser(MGuesser['model_file'], MGuesser['training_data'])
        printout(u"Done")

    printout(u"Loading Morphological guesser model...", u"")
    guesser = init_MGuesser(MGuesser['model_file'])
    printout(u"Done")

    return guesser

if __name__ == "__main__":
    #main()
    #coding_test()

    test = None  # u"TEST"

    MGuesser = {}
    server_port = 0

    if test == u"TEST":
        # Szeged korpusz 100 mondata teszt célokra
        MGuesser['training_data'] = os.path.abspath(u"sz100.txt")
        MGuesser['model_file']    = os.path.abspath(u"szeged_MGuesser_model_test")

    else:
        # Szeged korpusz
        MGuesser['training_data'] = os.path.abspath(u"szeged_corpus.txt")
        MGuesser['model_file']    = os.path.abspath(u"szeged_MGuesser_model")

    if  len(sys.argv) == 3 and sys.argv[1] == "--server":
        server_port = int(sys.argv[2])
    else:
        print "Usage: Test: python " + sys.argv[0] + " [--server port(60000)]"
        print "Or no argument for interactive session"
        print "Starting interactive session:"

    guesser = load_model(MGuesser)
    # Source: http://ilab.cs.byu.edu/python/socket/echoserver.html
    if server_port:
        import socket
        host = ''
        port = server_port  # 60000
        backlog = 5
        size = 65536
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host,port))
        s.listen(backlog)
        print "UP & Running@%d" % port
        while 1:
            client, address = s.accept()
            print "Got Client: %s" % str(address)
            data = client.recv(size)
            if data:
                ans = guesser.guess(data.decode("utf8"))
                #print "Got Data: %s" % data
                client.send(pickle.dumps(ans))
                client.close()
    else:
        print guesser.guess(u"alma")
        print guesser.guess(u"körte")
        print "It's yourt turn!"
        for line in sys.stdin:
            inp = line.decode("utf8").strip().split()
            print guesser.guess(inp)
