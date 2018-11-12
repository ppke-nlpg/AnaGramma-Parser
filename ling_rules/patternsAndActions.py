#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
import inspect


from ling_rules.mainActions import pers_search_fun, fin_search_fun, make_dborder, make_border, det_search_fun, \
    npmod_search_fun, focus_search_fun, det_restrictor_search_fun, focus_restrictor_search_fun,\
    vframe_nom_blocker_search_fun, nom_or_what_search_fun, set_feature, \
    vframe_direction_restrictor_search_fun, vframe_nom_acc_restrictor_search_fun,\
    mod_search_fun, postp_search_fun

from engine.pool import Pool
from engine.searcher import Searcher
from engine.utils import flatten
from engine.token_rep import Token


# Debug pattern rules
def inspect_patterns(patts):
    for p in patts:
        just_width = 0
        elems = []
        patt = patterns.get(p)
        if patt is not None:
            text, line_no = inspect.getsourcelines(patt)
            just_width = max(just_width, len(str(line_no)), len(str(line_no + len(text) - 1)))
            elems.append((p, (text, line_no)))
        else:
            elems.append((p, (None, None)))

        form = '{0:>' + str(just_width) + '}: {1}'
        for pa, (text, no) in elems:
            print('--- {0} ---'.format(pa))
            if text is None and no is None:
                print('ERR: PATTERN NOT FOUND IN THE PATTERN BANK: {0}'.format(p))
            else:
                for l, t in enumerate(text, start=no):
                    print(form.format(l, t), end='')


def expand_macros(patts, macro):
    new_patterns = {}
    to_expand = []
    for k, v in patts.items():
        if k in macro:
            to_expand.append((k, v))
        else:
            new_patterns[k] = v
    for k, v in to_expand:
        for m in macro[k]:
            if m not in new_patterns.keys():
                new_patterns[m] = v
            else:
                print('DUPLICATE PATTERN IN MACRO EXPANSION FOR {0}: {1} AND {2}'.
                      format(m, new_patterns[m], v), file=sys.stderr)
    return new_patterns

# ----------------------------------------------------------------------------------------------------------------------


def end_sentence(*_) -> [Searcher] or None:  # tok, pool
    pass  # véglegesítő (keresletgyilkos, alanykijelölő, zérókopula), vonzathiány-jelző


def NYITO_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return fin_search_fun(tok)


def ZARO_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    return end_sentence(tok, pool)  # Mondatvég esemény...


def DHATAR_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_dborder(tok, pool)  # '#' határ: || határ also makes a | határ


def PUNCT_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_dborder(tok, pool)  # PUNCT határ: || határ also makes a | határ


def Det_Def_fun(tok: Token, _: Pool) -> [Searcher] or None:
    """
    - esetes (0 is): N Det-et keres, talál maga előtt egyet, összekapcsolódnak (a fekete kutya)
    - tulajdonnév: valamiféle listából, hoz magával egy Det: 0+Def elemet. itt a Det-kereső azért elindul (amiatt,
     mert vannak olyan nyelvjárások, amelyek kiteszik a határozott névelőt a tul.nevek elé, pl és is ilyen vagyok
     (Bejött a terembe a Marci.), valamit a birtokos szerkezetek miatt (a Marci laptopja), ahol a határozott névelőt a
     Marci kapja meg, a laptopja hatérozottságát a birtokoltságtól kapja.) Tehát ha talál, akkor létrejön a Det-él,
     ha nem talál, akkor erre a Det: 0+Def-címkére rajzolja be a Det-élt.
    - birtok: a birtokoltság ténye határozottá tesz, hiszen a birtokos megléte jelöli ki az univerzumban azt a dolgot,
     ami birtokolva van (lásd: egy vers - a Petőfi verse). a Det-szülő akkor hoz létre egy definitséget jelölő elemet,
     ha ezt a definitséget nem adta meg egy határozott névelő a birtok NP-nek. ha volt határozott névelő balra a
     következő határig (Petinek a kutyája), akkor arra kapcsolódik a Det-kereső.

    :return:
    """
    set_feature(tok, 'Det_Def', 'Def')  # Itt igazából csak jellemzőállítás kell...


def Det_Indef_fun(tok: Token, _: Pool) -> [Searcher] or None:
    """
    - esetes (0 is): N Det-et keres, talál maga előtt egyet, összekapcsolódnak (a fekete kutya)
    - tulajdonnév: valamiféle listából, hoz magával egy Det: 0+Def elemet. itt a Det-kereső azért elindul (amiatt,
     mert vannak olyan nyelvjárások, amelyek kiteszik a határozott névelőt a tul.nevek elé, pl és is ilyen vagyok
     (Bejött a terembe a Marci.), valamit a birtokos szerkezetek miatt (a Marci laptopja), ahol a határozott névelőt a
     Marci kapja meg, a laptopja hatérozottságát a birtokoltságtól kapja.) Tehát ha talál, akkor létrejön a Det-él,
     ha nem talál, akkor erre a Det: 0+Def-címkére rajzolja be a Det-élt.
    - birtok: a birtokoltság ténye határozottá tesz, hiszen a birtokos megléte jelöli ki az univerzumban azt a dolgot,
     ami birtokolva van (lásd: egy vers - a Petőfi verse). a Det-szülő akkor hoz létre egy definitséget jelölő elemet,
     ha ezt a definitséget nem adta meg egy határozott névelő a birtok NP-nek. ha volt határozott névelő balra a
     következő határig (Petinek a kutyája), akkor arra kapcsolódik a Det-kereső.

    :return:
    """
    set_feature(tok, 'Det_Def', 'Indef')  # Itt igazából csak jellemzőállítás kell...


def PostP_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_border(tok, pool)
    return flatten((postp_search_fun(tok),))


def CAS_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_border(tok, pool)  # CAS border


def Nom_fun(tok: Token, _: Pool) -> [Searcher] or None:
    # Definition of the action by name... Theoretially, the elements of these function could be parallel.
    # set_feature(tok, 'NOM-OR-GEN', '?')
    return flatten((nom_or_what_search_fun(tok),))


def N_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return flatten((                          # There is no subcondition by default
                    det_search_fun(tok),      # Det-search
                    npmod_search_fun(tok)))   # Adj jelzőkereső: Collect all Adj!


def PropN_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return det_restrictor_search_fun(tok)  # "Lila" Det_search: ['Det def' = Def]


# ###################### SZÁM SZEMÉLYES CUCCOK ############################################################


def Pers_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return pers_search_fun(tok, _, {'SgPl1_3': 'Sg3'})


def pers_SgPl3_fun(tok: Token, _: Pool) -> [Searcher] or None:
    pass
    # Most nem csinál semmit, de majd lesz valami ha kigondoljuk
    # a Hősök tere és a Jancsi és Juliska elmegy egyes vagy többes szám?
    # cond = nested_frozen_fs({'subcond': {'SgPl1_3': {'Sg3', 'Pl3', 'Sg', 'Pl'}}})
    # ballast = nested_frozen_fs({'subcond': {'SgPl1_3': {'Sg3', 'Pl3', 'Sg', 'Pl'}}})
    # return pers_restrictor_search_fun(tok, cond, ballast)


def acc_Def_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Acc', 'subcond': {'Det_Def': 'Def'}},
                                                {'Det_Def': 'Def'})


def acc_Indef_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Acc', 'subcond': {'Det_Def': 'Indef'}},
                                                {'Det_Def': 'Indef'})


def acc_SgPl3_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Acc',
                                                      'subcond': {'SgPl1_3': {'Sg3', 'Pl3', 'Sg', 'Pl'}}},
                                                {'SgPl1_3': 'Sg3'})


def acc_SgPl2_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Acc',
                                                      'subcond': {'SgPl1_3': {'Sg2', 'Pl2'}}},
                                                {'SgPl1_3': 'SgPl2_Pron'})


def nom_Sg1_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': 'Sg1'}},
                                                {'SgPl1_3': 'Sg1'})


def nom_Sg2_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': 'Sg2'}},
                                                {'SgPl1_3': 'Sg2'})


def nom_Sg3_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': {'Sg3', 'Sg'}}},
                                                {'SgPl1_3': 'Sg3'})


def nom_Pl1_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': 'Pl1'}},
                                                {'SgPl1_3': 'Pl1'})


def nom_Pl2_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': 'Pl2'}},
                                                {'SgPl1_3': 'Pl2'})


def nom_Pl3_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return vframe_nom_acc_restrictor_search_fun(tok, {'main': 'Nom', 'subcond': {'SgPl1_3': {'Pl3', 'Pl'}}},
                                                {'SgPl1_3': 'Pl3'})


def Sg1_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Sg1')


def Sg2_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Sg2')


def Sg3_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Sg3')


def Pl1_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Pl1')


def Pl2_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Pl2')


def Pl3_Pron_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Pl3')


def Sg_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Sg')


def Pl_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'SgPl1_3', 'Pl')


# ###################### IGÉS CUCCOK INNEN ################################################################


def FIN_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_border(tok, pool)        # FIN határ
    return flatten([focus_search_fun(tok),  # Fin fókuszkereső
                    mod_search_fun(tok)])


def FOC_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return focus_restrictor_search_fun(tok)


def Inf_fun(tok: Token, pool: Pool) -> [Searcher] or None:
    make_border(tok, pool)
    return vframe_nom_blocker_search_fun(tok)


def PART_fun(tok: Token, _: Pool) -> [Searcher] or None:
    return flatten((vframe_nom_blocker_search_fun(tok),
                    vframe_direction_restrictor_search_fun(tok)))


def weather_fun(tok: Token, _: Pool) -> [Searcher] or None:  # NOM letiltó...
    return vframe_nom_blocker_search_fun(tok)


# Nincs bekötve, csak tudjuk...
def NPMod_fun(tok: Token, _: Pool) -> [Searcher] or None:
    set_feature(tok, 'macro_NPMod', 'YES')


patterns = {'||': DHATAR_fun, 'NYITO': NYITO_fun, 'PUNCT': PUNCT_fun,  # Punktuáció, baromságok
            'CAS': CAS_fun,  # Makrók
            'Pers': Pers_fun,  # Ok 'pers_SgPl3': pers_SgPl3_fun,
            'Φ': Nom_fun, 'PropN': PropN_fun,  # Ok
            'Sg': Sg_fun, 'Pl': Pl_fun,
            'PART': PART_fun,  # Ok, Part problémás!
            'Def': Det_Def_fun, 'Indef': Det_Indef_fun,  # Ok, erről az oldalról...
            'N': N_fun, 'FIN': FIN_fun, 'Inf': Inf_fun,  # OK
            'weather': weather_fun,  # OK, fölösleges
            'FOC': FOC_fun,  # OK, erről az oldalról...
            'acc_Indef': acc_Indef_fun, 'acc_Def': acc_Def_fun,  # Ok
            'acc_SgPl3': acc_SgPl3_fun, 'acc_SgPl2_Pron': acc_SgPl2_Pron_fun,
            'nom_Sg1_Pron': nom_Sg1_Pron_fun, 'nom_Sg2_Pron': nom_Sg2_Pron_fun, 'nom_Sg3': nom_Sg3_fun,
            'nom_Pl1_Pron': nom_Pl1_Pron_fun, 'nom_Pl2_Pron': nom_Pl2_Pron_fun, 'nom_Pl3': nom_Pl3_fun,
            'PostP': PostP_fun,
            'Sg1_Pron': Sg1_Pron_fun, 'Sg2_Pron': Sg2_Pron_fun, 'Sg3_Pron': Sg3_Pron_fun,
            'Pl1_Pron': Pl1_Pron_fun, 'Pl2_Pron': Pl2_Pron_fun, 'Pl3_Pron': Pl3_Pron_fun,
            }  # Maybe RegExp later...

macros = {'CAS': {'Abl', 'Acc', 'Ade', 'All', 'Cau', 'Dat', 'Del', 'Ess', 'Essmod', 'Essnum', 'Fac', 'For', 'FROM+Ela',
                  'Ill', 'Ine', 'Ins', 'Keppen', 'Sub', 'Sup', 'Tem', 'Ter', 'Mul'},
          'PART': {'PartPres', 'PartPast', 'PartFut'}}

patterns = expand_macros(patterns, macros)

if __name__ == '__main__':
    patterns_to_inspect = ('Inf', 'FIN', 'V', 'PropN')
    inspect_patterns(patterns_to_inspect)
