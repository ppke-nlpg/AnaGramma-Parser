#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
Ennek a fájlnak az a feladata, hogy elfedje a többi rész elől a mofológiát és az ablakot 1:1
Tehát megoldandók:
- Humor integráció, az jöjjön ki címke szinten, amit várunk
- Tokenizálás
- Mozaikgram look-up
- Szófaji egyértelműsítés (?)
- Ablakba rendezés + harmónika ablak (det, adj kihagyható de ezt szeretnénk definálni
    + a karakter szám is azért legyen limitálva stb)
"""

import sys  # debug
import json
import requests

from engine.token_rep import Token
from engine.flexibleWindow import FlexibleWindow
from ling_rules.morphconverter.morphologyConverter import morph_converter


def _morphology_lookup(word):
    """
        Morphology lookup and preprocessing
    :param word: word
    :return: token(s)
    """
    # Integral token numbers, token list...           # todo: HACK NINCS több anal
    ret = []
    # todo: Itt tokenizálunk... !!! ITT LESZ EGY SZÓBÓL TÖBB !!!
    # Az alma, de nem a körte.
    # Az#... [alma#... ,#...] de#... nem#... a#... [körte#... .#...]
    for morph_anals in [[morph_converter(word)]]:  # morphologyP[word]:
        #    Split morphology output and make feature lists from it...
        spiltted_anals = []
        for morph_anal in morph_anals:
            mainPOS, rest = morph_anal.split(':', maxsplit=1)
            anal_parts = [mainPOS]
            if len(rest) > 1:
                stem, *other_parts = rest.split('+')
                anal_parts.extend(other_parts)
            else:
                stem = rest
            spiltted_anals.append({'anal': morph_anal, 'anal_parts': anal_parts, 'stem': stem})

        ret.append(Token(word.split('#')[0], spiltted_anals[0], purepos_anal=word))
    return ret


def _morphology_generator(iterable, morph):
    """
    Make a generator of Morphologially analysed Tokens !!!!SPLITTED TOKENS APPEARS HERE!!!!

    :param iterable: word iterable
    :param morph: morphology that returns one or more analysed tokens
    :return: iterator of tokenised, analysed tokens
    outer morphology(a = 'alma,' -> a= ['alma', ',']) is split into separate generator elements
    """
    token = []
    i = iter(iterable)
    while True:
        if len(token) == 0:
            nexti = next(i)  # todo: a mozaikgrammok összerakása + egyértelműsítés is itt történik...
            token = morph(nexti)  # Morphology API
        # if mozaik(token[0]):
        # Várunk még elemre, különben összerakjuk vagy továbbengedjük és ledaráljuk a puffert...
        yield token.pop(0)


def _detokenize(text) -> list:
    """
    Dummy detokenizer: Glued to the left...
    :param text:
    :return:
    """
    i = next((i for i, e in enumerate(text) if e.endswith('#[PUNCT]')), None)
    while i is not None:
        token, stem, tag = text[i-1].split('#')
        ptok, pstem, ptag = text[i].split('#')
        text[i-1:i+1] = ['#'.join([token+ptok, stem, tag+ptag])]
        i = next((i for i, e in enumerate(text) if e.endswith('#[PUNCT]')), None)
    return text


# FŐ FÜGGVÉNY EZT HASZNÁLJUK KÍVÜL!!!!
def prepare_input(input_text, n, mosaics, debug=False):
    """
    Add padding analyse with morphology and make windows...
    :param mosaics: list of mosaic n-grams to join
    :param input_text: iterable of the input words
    :param n: positive int, the length of the window
    :param debug: Help debuging with seeing what happening actually in the process...
    :return: window iterator
    """
    input_text_for_purepos = list(input_text)  # PurePOS cheat!
    # input_text_for_purepos.reverse()  # Just to suppress the IDE's warining message...
    # XXX: PurePOS tagging omited, for speed...
    # purePOS_out = pp.tag_sentence(' '.join(input_text_for_purepos))
    # input_text_purepos_tagged = eval(purePOS_out)[0]
    tagged_json = requests.post('http://XXX.TODO.hu/purepos/postag',
                                json=json.dumps({'sent': ' '.join(input_text_for_purepos)}),
                                auth=('USER', 'PASS')).text
    input_text_purepos_tagged = json.loads(tagged_json)['tagged']
    input_text_purepos_tagged = input_text_purepos_tagged
    input_text_purepos_tagged_detokenized = _detokenize(input_text_purepos_tagged)
    input_text_mosaic_hack = mosaics.merge_mosaic_tokens(input_text_purepos_tagged_detokenized)[0]
    # input_text_mosaic_hack = input_text_purepos_tagged_detokenized

    # Dummy Padding Token...
    def padding_token():
        return Token('#', {'anal': '||:NYITO', 'anal_parts': ['||', 'NYITO'], 'stem': 'NYITO'})

    # todo: Ez majd máshogy lesz, ha lesz rendes PurePOS
    # Itt olyan token n-gram iterátort várok kimenetnek, ami már megoldja:
    # a tokenizálás, a mozaikgram és az morfológiai egyértelműsítés problémáját...
    morph_analysed = _morphology_generator(iter(input_text_mosaic_hack), _morphology_lookup)
    if debug:
        return morph_analysed
    return iter(FlexibleWindow(morph_analysed, n, padding_token))


if __name__ == '__main__':
    print('DEBUG:', file=sys.stderr)
    uterance = ['Holnap a korábbi elnökjelölttel egyeztet a megválasztott elnök. '
                ' Trump a sajtóhírek szerint miniszteri posztot ajánl fel a kampánya alatt őt kritizáló politikusnak.']
    sentence = ['Holnap a korábbi elnökjelölttel egyeztet a megválasztott elnök.',
                'Trump a sajtóhírek szerint miniszteri posztot ajánl fel a kampánya alatt őt kritizáló politikusnak.',
                '',
                'Az Országgyűlés elfogadta a kormány őszi adócsomagját.',
                'Legfontosabb elemének a kabinet a köztehercsökkentést tartja.',
                'A változtatások miatt nő a kisadózó vállalkozások tételes adójának bevételi határa.',
                'Az adóhatóság később szakmai segítségnyújtással támogatja a hibázó adózókat.',
                '',
                'A kormányzati rezsicsökkentéshez kapcsolódó újabb törvényjavaslat tárgyalásával '
                'foglalkozhat az Országgyűlés következő ülésén.',
                'A parlament tegnap két jogszabályt hozott a fogyasztói gázár mérséklésének érvényesítésére.',
                'A képviselők ezúttal a vízdíjak csökkentéséről kezdhetnek tárgyalni.',
                '',
                'Fenntarthatatlannak nevezte a kormány rezsicsökkentési programját az LMP.',
                '',
                'A magyar érdemrend középkeresztjét kapta meg tegnap Polgár_Judit.',
                '',
                'Ma várják az önkéntesek jelentkezését a Hősök terén.',
                'Folyamatosan indulnak a buszok a havazás által leginkább sújtott útszakaszokhoz.',
                'Mintegy ötszáz autó vesztegel az utakon.',
                'A honvédség folyamatosan részt vesz a mentési munkálatokban.',
                'A Volánbusz rendkívüli közlekedési rend szerint indítja járatait.',
                '',
                'A szegényekért fellépő egyházat szeretne az új pápa.',
                'Ferenc_pápa erről a sajtó munkatársainak tartott audienciáján beszélt.']

    from ling_rules.mosaic import mosaic_list, test_text

    print(join_mosaics(test_text.split(), mosaic_list))
    """
    for sent in sentence:
        if sent != '':
            for tok in prepare_input(sent.split(), 3, mos_list, debug=True):
                print('\t'.join(tok.WLT_from()))
        print()
    """