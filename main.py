#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import sys

from ling_rules.mainActions import PatternToAction
from ling_rules.patternsAndActions import patterns
from ling_rules.mosaic import mosaic_list
from engine.mosaic_engine import Mosaic
from engine.pool import Pool
from engine.utils import unify_till_pass
from engine.windowedMorphology import prepare_input

sentence = ['Holnap a korábbi elnökjelölttel egyeztet a megválasztott elnök.',
            'Donald Trump a sajtóhírek szerint miniszteri posztot ajánl fel a kampány alatt őt kritizáló politikusnak.',
            '',
            'Az Országgyűlés elfogadta a kormány őszi adócsomagját.',
            'Legfontosabb elemének a kabinet a köztehercsökkentést tartja.',
            'A változtatások miatt nő a kisadózó vállalkozások tételes adójának bevételi határa.',
            'Az adóhatóság később szakmai segítségnyújtással támogatja a hibázó adózókat.',
            '',
            'A kormányzati rezsicsökkentéshez kapcsolódó újabb törvényjavaslat tárgyalásával '
            'foglalkozhat az Országgyűlés a következő ülésen.',
            'A parlament tegnap két jogszabályt hozott a fogyasztói gázár mérséklésének érvényesítésére.',
            'A képviselők ezúttal a vízdíjak csökkentéséről kezdhetnek tárgyalni.',
            '',
            'Fenntarthatatlannak nevezte a kormány rezsicsökkentési programját az LMP.',
            '',
            'A magyar érdemrend középkeresztjét kapta meg tegnap Polgár Judit.',
            '',
            'Ma várják az önkéntesek jelentkezését a Hősök terén.',
            'Folyamatosan indulnak a buszok a havazás által leginkább sújtott útszakaszokhoz.',
            'Ötszáz autó vesztegel az utakon.',
            'A honvédség folyamatosan részt vesz a mentési munkálatokban.',
            'A Volánbusz rendkívüli közlekedési rend szerint indítja a járatokat.',
            '',
            'A szegényekért fellépő egyházat szeretne az új pápa.',
            'Ferenc pápa erről a sajtó munkatársainak tartott audiencián beszélt.',
            '',
            'Én elmentem a vásárba.',
            '',
            'Elmegyek a vásárba.',
            '',
            'A kutyád hangosan ugat.',
            '',
            'Utállak.',
            '',
            'Utál minket.',
            '',
            'Szereti Marit.',
            '',
            'Két konstrukciót ajánl a devizahiteleseknek a Bankszövetség.',
            '',
            'Két konstrukciót ajánlottak a devizahiteleseknek.',
            '',
            'Géza bácsi megtanította a halakat repülni.',
            '',
            'Itt most elkezdődött valami.',
            '',
            'Péter szereti Marit.',
            '',
            'Szereti Marit Péter.',
            '',
            'Szereti Marit.',
            '',
            'Szerintem nemsokára el fogod akarni adni a kocsidat.',
            '',
            'Elveszett a laptopja Marcinak.',
            '',
            'Elveszett Marci laptopja.',
            '',
            'Elveszett Marcinak a laptopja.',
            '',
            'Engem nem érdekel a gyakran indokolatlanul lesújtó véleménye a férfiaknak a divatról.',
            '',
            'A macskám eddig képtelen volt felmászni a szekrényre.',
            '',
            'Megfelelve a kritériumoknak Mari nyugodtan bízhat a kedvező döntésben.',
            '',
            'A lap értesülései szerint a városhatáron átlépő HÉV-pályákat a MÁV szabványait is figyelembe véve újítják'
            ' fel.',
            'Ezeket új szakaszok építésekor össze is kötik az állami vasúttársaság elővárosi vonalaival.',
            '',
            'Kórházba vitték Sonia Gandhit.',
            'A politikus a parlamentben lett rosszul.',
            'Az intenzív osztályra vitték, de már elhagyhatta a kórházat.',
            '',
            'Napszámos órának nevezett szobrot állítanak vasárnap Rimóc községben a mezőgazdasági bérmunkások'
            ' tiszteletére.',
            '',
            'Peti elég csokit evett.',
            '',
            'Megjött a lányok nagynénje.',
            '',
            'Lakik orvos a szállodában.',
            '',
            'Nincs változás a pártok versenyében.',
            '',
            'Az eljárások lezárása nem előfeltétele a hiteltárgyalásnak.',
            '',
            'Magyarországnak fontos Szerbia uniós tagjelöltsége.',
            '',
            'Magyarországnak fontos volt Szerbia uniós tagjelöltsége.',
            '',
            'Az embereknek fontos kérdésekkel kell foglalkozni az EU-ban.',
            '',
            'Budapestnek fontos politikai kapcsolatai vannak meghatározó orosz körökkel.',
            '',
            'Egyedül a Chelsea-t verő MU százszázalékos Angliában.',
            '',
            'Teljes a káosz a kötelező biztosítások körül.',
            '',
            '2012 a gyermekbarát igazságszolgáltatás éve.',
            '',
            'Elveszett a türelmed.'
            ]

fromSTDIN = True
# default_text = 'Két konstrukciót ajánl a devizahiteleseknek a Bankszövetség.'
# 0:2 3:7 8:12 12:13 14:15 16:22 22:25 26:27
sentences = [slice(0, 2), slice(3, 7), slice(8, 12), slice(12, 13), slice(14, 15), slice(16, 22), slice(22, 25),
             slice(25, 26), slice(27, 28), slice(29, 30), slice(31, 32), slice(33, 34), slice(35, 36), slice(37, 38),
             slice(39, 40), slice(41, 42), slice(43, 44), slice(45, 46), slice(47, 48), slice(49, 50), slice(51, 52),
             slice(53, 54), slice(55, 56), slice(57, 58), slice(59, 60), slice(61, 62), slice(63, 64), slice(65, 67),
             slice(68, 71), slice(72, 73), slice(74, 75), slice(76, 77), slice(78, 79), slice(80, 81), slice(82, 83),
             slice(84, 85), slice(86, 87), slice(88, 89), slice(90, 91), slice(92, 93), slice(94, 95), slice(96, 97),
             slice(98, 99)]

default_text = ' '.join(sentence[sentences[0]])
default_n = 3  # Default window size

# --------------- Start of search functions in the code...  ---------------


def prepare_and_fire(pattern_bank, pool, handle, curr_window):
    repr(handle)  # Dummy action to suppress the IDE's warining...
    tok = curr_window[0]
    pool.tokens.append(tok)  # Last input token will be the last in the window

    # Here the actual word triggers all patterns into curr_patts...
    curr_patts = []
    for part in tok.attrs['anal_parts']:
        print('feature', part, 'other', tok.index(), file=sys.stderr)
        patt = pattern_bank.get_pattern(part, tok.n)
        if patt is not None:
            curr_patts.append(patt)
        # else:
        #    print(part)  # Unhandled morphological elements
    # Then the list is flattened (One pattern can trigger one, multiple or no actions)
    actions = []
    for patt in curr_patts:
        # TODO: Emit signal to add supply here...
        todo = patt(tok, pool)  # Generate Searchers, trigger token feature setters...
        if todo is not None:  # Not a token feature setter (which is already triggered), but a list of searchers
            # TODO: Emit signal to add demand here...
            actions.extend(todo)

    if len(actions) > 0:
        # Lookahead: Steps in the window...
        for i, tok in enumerate(curr_window):
            # Uinfies all Searchers till nothing can be unified...
            actions = unify_till_pass(actions)
            new_actions = []
            while len(actions) > 0:  # Do search...
                act = actions.pop(0)  # TODO: Here we should add some determinism for easier debuging!
                reuse, ret = act.search(tok, pool, is_rightmost=i == len(curr_window) - 1)
                # reuse == False => a köv tokennél nézzük újra, reuse == True még ezzel a tokkenel próbálkozunk!
                if reuse:  # [self] Not found, but did not gave up...
                    actions.extend(ret)  # The resulting Searcher(s) go another round... (Direction changed, hit, etc.)
                    actions = unify_till_pass(actions)
                elif ret is not None:  # Is it putted into the pool or not?
                    new_actions.append(act)  # Preserve for next token...
                # TODO: Emit signal to remove demand here...
            actions = new_actions

    # Searchers in the Pool checks for "Supply"...
    pool.check_searchers(curr_window[0])
    # Token go into the pool...
    pass  # Token already in pool.tokens...

# --------------- Start of the non-functional part of the code...  ---------------


def main(default_input=None):
    pool = Pool()
    pattern_bank = PatternToAction(patterns)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        input_text = open(sys.argv[1], encoding='UTF-8').readlines()[0]
    elif fromSTDIN and not default_input:
        input_text = input('Waiting for STDIN:\n')
    else:
        input_text = default_input
    input_text = iter(input_text.strip().split())

    # To be able to give real input by tokens... (For demo purposes...)
    # Automatic morphological lookup of last item in the window...
    for handle, curr_window in prepare_input(input_text, default_n, Mosaic(mosaic_list)):
        if not (curr_window[0].tok == '#' and curr_window[1].tok == '#'):
            print('token', curr_window[0].n, curr_window[0].tok, curr_window[0].attrs['anal'].split(':')[0],
                  file=sys.stderr, flush=True)
            print(curr_window[0].n, '|\t|'.join(i.attrs['anal'] for i in curr_window), flush=True)

        prepare_and_fire(pattern_bank, pool, handle, curr_window)   # Do everything functional...

        # Print what needed...
        if not (curr_window[0].tok == '#' and curr_window[1].tok == '#'):
            print(str(curr_window[0]), end='\n\n', flush=True)

    # XXX At the end sum...


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        default_text = ' '.join(sentence[sentences[int(sys.argv[2])]])
    elif fromSTDIN:
        default_text = ''
    main(default_text)

# EZ már olyan csúnya hack, hogy szép!
# from itertools import repeat
# def default_rule_once(fun):
#     return next(repeat(fun, 1), None)
