#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import sys

from nltk.featstruct import FeatStruct

from engine.searcher import Searcher
from engine.token_rep import Token
from engine.utils import unify_till_pass, nested_frozen_fs, update_nested_frozen_fs, UnifiableSet
from .verbDictionary import verb_prev_restrs_dict, verb_frames, HOL, HOVA


class PatternToAction:
    def __init__(self, pb):
        self.pattern_bank = pb
        self.lastpatt = None
        self.default_fired = False

    def get_pattern(self, patt, n):
        if self.lastpatt != n:
            self.default_fired = False
        self.lastpatt = n

        act = self.pattern_bank.get(patt)
        if act is None and not self.default_fired:
            act = lex_rules_fun
            self.default_fired = True
        return act


def make_edge(from_token, to_token, color, label, occupied=None):
    if occupied is None:  # todo: ez majd a keresőbe integrálva
        set_feature(to_token, 'occupied', {label})
    else:
        if not isinstance(label, set):
            set_feature(to_token, 'occupied', {label, occupied})
        else:
            set_feature(to_token, 'occupied', {occupied})
    print("ÉL KÉSZÜLT", from_token.index(), to_token.index(), color, label)
    print("edge", label, from_token.index(), to_token.index(), color, file=sys.stderr)


def inherit_features_to_token(from_token, to_token):
    from_token.inherit_attrs(to_token)


def set_feature(token, attribute, value=None):    # Value == None akkor az egyéb halmazba rakjuk!
    if value is None:                             # TODO: És még talán kereső triggerelést is csinál a feature
        token.attrs['anal_parts'].add(attribute)  # létrejötte...
        token.other.append(attribute)
        print('feature', attribute, 'other', token.index(), file=sys.stderr)
    elif attribute not in token.attrs:            # TODO: Unifikálódással EZT OLYAN FeatStruct módjára kellene megadni.
        token.attrs[attribute] = value
        print('feature', attribute, value, token.index(), file=sys.stderr)
    elif isinstance(token.attrs[attribute], set):
        token.attrs[attribute] |= value
        print('feature', attribute, value, token.index(), file=sys.stderr)
    else:
        token.attrs[attribute] = value
        print('feature', attribute, value, token.index(), file=sys.stderr)


"""
Keresők paraméterei:

Forrás: Ki indítja?
Irány: Itt lista szerűen meg kell adni, hogy merre keresen. Ezen a listán megy végig. Nincs default sorrend!
Megállási feltétel: | vagy ||
Főteltétel: XXX:... ból az XXX típusú morfológiai jegy vagy * a Jokerhez
Alfeltétel: FeatureStructure vagy semmi
Egyet-keresünk: Igen/Nem
Default akció (nem talált): Semmi, Másik kereső (Dat-birtokos), Jellemző átvétel + Él, Jelemző/Semmi, ???
Talált: Piros vagy Fekete él (forrás, találat), kereső lelövés stb.
Ballaszt: midnen infó, ami máshova nem fér be és madj a hit_function kezd vele valamit...
"""

# A *_search_fun három argumentumot vár: tok, cond és ballast...
# És visszatérésnek [Searcher] listát ad...

# A *_search_fun nem vár argumentumot. Visszaadni egy bool ad vissza aszerint, hogy a visszatérítendő keresőket
#  még az azonos körben unifikáljuk és futtassuk, vagy csak a következő körtől.
# Továbbá vagy visszatérít egy [Searcher] listát vagy None.

# ----------------------------------------------------------------------------------------------------------------------


def make_border(tok, pool, border_type=('|',)):
    for t in border_type:
        if len(pool.borders[t]) == 0 or pool.borders[t][-1] != tok.n:
            pool.borders[t].append(tok.n)


def make_dborder(tok, pool):
    make_border(tok, pool, ('||', '|'))

# ----------------------------------------------------------------------------------------------------------------------


def fin_search_fun(tok: Token, *_) -> [Searcher]:
    # Nincs külső input!
    return [Searcher('FIN', {'main': 'FIN'}, direction=['<', '>'], border='||', max_words_in_direction=None,
                     unique=True, hit_function=fin_hit_fun, initiator=tok)]


def fin_hit_fun(self) -> (bool, [Searcher] or None):
    if self.hit is not None:
        make_edge(self.initiator, self.hit, 'Black', 'Fin')  # él, fekete
    else:
        pass  # ???  todo: Gábor kopula...
    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def npmod_search_fun(tok: Token, *_) -> [Searcher]:  # Nincs külső input!
    return [Searcher('macro_NPMod', {'main': '*', 'other': {'macro_NPMod'}}, direction=['<'], border='|',
                     max_words_in_direction=None, unique=False, hit_function=npmod_hit_fun, initiator=tok)]


def npmod_hit_fun(self) -> (bool, [Searcher] or None):  # If not found, then do nothing
    occupied = False
    hits = []
    if self.hit is not None:
        hits = []
        for i in self.hit:
            if 'occupied' not in i.attrs or self.name not in i.attrs['occupied']:
                hits.append(i)
    if self.hit is not None and not occupied:
        for hit in hits:
            if 'Num' in hit.other:
                label = 'Num'
            elif 'Adj' in hit.other:
                label = 'Adj'
            elif 'PartPres' in hit.other:
                label = 'PartPres'
            elif 'PartPast' in hit.other:
                label = 'PartPast'
            else:
                print('Error:Adj???{0}'.format(hit.attrs), file=sys.stderr, flush=True)
                exit(1)
                label = ''  # SILENCE DUMMY IDE WARNING!
            make_edge(self.initiator, hit, 'Black', label, 'macro_NPMod')  # él, fekete
    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def det_restrictor_search_fun(tok: Token, *_) -> [Searcher]:
    # PropN és Pers megszorító
    # A ballaszt lehet, Def a PropN miatt és a Pers miatt (de a Pers-nél NINCS alfeltétel)
    # cond = {'main': 'Det', 'subcond': ...}
    return [Searcher('Det', {'main': 'Det', 'subcond': {'Det_Def': 'Def'}}, direction=None, border=None,
                     max_words_in_direction=None, unique=None, ballast={'Det_Def': 'Def'}, initiator=tok)]


def det_search_fun(tok: Token, *_) -> [Searcher]:
    # A ballaszt lehet, Def a PropN miatt és a Pers miatt (de a Pers-nél NINCS alfeltétel)
    return [Searcher('Det', {'main': 'Det'}, direction=['<'], border='|', max_words_in_direction=None, unique=True,
                     hit_function=det_hit_fun, ballast={}, initiator=tok)]


def det_hit_fun(self) -> (bool, [Searcher] or None):  # Nincs külső input!  # If not found
    if self.hit is None or ('occupied' in self.hit.attrs and self.name in self.hit.attrs['occupied']):
        if 'Det_Def' in self.ballast:  # Ha Def-et keresett (PropN, Pers)
            set_feature(self.initiator, 'Det_Def', self.ballast['Det_Def'])  # jellemzőállítás Def-re
        else:
            set_feature(self.initiator, 'Det_Def', 'Indef')  # jellemzőállítás Indef-re
        make_edge(self.initiator, self.initiator, 'Black', 'Det')  # Önmagára él
    else:
        inherit_features_to_token(self.hit, self.initiator)  # öröklődik a CAS-ra (found) a jellemző
        make_edge(self.initiator, self.hit, 'Black', 'Det')  # él, fekete
    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def pers_restrictor_search_fun(tok: Token, cond, ballast) -> [Searcher]:
    # Pers megszorító
    # Ő mondja meg a Pers számát és személyét!
    # ballast: {'subcond': {'SgPl1_3': {'Sg3', 'Pl3', 'Sg', 'Pl'}}, 'SgPl1_3':{'Sg3', 'Pl3', 'Sg', 'Pl'}}
    # és méghozzá a ballast.SgPl1_3 konkrét string kell, hogy legyen lásd a zéróbirtokost!
    return [Searcher('Pers', cond, direction=None, border=None, max_words_in_direction=None, unique=None, ballast={},
                     initiator=tok)]


def pers_search_fun(tok: Token, _, ballast) -> [Searcher]:
    # A ballasztba is belemegy az SgPl1_3 amit külön kap meg!
    return [Searcher('Pers', {'main': 'Nom', 'subcond': {'NOM_OR_GEN': 'GEN'}, 'other': {'N'}}, direction=['<'],
                     border='||', max_words_in_direction=None, unique=True, hit_function=pers_nom_left_hit_fun,
                     ballast=ballast, initiator=tok)]


# Ezt összevonni a pers_dat_left_hit_fun-al mert csak az irányban különböznek?
def pers_nom_left_hit_fun(self) -> (bool, [Searcher] or None):  # itt kell a Searcher-hez hozzáférés...  # If found
    if self.hit is not None and ('occupied' not in self.hit.attrs or self.name not in self.hit.attrs['occupied']):
        self.hit.main = 'Gen'  # a Nom-ot Gen...
        make_edge(self.initiator, self.hit, 'Red', 'Gen', 'Pers')  # él, piros
        if self.initiator.attrs['Det_Def'] == 'Indef':
            self.initiator.attrs['Det_Def'] = 'Def'
        ret = False, None
    else:  # Birtokos-dat-balra-kereső
        # A ballasztban adja át a szám személy alfeltételt...
        cond = {'main': 'Dat'}                      # XXX Fölösleges bonyolítás, mert most a Pers-t nem szorítjuk meg
        if 'subcond' in self.ballast:               # a pers_restrictor_search_fun függvénnyel a demo miatt...
            cond['subcond'] = self.ballast.subcond  # A végleges verzióban majd: {'main':'Dat', 'subcond': self.ballats.subcond}
        ret = True, [Searcher('Pers', cond, direction=['<'], border='||', max_words_in_direction=None, unique=True,
                              hit_function=pers_dat_left_hit_fun, ballast=self.ballast, initiator=self.initiator)]

    return ret


def pers_dat_left_hit_fun(self) -> (bool, [Searcher] or None):  # itt kell a Searcher-hez hozzáférés...  # If found
    if self.hit is not None and ('occupied' not in self.hit.attrs or self.name not in self.hit.attrs['occupied']):
        make_edge(self.initiator, self.hit, 'Red', 'Gen', 'Pers')  # él, piros
        ret = False, None
    else:  # Birtokos-dat-jobbra-kereső
        # A ballasztban adja át a szám személy alfeltételt...
        cond = {'main': 'Dat'}                      # XXX Fölösleges bonyolítás, mert mos a Pers-t nem szorítjuk meg
        if 'subcond' in self.ballast:               # a pers_restrictor_search_fun függvénnyel a demo miatt...
            cond['subcond'] = self.ballast.subcond  # A végleges verzióban majd: {'main':'Dat', 'subcond': self.ballats.subcond}
        ret = True, [Searcher('Pers', cond, direction=['>]', '>'], border='||', max_words_in_direction=None,
                              unique=True, hit_function=pers_dat_right_hit_fun, ballast=self.ballast,
                              initiator=self.initiator)]
    return ret


def pers_dat_right_hit_fun(self) -> (bool, [Searcher] or None):  # itt kell a Searcher-hez hozzáférés...  # If found
    if self.hit is not None and ('occupied' not in self.hit.attrs or self.name not in self.hit.attrs['occupied']):
        make_edge(self.initiator, self.hit, 'Red', 'Gen', 'Pers')  # él, piros
    else:  # Not found
        # Zéró birtokos névmás: jellemzőállítás Sg/Pl1-3 a ballasztból, él magára? (GÁBOR!), fekete
        set_feature(self.initiator, 'SgPl1_3', self.ballast['SgPl1_3'])
        make_edge(self.initiator, self.initiator, 'Black', 'Gen', 'Pers')  # él, fekete

    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def focus_restrictor_search_fun(tok: Token, *_) -> [Searcher]:
    # Ballasztba bekerül a PreVV unifikálással és átállítja a max_words_in_direction-et =0 ra...
    return [Searcher('Focus', {}, direction=None, border=None, max_words_in_direction=0, unique=None,
                     ballast={'PreVV': 'PreVV'}, initiator=tok)]


def focus_search_fun(tok: Token, *_) -> [Searcher]:
    # Ballasztba bekerül a PreVV unifikálással és átállítja a max_words_in_direction-et =0 ra...
    return [Searcher('Focus', {'main': '*'}, direction=['<'], border='||', max_words_in_direction=1, unique=True,
                     hit_function=focus_hit_fun, initiator=tok)]


def focus_hit_fun(self) -> (bool, [Searcher] or None):
    if 'PreVV' in self.ballast or self.hit is None:  # If not found or PreVV
        make_edge(self.initiator, self.initiator, 'Blue', 'Focus')  # él magára, kék
    else:
        make_edge(self.initiator, self.hit, 'Blue', 'Focus')  # ha talált: él, kék

    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def mod_search_fun(tok: Token, *_) -> [Searcher]:  # Nincs külső input!
    return [Searcher('MOD', {'main': {'MOD', 'Essmod'}}, direction=['<', '>'], border='||', max_words_in_direction=None,
                     unique=False, hit_function=mod_hit_fun, initiator=tok)]


def mod_hit_fun(self) -> (bool, [Searcher] or None):
    occupied = False
    hits = []
    if self.hit is not None:
        hits = []
        for i in self.hit:
            if 'occupied' not in i.attrs or self.name not in i.attrs['occupied']:
                hits.append(i)
    if self.hit is not None and not occupied:  # If not found, then do nothing
        for hit in hits:
            make_edge(self.initiator, hit, 'Red', 'MOD')  # él, piros

    return False, None

# ----------------------------------------------------------------------------------------------------------------------


# XXX ITT NEM JÓ, MERT A PERS NEM FŐKATEGÓRIA!
"""
A Pers nem főkategória hanem valami feature és bármilyen főkategóriával keres
de még keres a névutót is ami viszont főkategória!

A pont és a finit ige megállítja sikertelenül, de csak a névutókeresőt

Összefoglalva:
Nom elindítja a:
1) névutó kereső: Főkategória *, Alkategória: PostP, csak egy-et megy ha talált megöli a birtokos keresőt, ha nemtalált
 meghal.
Ha talált: (nom <- névutó él) Élcímke: névutó szótő. NP-ige közötti él az pedig HOL címkéjű és a névutóra mutat
2) birtokos kereső: Főkategória *, Alkategória: Pers, többet is megy ablak végégig
3) birtokos lelövő: {Főkategória: PUNCT, Főkategória: FIN} az ablak végéig megy, ha talált lelövi a birtokost,
 ha nem talált, akkor semmi
ha a birtokos talált előbb, akkor lelövi a birtokoslelövőt!

"""

"""
def postp_search_fun(tok: Token, *_) -> [Searcher]:
    return [Searcher('POSTP_SEARCH', {'main': '*', 'other': {'PostP'}}, direction=['>]'], border='||',
                     max_words_in_direction=1, unique=True, hit_function=postp_hit_fun, initiator=tok)]


def postp_hit_fun(self) -> (bool, [Searcher] or None):
    if self.hit is not None:  # If found
        self.initiator.main = self.hit.main  # a Nom-ot szerintívusszá...
        make_edge(self.hit, self.initiator, 'Black', self.hit.stem)  # él, fekete

    return False, None

def nom_or_gen_killer_search_fun(tok: Token, *_) -> [Searcher]:
    return [Searcher('PUNCT_OR_FIN_SEARCH', {'main': {'PUNCT', 'FIN'}}, direction=['>]'], border='||',
                     max_words_in_direction=None, unique=True, hit_function=nom_or_gen_killer_hit_fun, initiator=tok)]


def nom_or_gen_killer_hit_fun(self) -> (bool, [Searcher] or None):
    if self.hit is not None and 'NOM_OR_GEN' not in self.initiator.attrs:  # If found
        set_feature(self.initiator, 'NOM_OR_GEN', 'Nom')
        # return [Searcher('NOM_OR_GEN', {}, direction=['>]'], border='||', max_words_in_direction=0,  # Kill!
        #                 unique=True, hit_function=None, initiator=self.initiator)]

    return False, None

"""


def postp_search_fun(tok: Token, *_) -> [Searcher]:
    return [Searcher('POSTP_SEARCH', {'main': '0'}, direction=['<'], border='||',
                     max_words_in_direction=1, unique=True, hit_function=postp_hit_fun, initiator=tok)]


def postp_hit_fun(self) -> (bool, [Searcher] or None):
    if self.hit is not None:  # If found
        self.hit.main = self.initiator.main  # a Nom-ot szerintívusszá...
        make_edge(self.initiator, self.hit, 'Black', self.initiator.stem)  # él, fekete

    return False, None

# MACROS:


def macro_np_mod(annot):
    """
    defines if a token is an macro_np_mod or not
    :param annot: list of token, lemma, annotation.with.dots
    :return: true if it is an macro_np_mod, false otherwise
    """
    return re.search('MN|SZN|MIB|MIF|MIA|OKEP', annot)


def macro_nominal(annot):
    return re.search('FN|MN|SZN', annot)


# still incomplete:
nu_mn_list = {'alatti', 'általi', 'elleni', 'előli', 'előtti', 'felőli', 'fölötti', 'helyetti', 'iránti', 'képesti',
              'körüli', 'közötti', 'melletti', 'mellőli', 'miatti', 'mögötti', 'nélküli', 'szerinti', 'végetti',
              'utáni', 'közti'}


def macro_nu_mosaic(token, annot):
    return token in nu_mn_list or annot.endswith('[NU]') or token in {'című', 'nevű'}


def macro_conjunctionwords(token):
    # particles and friends
    return token in {'is', 'sem', 'nem', 'pedig'}


def macro_spunct(token, annot):
    return token in {'!', '?', '.'} or annot == '[PUNCT]'


def macro_nm(annot):
    return 'NM' in annot


def macro_words_can_never_be_gen(token):
    return token.title() in {'Mindez', 'Az', 'Ez', 'Ami', 'Aki'}  # Words can never be gen


def macro_a_az_det(token, annot):
    return token in {'a', 'az'} and annot.endswith('[DET]')


def macro_ige_not_van(lemma, annot):
    return 'IGE' in annot and 'van' != lemma and '_' not in annot  # [IGE][_MIB]


def macro_poss(annot):
    return 'PS' in annot


def macro_poss_sg(annot):
    return 'PSe' in annot


def macro_poss_sg3(annot):
    return 'PSe3' in annot


def macro_is_prev(annot):
    return annot == '[IK]'


def macro_is_propn(annot):
    return 'TULN'in annot


def macro_is_pl(annot):
    return 'PL' in annot


def macro_is_numeral(annot):
    return 'SZN' in annot


def macro_is_adv(annot):
    return 'HA' in annot


def macro_noun_or_pronoun(annot):
    return re.search('FN|DET_NM', annot)


def macro_ige(annot):
    return 'IGE' in annot


def macro_clause_starter(token):
    return token in {'ami', 'aki', 'hogy', 'de'}


# TODO: EZ egy ordas nagy hack és a szemenköpése az AnaGrammának, de remélhetőleg működik és nem veszi észre senki...
def nom_or_what_search_fun(tok: Token, *_) -> [Searcher]:
    curr_annot = tok.purepos_anal
    if tok.stem.title() in {'Mindez', 'Az', 'Ez', 'Ami', 'Aki'} or tok.purepos_anal.endswith('[PUNCT]'):
        # Always Nom! "macro_words_can_never_be_gen"
        tok.main = 'Nom'
        # Set Feature!
        print('feature', 'main', 'Nom', tok.index(), file=sys.stderr)
        return []
    # TULN, NPMod+PL, FN
    elif macro_noun_or_pronoun(curr_annot) or (macro_np_mod(curr_annot) and macro_is_pl(curr_annot)) or \
            macro_is_propn(curr_annot):  # MN + PL == FN + PL
        state = 'mn_fn_first_right'
    elif macro_is_numeral(tok.purepos_anal):
        state = 'numeral_first_right'
    elif macro_np_mod(tok.purepos_anal):
        state = 'npmod_first_right'
    else:
        raise Exception('Nom-or-What exception')

    # TODO: Itt kellne megírni a feltételeket nem a ballastban hackelni... De senkit sem érdekel...
    return [Searcher('NOM_OR_WHAT', {'main': '*'}, direction=['>]'], border='||',
                     max_words_in_direction=2, ballast={'state': state}, unique=True,
                     hit_function=nom_or_what_hit_fun, initiator=tok)]


def nom_or_what_hit_fun(self) -> (bool, [Searcher] or None):
    state = self.ballast['state']
    # TODO: Hack, mert nincs idő szakszerűen megírni még egy keresőkört, de azt kellene...
    if (self.hit.index() - self.initiator.index()) == 1:
        self.ballast = FeatStruct({'state': self.ballast['state'],
                                   'firstr_token': self.hit.tok,
                                   'firstr_lemma': self.hit.stem,
                                   'firstr_annot': self.hit.purepos_anal})
        self.ballast.freeze()
        self.direction = ['>]']
        return False, [self]

    firstr_token = self.ballast['firstr_token']
    firstr_lemma = self.ballast['firstr_lemma']
    firstr_annot = self.ballast['firstr_annot']
    secondr_token = self.hit.tok
    secondr_lemma = self.hit.stem
    secondr_annot = self.hit.purepos_anal

    if state == 'mn_fn_first_right':
        if macro_poss_sg(firstr_annot):
            self.initiator.main = 'Gen'
            # Set Feature!
            print('feature', 'main', 'Gen', self.initiator.index(), file=sys.stderr)
            return False, None
        elif macro_ige_not_van(firstr_lemma, firstr_annot) or macro_is_prev(firstr_annot) or \
                macro_is_propn(firstr_annot) or macro_is_pl(firstr_annot) or macro_a_az_det(firstr_token, firstr_annot) \
                or macro_conjunctionwords(firstr_token) or macro_spunct(firstr_token, firstr_annot) or \
                macro_nm(firstr_annot):  # before verbs, verbal particles, proper names and pronouns: nom;
            # disambed_pos_tag = 'nom'  # before article, is, sem, dot or comma: nomorkop
            self.initiator.main = 'Nom'
            # Set Feature!
            print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)
            #  this is a cheat: now only NOM
            # self.initiator.main = 'Gen'
            # Set Feature!
            # print('feature', 'main', 'Gen', self.initiator.index(), file=sys.stderr)
            return False, None  # Nem kell semmit csinálni, mert már Nom...

        elif macro_np_mod(firstr_annot):  # before macro_np_mod: nom or gen
            # TODO: Itt nem döntési fa, mert az initiator-t nem kérdezhetjük. De ez van a kódban.
            if not macro_poss_sg3(self.initiator.purepos_anal) \
                    and macro_poss(secondr_annot):
                # disambed_pos_tag = 'gen'  # TODO Ezt kiszedni innen...
                self.initiator.main = 'Gen'
                # Set Feature!
                print('feature', 'main', 'Gen', self.initiator.index(), file=sys.stderr)

            # connectives
            elif macro_poss_sg3(self.initiator.purepos_anal) \
                or macro_ige(secondr_annot) or macro_clause_starter(secondr_token) \
                or macro_spunct(secondr_token, secondr_annot):  # check the second in the window
                # disambed_pos_tag = 'nom'  # TODO Ezt kiszedni innen...
                self.initiator.main = 'Nom'
                # Set Feature!
                print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)

            else:
                # disambed_pos_tag = 'nulla'
                self.initiator.main = '0'
                # Set Feature!
                print('feature', 'main', '0', self.initiator.index(), file=sys.stderr)
        else:
            # connectives
            if macro_poss_sg3(self.initiator.purepos_anal):
                # or macro_ige(secondr_annot) or macro_clause_starter(secondr_token) or \
                # macro_spunct(secondr_token, secondr_annot):  # check the second in the window
                # disambed_pos_tag = 'nom'  # TODO Ezt kiszedni innen...
                self.initiator.main = 'Nom'
                # Set Feature!
                print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)

            else:
                self.initiator.main = '0'
                # Set Feature!
                print('feature', 'main', '0', self.initiator.index(), file=sys.stderr)
                # disambed_pos_tag = 'nulla'  # otherwise default, 'question mark in the table'

    elif state == 'numeral_first_right':
        if macro_nominal(firstr_annot) or macro_nu_mosaic(firstr_token, firstr_annot):
            # disambed_pos_tag = 'semmi'
            self.initiator.main = 'ΦΦ'  # Ez az eldöntött semmi...
            # Set Feature!
            print('feature', 'main', 'ΦΦ', self.initiator.index(), file=sys.stderr)

        elif macro_ige_not_van(firstr_lemma, firstr_annot) or macro_a_az_det(firstr_token, firstr_annot) or \
                macro_is_adv(firstr_annot):
            # disambed_pos_tag = 'nom'  # cheating
            self.initiator.main = 'Nom'
            # Set Feature!
            print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)

        else:
            # Φ a def semmi, így nem csinálunk semmit.
            pass  # disambed_pos_tag = 'defsemmi'  # default
    elif state == 'npmod_first_right':
        if macro_nu_mosaic(firstr_token, firstr_annot):
            # disambed_pos_tag = 'semmi'  # before postpositions, alatti-feletti and című-nevű: semmi
            self.initiator.main = 'ΦΦ'  # Ez az eldöntött semmi...
            # Set Feature!
            print('feature', 'main', 'ΦΦ', self.initiator.index(), file=sys.stderr)

        # if the next one is a verb: nom
        elif macro_ige_not_van(firstr_lemma, firstr_annot) or macro_a_az_det(firstr_token, firstr_annot) or \
                macro_conjunctionwords(firstr_token) or macro_spunct(firstr_token, firstr_annot) or macro_nm(
                firstr_annot):
            # disambed_pos_tag = 'nom'  # before article, is, sem, '.' or ',': nomorkop # this is a cheat: now only NOM
            self.initiator.main = 'Nom'
            # Set Feature!
            print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)

        elif macro_is_numeral(firstr_annot):  # before a num: nom or gen # disambed_pos_tag = 'nulla'
            if macro_poss_sg(secondr_annot):
                # disambed_pos_tag = 'gen'
                self.initiator.main = 'Gen'
                # Set Feature!
                print('feature', 'main', 'Gen', self.initiator.index(), file=sys.stderr)

            else:
                # disambed_pos_tag = 'nom'
                self.initiator.main = 'Nom'
                # Set Feature!
                print('feature', 'main', 'Nom', self.initiator.index(), file=sys.stderr)

        elif firstr_annot.endswith('.NOM'):  # otherwise default
            if macro_spunct(secondr_token, secondr_annot) or macro_ige_not_van(secondr_lemma, secondr_annot) or \
                    macro_conjunctionwords(secondr_token) or \
                    macro_spunct(secondr_token, secondr_annot) or macro_nm(secondr_annot) or \
                    macro_nu_mosaic(secondr_token, secondr_annot):
                # disambed_pos_tag = 'semmi'
                self.initiator.main = 'ΦΦ'  # Ez az eldöntött semmi...
                # Set Feature!
                print('feature', 'main', 'ΦΦ', self.initiator.index(), file=sys.stderr)
            else:
                # disambed_pos_tag = 'defsemmi'
                pass
        else:
            if macro_spunct(secondr_token, secondr_annot):
                # disambed_pos_tag = 'semmi'
                self.initiator.main = 'ΦΦ'  # Ez az eldöntött semmi...
                # Set Feature!
                print('feature', 'main', 'ΦΦ', self.initiator.index(), file=sys.stderr)

            else:
                # disambed_pos_tag = 'defsemmi'
                pass

    else:
        raise Exception('Nom-or-What exception')

    return False, None

# ----------------------------------------------------------------------------------------------------------------------


def verbarg_search_fun(tok: Token, cond, _) -> [Searcher]:
    # Innen jön fő és alfeltétel illetve majd unifikálódik vele a ballasztba a SgPl1_3 ha lesz ilyen...
    return [Searcher(cond['main'], cond, direction=['<', '>'], border='||', max_words_in_direction=None,
                     unique=True, hit_function=verbarg_hit_fun, ballast={}, initiator=tok)]


def verbarg_hit_fun(self) -> (bool, [Searcher] or None):
    # Ha a max_words_in_direction be van állítva, akkor vagy blokkolt Nom vagy Inf, amit előre megtaláltunk.
    # Ha a restrictor, ami a találatot hordozza nem unifikálódik a vonzatkerettel és fals módon találtuk, akkor
    # eleresztjük azaz blokkoltnak tekintjük a self.ballast['inf_restr'] hiánya miatt, amivel mindig tud unifikálódni a
    # semmi a restrictorban!
    # todo: Ezt amúgy a kereső osztályban kellene tárolni, hogy restrictor vagy nem és akkor két restrictor
    # todo tud unifikálódni restrictorrá és a nem restrictor + restrictor nem restrictorrá...
    if self.max_words_in_direction is None:  # Not blocked
        if self.hit is not None:  # If found
            label = self.condition['main']
            if self.condition['main'] == HOL:
                occup = 'HOL'
                label = self.hit.main
            elif self.condition['main'] == HOVA:
                occup = 'HOVA'
                label = self.hit.main
            else:
                occup = self.condition['main']
            make_edge(self.initiator, self.hit, 'Red', label, occup)  # él, piros
        elif len(self.direction) == 0:  # todo: A mondat végén nincs nem szól senki, hogy vége...
            if self.condition['main'] in {'Nom', 'Acc'}:
                # ha van jellemző a ballasztban: jellemzőállítás Sg/Pl1-3 él
                make_edge(self.initiator, self.initiator, 'Black', self.condition['main'])  # todo: Gábor ??
                if 'SgPl1_3' in self.ballast:
                    set_feature(self.initiator, 'SgPl1_3', self.ballast['SgPl1_3'])
                if 'Det_Def' in self.ballast:
                    set_feature(self.initiator, 'Det_Def', self.ballast['Det_Def'])
    elif self.hit is not None:
        make_edge(self.initiator, self.hit, 'Black', self.condition['main'])  # todo: Gábor ??

    return False, None


def vframe_nom_blocker_search_fun(tok: Token, *_) -> [Searcher]:
    # Nomletiltó: Időjárás igéknél és PART-oknál, INF-nél is...
    ps = UnifiableSet(Searcher('Nom', {'main': 'Nom'}, direction=['<'], border=None, max_words_in_direction=0,
                               unique=True, initiator=tok))
    return [Searcher('VFRAME', condition=None, direction=None, border=None, max_words_in_direction=None, unique=None,
                     ballast={'postponed-searchers': ps}, initiator=tok)]


def vframe_nom_acc_restrictor_search_fun(tok: Token, cond, ballast=None) -> [Searcher]:
    if ballast is None:
        ballast = {}
    # cond = {'main': 'Nom'/'Acc', 'subcond': {'SgPl1_3': ...}
    ps = UnifiableSet(Searcher(cond['main'], cond, direction=None, border=None, max_words_in_direction=None,
                               unique=None, ballast=ballast, initiator=tok))
    return [Searcher('VFRAME', condition=None, direction=None, border=None, max_words_in_direction=None, unique=None,
                     ballast={'postponed-searchers': ps}, initiator=tok)]


def vframe_direction_restrictor_search_fun(tok: Token, *_) -> [Searcher]:  # PART, GER
    # Megszorítja az irányát annak, amivel unifikálódik
    # A vonzatkeret nem ismert, de a vonzatkeret irányát szorítjuk meg ne ma VFrame irányát!
    return [Searcher('VFRAME', condition=None, direction=None, border=None,
                     max_words_in_direction=None, unique=None, ballast={'direction': ['<']},
                     initiator=tok)]


def vframe_starter_fun(tok: Token, cond, ballast):  # <----------------------- BEMENET
    if len({'?'} & set(ballast['restr_prev_inf'].values())) > 0:  # Ha az 'X' PreV-nek van ?-e akkor is ide megy!
        return left_inf_search_fun(tok, None, ballast)
    else:
        if cond is None:
            stems = set(ballast['restr_prev_inf'].keys()) - {'X'}  # Itt kivesszük az X-et a lehetséges PreV-k közül...
            cond = {'main': 'PreV', 'stem': stems}
        ballast['Inf'] = 'X'
        return right_infandprev_search_fun(tok, cond, ballast)


def left_inf_search_fun(tok: Token, _, ballast) -> [Searcher]:
    """
    PrevV				elad
    V	Prev			ad el
    Prev	FIN	Inf		el akarom adni
    PreV 	FIN	Inf	Inf	el fogom akarni adni
    PreV	FIN	Inf	Inf	el fogom adni akarni
    V	V	PreV		akarom adni el
    """
    # Ballasztban: van az igető, PreV és Inf viszonyok, Van a lehetséges PreV-k halmaza opcionálisan: iránymegszorító
    return [Searcher('VFRAME', {'main': 'Inf'}, direction=['<'], border='||', max_words_in_direction=None,
                     unique=True, hit_function=left_inf_hit_fun, ballast=ballast, initiator=tok)]


def right_infandprev_search_fun(tok: Token, cond, ballast) -> [Searcher]:
    # Jobb-mindkettő-kereső (a PreV sose üres, ha az Inf talált, akkor nem halmaz, egyébként halmaz)
    # Ballasztban: van az igető, PreV és Inf viszonyok, Van a lehetséges PreV-k halmaza opcionálisan: iránymegszorító
    # Ha talált, akkor Inf a ballasztban van!
    return [Searcher('VFRAME', cond, direction=['>]'], border='||', max_words_in_direction=None, unique=True,
                     hit_function=right_infandprev_hit_fun, ballast=ballast, initiator=tok)]


def left_prev_search_fun(tok: Token, _, ballast) -> [Searcher]:
    return [Searcher('VFRAME', {'main': 'PreV', 'stem': set(ballast['restr_prev_inf'].keys()) - {'X'}},
                     direction=['<'], border='||', max_words_in_direction=None, unique=True,
                     hit_function=left_prev_hit_fun, ballast=ballast, initiator=tok)]


def left_inf_hit_fun(self) -> (bool, [Searcher] or None):  # TODO: Itt nem ellenőrizzük, hogy nem zárja ki egymást a PreVV és az Inf!
    if self.hit is not None:  # If found Inf
        self.ballast['Inf'] = self.hit  # Inf ballasztba...  # PreV megszorítás
        self.ballast['PreV'] = {k for k, v in self.ballast['restr_prev_inf'].items() if v == '?' and k != 'X'}
    else:  # If Inf not found
        self.ballast = update_nested_frozen_fs(self.ballast,  # Az X-et kivesszük a PreV-kből
                                               {'PreV': set(self.ballast['restr_prev_inf'].keys()) - {'X'}})

    # Has PreVV (no search for 'PreV') or No PreV by Inf restriction
    if 'PreVV' in self.initiator.other or len(self.ballast['PreV']) == 0:
        self.ballast = update_nested_frozen_fs(self.ballast, {'PreV': 'X'})

    if self.ballast['PreV'] == 'X' and 'Inf' in self.ballast:  # PreV tisztázva és Inf talált
        ret = True, get_verb_frames(self.ballast, self.initiator)    # Got PreVV and Inf, done here!
    else:
        prev_cond = nested_frozen_fs({'main': 'PreV', 'stem': self.ballast['PreV']})
        if 'Inf' not in self.ballast and self.ballast['PreV'] != 'X':  # Inf OR PreV search
            next_cond = {self.condition, prev_cond}
        elif 'Inf' not in self.ballast:                                # Inf search (PreV = X)
            next_cond = self.condition
        else:                                                          # PreV search (Inf tisztázva)
            next_cond = prev_cond

        ret = True, right_infandprev_search_fun(self.initiator, next_cond, self.ballast)  # Get PreV or Inf
    return ret


def right_infandprev_hit_fun(self) -> (bool, [Searcher] or None):
    # TODO: Kereshetné az inf-et akkor is tovább jobbra, ha PreV-t talált...
    # Ha az Inf == X korábbról (mert az ige sehogy sem eszik Inf-et) vagy már találtunk és nem is kerestünk)
    # akkor Inf et nem is találhat és bele se megy abba az ágba! :)
    if self.hit is not None and 'PreV' in self.hit.main:  # If found and is PreV
        self.ballast = update_nested_frozen_fs(self.ballast, {'PreV': self.hit})  # PreV ballasztba
        if 'Inf' not in self.ballast:  # If Inf has not been found already
            # Itt nem érdekel minket a végeredmény igazából, mert úgyis a get_verb_frames fogja megoldani a dolgot!
            self.ballast = update_nested_frozen_fs(self.ballast,  # Inf megszorítás
                                                   {'Inf': self.ballast['restr_prev_inf'][self.ballast['PreV'].stem]})
        return True, get_verb_frames(self.ballast, self.initiator)  # vonzatkeret lehívás (searcher-ek halmaza)

    if self.hit is not None and self.hit.main == 'Inf':  # If found and is Inf
        self.ballast = update_nested_frozen_fs(self.ballast,
                                               {'Inf': self.hit,  # Inf ballasztba...
                                                'PreV': {k for k, v in self.ballast['restr_prev_inf'].items()
                                                         if v == '?' and k != 'X'}})  # PreV megszorítás
        if self.ballast['PreV'] == 'X':  # There is no Prev (No PreV is accepted) -> Done here! Get frames!
            return True, get_verb_frames(self.ballast, self.initiator)  # vonzatkeret lehívás (searcher-ek halmaza)

    # Ballaszt: Inf, ha van, PreV-Inf viszonyok, lehetséges (talált Inf-re megszorított) PreV-k, amit balra keresünk
    return True, left_prev_search_fun(self.initiator, None, self.ballast)


def left_prev_hit_fun(self) -> (bool, [Searcher] or None):
    if self.hit is not None:  # If found
        self.ballast['PreV'] = self.hit  # PreV ballasztba
        if 'Inf' not in self.ballast:
            # Itt nem érdekel minket a végeredmény igazából, mert úgyis a get_verb_frames fogja megoldani a dolgot!
            self.ballast = update_nested_frozen_fs(self.ballast,  # Inf megszorítás
                                                   {'Inf': self.ballast['restr_prev_inf'][self.ballast['PreV'].stem]})
    else:  # If not found
        self.ballast = update_nested_frozen_fs(self.ballast, {'PreV': 'X'})

    return True, get_verb_frames(self.ballast, self.initiator)  # vonzatkeret lehívás (searcher-ek halmaza)


# ----------------------------------------------------------------------------------------------------------------------


def lex_rules_fun(tok, _):
    """
    Ennek a függvénynek kell megmondania, hogy lexikálisan mi történik az adott szóval:
    pl:
    Igetőhöz hozzárendeli a lehetséges PreV és Inf kombinációit...  (ami majd segít a vonzatkeret lehívásban
    """
    ret = []

    # Vonzat keret lehúzás majd máshol lesz
    # Itt az igető megondja, hogy PreV, INF, PreV-XOR-INF, PreV-AND-INF, PreV-OR-INF
    verb_stem = tok.stem
    if 'PreVV' in tok.other and '|' in verb_stem:
        _, verb_stem = verb_stem.split('|')
        # TODO: HACK!
    if verb_stem.endswith(('#PartPast', '#PartPres', '#PartFut', '#Ger')):  # To handle other verb forms as well...
        verb_stem = verb_stem.split('#')[0] + '#V'

    prev_restrs = verb_prev_restrs_dict.get(verb_stem)
    if prev_restrs is not None:
        ret = vframe_starter_fun(tok, None, ballast={'verbstem': tok.stem, 'restr_prev_inf': prev_restrs})

    # Lexikális valamik...
    return tuple(ret)


def get_verb_frames(ballast, tok):
    # A főszereplők
    prev_tok = ballast.get('PreV', 'X')
    verb_stem = tok.stem.split('#')[0] + '#V'  # To handle other verb forms as well... ('#PartPast', '#PartPres')
    inf = ballast.get('Inf', '?')  # Mondunk-e valamit az Inf-ről ha semmit '?' Lehet explicit kimondva és implicit is!

    # Irány beállítása...
    direct = ballast.get('direction',  ['<', '>'])  # Volt-e Part iránymegszorító...

    # PreV változók beállítása élhúzáshoz és vonzatkeret lekérdezéshez
    if prev_tok != 'X':  # Ez azt jelenti, hogy PreV nincs (a PreVV más tészta)
        prev = prev_tok.stem  # Later we only need this
    elif 'PreVV' in tok.other and '|' in verb_stem:
        prev, verb_stem = verb_stem.split('|')
        prev_tok = tok
        prev = prev + '#PreV'  # Later we only need this
    else:
        prev = 'X'

    # Itt húzza be a PreV élt, fekete
    if prev_tok != 'X':
        make_edge(tok, prev_tok, 'Black', 'PreV')

    # Itt kedjük építeni a visszatérő keresők listáját
    ret = []

    # Ha voltak megszorítások, hozzáadjuk...
    if 'postponed-searchers' in ballast:
        ret.extend(ballast['postponed-searchers'])

    # Ha volt INF akkor hozzáadjuk...
    if inf not in {'X', '?'}:  # Ha Nincs infó vagy nicns Inf, akkor nincs él...
        # make_edge(tok, inf, 'Red', 'Inf')  # Itt húzza be az élt, piros
        # Inf megszorító, ami nem megy sehová, de az Inf keresővel unifikálódik és találtá válik...
        # Ha nem keresünk Inf-et, akkor blokkolt és meghal... elvileg...
        ret.append(Searcher('Inf', {'main': 'Inf'}, direction=direct, border='||', max_words_in_direction=0,
                            unique=True, hit_function=verbarg_hit_fun, ballast={}, initiator=tok, hit=inf))
        inf = '!'  # Meg is találtuk.

    # MMO magic, return [Searcher]
    frame = verb_frames.get((verb_stem, prev, inf))
    # Itt az a baj, hogy ha explicit meg akarjuk találni eddigre, akkor az miben különbözik az explicit megtaláltuk-tól?
    if frame is None and inf == '?':
        frame = verb_frames.get((verb_stem, prev, '?!'))  # TODO: Hack. Erre nincs jobb ötletem per pill.
    if frame is not None:
        for name, cond in frame:
            ret.append(Searcher(name, cond, direction=direct, border='||', max_words_in_direction=None, unique=True,
                                hit_function=verbarg_hit_fun, ballast={}, initiator=tok))

    ret = unify_till_pass(ret)  # Szedd össze magad! todo: hack

    # torlendo = [s for s in ret if s.direction is None]  # TODO: nem tárgyas igék pl egyeztet ACC megszorítója itt csendben elhullik
    # if torlendo:
    #    print("XXX", torlendo)
    ret = [s for s in ret if s.direction is not None]

    return ret
