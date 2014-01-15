#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
Author: György Orosz
"""

import sys
import os
import codecs
import pickle
from math import log
from operator import itemgetter

from nltk.probability import FreqDist, ConditionalFreqDist
from nltk import __version__ as NLTK_VERSION

from guesser import Guesser


class MorphProbModel():
    UNK_PROB = -99

    def __init__(self,
                 beam=1000,
                 max_guess=20,
                 rare_treshold=10,
                 capitalization=True):
        self._uni = FreqDist()
        self._bi = ConditionalFreqDist()
        self._tri = ConditionalFreqDist()

        self._wd = ConditionalFreqDist()

        self._l1 = 0.0
        self._l2 = 0.0
        self._l3 = 0.0

        self._beam_size = beam
        self._use_capitalization = capitalization
        self._max_guess = max_guess
        self._treshold = rare_treshold

        self._unk = Guesser(10)
        self._analyzer = None
        self.cache = {}

    def set_analyzer(self, obj):
        self._analyzer = obj

    def train(self, data):
        C = False
        for sent in data:
            history = [('BOS', False), ('BOS', False)]
            for w, l, t in sent:
                # Ezt azért szedtem ki mert megeszik 4 giga memóriát ha marad
                # t = encode((w, l, t))
                if self._use_capitalization and w[0].isupper():
                    C = True

                self._wd[w].inc(t)
                self._uni.inc((t, C))
                self._bi[history[1]].inc((t, C))
                self._tri[tuple(history)].inc((t, C))

                history.append((t, C))
                history.pop(0)

                C = False

        for word, fd in self._wd.iteritems():
            for tag, count in  fd.iteritems():
                if count < self._treshold:
                    self._unk.add_word(word.lower(), tag, count)
        self._unk.finalize()

        self._compute_lambda()

    def _compute_lambda(self):
        tl1 = 0.0
        tl2 = 0.0
        tl3 = 0.0

        for history in self._tri.conditions():
            (h1, h2) = history

            for tag in self._tri[history].samples():

                if self._uni[tag] == 1:
                    continue

                c3 = self._safe_div((self._tri[history][tag] - 1),
                                    (self._tri[history].N() - 1))
                c2 = self._safe_div((self._bi[h2][tag] - 1),
                                    (self._bi[h2].N() - 1))
                c1 = self._safe_div((self._uni[tag] - 1), (self._uni.N() - 1))

                if (c1 > c3) and (c1 > c2):
                    tl1 += self._tri[history][tag]

                elif (c2 > c3) and (c2 > c1):
                    tl2 += self._tri[history][tag]

                elif (c3 > c2) and (c3 > c1):
                    tl3 += self._tri[history][tag]

                elif (c3 == c2) and (c3 > c1):
                    tl2 += float(self._tri[history][tag]) / 2.0
                    tl3 += float(self._tri[history][tag]) / 2.0

                elif (c2 == c1) and (c1 > c3):
                    tl1 += float(self._tri[history][tag]) / 2.0
                    tl2 += float(self._tri[history][tag]) / 2.0

                else:
                    pass

        self._l1 = tl1 / (tl1 + tl2 + tl3)
        self._l2 = tl2 / (tl1 + tl2 + tl3)
        self._l3 = tl3 / (tl1 + tl2 + tl3)

    def _safe_div(self, v1, v2):
        if v2 == 0:
            return -1
        else:
            return float(v1) / float(v2)

    def _transition_prob(self, t, C, history):
        p_uni = self._uni.freq((t, C))
        p_bi = self._bi[history[-1]].freq((t, C))
        p_tri = self._tri[tuple(history[-2:])].freq((t, C))
        p = self._l1 * p_uni + self._l2 * p_bi + self._l3 * p_tri
        if p == 0.0:
            return self.UNK_PROB
        return log(p, 2)

    def _known_lexical_prob(self, word, t, C):
        p = float(self._wd[word][t]) / float(self._uni[(t, C)])
        return log(p, 2)

    def _analyze(self, word):
        tag_candidates = []
        if word in self._wd.conditions():
            tag_candidates = set(self._wd[word].samples())
        else:
            analyses = map(itemgetter(1), self._analyzer.analyze(word))
            guesses = self._unk.get_probs(word.lower())
            guesses = map(itemgetter(0),
                          sorted(guesses.iteritems(), reverse=True,
                     key=itemgetter(1))[:self._max_guess])
            tag_candidates = set(guesses)
            if analyses:
                tag_candidates &= set(analyses)
            if not tag_candidates:
                tag_candidates = set(guesses)
        return tag_candidates

    def _lexical_prob(self, word, t, C):
        if word in self._wd.conditions():
            return self._known_lexical_prob(word, t, C)
        else:
            return self._unk.get_prob(word, t)

    def tag(self, sent, n=5):
        current_state = [(['BOS', 'BOS'], 0.0)]
        out = self._tagword(sent, current_state, n)
        return out

    def _tagword(self, sent, current_states, n=5):
        # A cache-sel elég gyors. Nem érdemes jobban vesződni vele.
        if sent == []:
            # yield ...
            return [(map(itemgetter(0), tag_seq[0][2:]),
                          tag_seq[1]) for tag_seq in current_states[:n]]

        word = sent[0]
        sent = sent[1:]
        new_states = []

        # Cache lookup
        sent_str = word + str(current_states)
        if sent_str in self.cache:
            return self._tagword(sent, self.cache[sent_str], n)

        C = False
        if self._use_capitalization and word[0].isupper():
            C = True

        analyses = self._analyze(word)

        for (history, curr_sent_logprob) in current_states:
            logprobs = []

            for t in analyses:

                p_t = self._transition_prob(t, C, history)
                p_l = self._lexical_prob(word, t, C)

                p = p_t + p_l

                logprobs.append(((t, C), p))

            for (tag, logprob) in logprobs:
                new_states.append((history + [tag],
                                   curr_sent_logprob + logprob))

        new_states.sort(reverse=True, key=itemgetter(1))

        if len(new_states) > self._beam_size:
            new_states = new_states[:self._beam_size]

        # Cache store
        self.cache[sent_str] = new_states

        # yield new_states
        # self._tagword(sent, new_states, n)
        return self._tagword(sent, new_states, n)


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


def read_corpus(file_path):
    lines = [[itemgetter(0, 1, 2)(tok.split("#")) for tok in line.strip().split()]
                for line in codecs.open(file_path,
                                        encoding="utf8").readlines()]
    return lines


# Module init
def init_POS(model_file, analyzer):
    model = pickle.load(open(model_file, "rb"))
    model.set_analyzer(analyzer)
    return model


# For External use
def pickle_POS(model_file, training_data_file):
    model = MorphProbModel()
    model.train(read_corpus(training_data_file))
    pickle.dump(model, open(model_file, "wb"))


def main(model_file, training_data_file, server_port):
    if train:
        print "Training..."
        pickle_POS(model_file, training_data_file)
        print "Success!"
        exit(0)
    else:

        # Humor LOAD BEGIN
        sys.path.append(os.path.abspath(".."))
        from humor_dummy import Humor
        analyzer = Humor()
        # Humor LOAD END

        print "Loading model..."
        model = init_POS(model_file, analyzer)
        # Source: http://ilab.cs.byu.edu/python/socket/echoserver.html
        if server_port:
            import socket
            host = ''
            port = server_port  # 50000
            backlog = 5
            size = 65536
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((host, port))
            s.listen(backlog)
            print "UP & Running@%d" % port
            while 1:
                client, address = s.accept()
                print "Got Client: %s" % str(address)
                data = client.recv(size)
                if data:
                    ans = model.tag(pickle.loads(data), n=5)
                    #print "Got Data: %s" % data
                    client.send(pickle.dumps(ans))
                    client.close()
        else:
            from pprint import pprint
            print "It's yourt turn!"

            for line in sys.stdin:
                inp = line.decode("utf8").strip().split()
                pprint(model.tag(inp, n=5))

if __name__ == "__main__":
    port = 0
    if NLTK_VERSION[0] == "2":
        print "NLTK minimum version is 3.0a3!"
        exit(1)
    if len(sys.argv) == 3:
        mod = sys.argv[1]
        train = sys.argv[2]
    elif  len(sys.argv) == 2:
        mod = sys.argv[1]
        train = None
    elif  len(sys.argv) == 4 and sys.argv[2] == "--server":
        mod = sys.argv[1]
        train = None
        port = int(sys.argv[3])
    else:
        print "Usage: Train: python " + sys.argv[0] + " model.txt train.txt"
        print "Usage: Test: python " + sys.argv[0] + " model.txt [--server port(50000)]"
        exit(1)
    main(mod, train, port)
