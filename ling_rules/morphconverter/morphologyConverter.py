#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import requests
import json

humor_tags = re.compile('\[[^[\]]+\]')

exceptional_anals = {'#': [['||:NYITO']]}

verb = {'[IGE][Te1]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mosom
        '[IGE][Te2]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Sg2_Pron+acc_SgPl3'),  # mosod
        '[IGE][Te3]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Sg3+acc_SgPl3'),  # mossa
        '[IGE][Tt1]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mossuk
        '[IGE][Tt2]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mossátok
        '[IGE][Tt3]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Pl3+acc_SgPl3'),  # mossák

        '[IGE][Ie1]': ('FIN', 'V+acc_Def+Dec+Pres+nom_Sg1_Pron+acc_SgPl2_Pron'),  # moslak
        '[IGE][e1]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mosok
        '[IGE][e2]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Sg2_Pron+acc_SgPl3'),  # mosol
        '[IGE][e3]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Sg3'),  # mos
        '[IGE][t1]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mosunk
        '[IGE][t2]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mostok
        '[IGE][t3]': ('FIN', 'V+acc_Indef+Dec+Pres+nom_Pl3'),  # mosnak

        '[IGE][TMe1]': ('FIN', 'V+acc_Def+Dec+Past+nom_Sg1_Pron+acc_SgPl3'),  # mostam
        '[IGE][TMe2]': ('FIN', 'V+acc_Def+Dec+Past+nom_Sg2_Pron+acc_SgPl3'),  # mostad
        '[IGE][TMe3]': ('FIN', 'V+acc_Def+Dec+Past+nom_Sg3+acc_SgPl3'),  # mosta
        '[IGE][TMt1]': ('FIN', 'V+acc_Def+Dec+Past+nom_Pl1_Pron+acc_SgPl3'),  # mostuk
        '[IGE][TMt2]': ('FIN', 'V+acc_Def+Dec+Past+nom_Pl2_Pron+acc_SgPl3'),  # mostátok
        '[IGE][TMt3]': ('FIN', 'V+acc_Def+Dec+Past+nom_Pl3+acc_SgPl3'),  # mosták

        '[IGE][IMe1]': ('FIN', 'V+acc_Def+Dec+Past+nom_Sg1_Pron+acc_SgPl2_Pron'),  # mostalak
        '[IGE][Me1]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Sg1_Pron+acc_SgPl3'),  # mostam
        '[IGE][Me2]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Sg2_Pron+acc_SgPl3'),  # mostál
        '[IGE][Me3]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Sg3'),  # mosott
        '[IGE][Mt1]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Pl1_Pron+acc_SgPl3'),  # mostunk
        '[IGE][Mt2]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Pl2_Pron+acc_SgPl3'),  # mostatok
        '[IGE][Mt3]': ('FIN', 'V+acc_Indef+Dec+Past+nom_Pl3'),  # mostak

        '[IGE][TFe1]': ('FIN', 'V+acc_Def+Con+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mosnám
        '[IGE][TFe2]': ('FIN', 'V+acc_Def+Con+Pres+nom_Sg2_Pron+acc_SgPl3'),  # mosnád
        '[IGE][TFe3]': ('FIN', 'V+acc_Def+Con+Pres+nom_Sg3+acc_SgPl3'),  # mosná
        '[IGE][TFt1]': ('FIN', 'V+acc_Def+Con+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mosnánk
        '[IGE][TFt2]': ('FIN', 'V+acc_Def+Con+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mosnátok
        '[IGE][TFt3]': ('FIN', 'V+acc_Def+Con+Pres+nom_Pl3+acc_SgPl3'),  # mosnák

        '[IGE][IFe1]': ('FIN', 'V+acc_Def+Con+Pres+nom_Sg1_Pron+acc_SgPl2_Pron'),  # mosnálak
        '[IGE][Fe1]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mosnék
        '[IGE][Fe2]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Sg2_Pron+acc_SgPl3'),  # mosnál
        '[IGE][Fe3]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Sg3'),  # mosna
        '[IGE][Ft1]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mosnánk
        '[IGE][Ft2]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mosnátok
        '[IGE][Ft3]': ('FIN', 'V+acc_Indef+Con+Pres+nom_Pl3'),  # mosnának

        '[IGE][TPe1]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mossam
        '[IGE][TPe2]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Sg2_Pron+acc_SgPl3'),  # mossad
        '[IGE][TPe3]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Sg3+acc_SgPl3'),  # mossa
        '[IGE][TPt1]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mossuk
        '[IGE][TPt2]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mossátok
        '[IGE][TPt3]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Pl3+acc_SgPl3'),  # mossák

        '[IGE][IPe1]': ('FIN', 'V+acc_Def+Imp+Pres+nom_Sg1_Pron+acc_SgPl2_Pron'),  # mossalak
        '[IGE][Pe1]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Sg1_Pron+acc_SgPl3'),  # mossak
        '[IGE][Pe2]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Sg2_Pron+acc_SgPl3'),  # moss, mossál
        '[IGE][Pe3]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Sg3'),  # mosson
        '[IGE][Pt1]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Pl1_Pron+acc_SgPl3'),  # mossunk
        '[IGE][Pt2]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Pl2_Pron+acc_SgPl3'),  # mossatok
        '[IGE][Pt3]': ('FIN', 'V+acc_Indef+Imp+Pres+nom_Pl3'),  # mossanak

        '[IGE][_HAT][Te1]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshat
        '[IGE][_HAT][Te2]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshatod
        '[IGE][_HAT][Te3]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Sg3+acc_SgPl3'),  # moshatja
        '[IGE][_HAT][Tt1]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshatjuk
        '[IGE][_HAT][Tt2]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshajtátok
        '[IGE][_HAT][Tt3]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Pl3+acc_SgPl3'),  # moshatják

        '[IGE][_HAT][Ie1]': ('FIN', 'V+acc_Def+Dec+Pres+Hat+nom_Sg1_Pron+acc_SgPl2_Pron'),  # moshatlak
        '[IGE][_HAT][e1]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshatok
        '[IGE][_HAT][e2]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshatsz
        '[IGE][_HAT][e3]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Sg3'),  # moshat
        '[IGE][_HAT][t1]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshatunk
        '[IGE][_HAT][t2]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshattok
        '[IGE][_HAT][t3]': ('FIN', 'V+acc_Indef+Dec+Pres+Hat+nom_Pl3'),  # moshatnak

        '[IGE][_HAT][TMe1]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshattam
        '[IGE][_HAT][TMe2]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshattad
        '[IGE][_HAT][TMe3]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Sg3+acc_SgPl3'),  # moshatta
        '[IGE][_HAT][TMt1]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshattuk
        '[IGE][_HAT][TMt2]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshatták
        '[IGE][_HAT][TMt3]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Pl3+acc_SgPl3'),  # moshatják

        '[IGE][_HAT][IMe1]': ('FIN', 'V+acc_Def+Dec+Past+Hat+nom_Sg1_Pron+acc_SgPl2_Pron'),  # moshattalak
        '[IGE][_HAT][Me1]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshattam
        '[IGE][_HAT][Me2]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshattál
        '[IGE][_HAT][Me3]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Sg3'),  # moshatott
        '[IGE][_HAT][Mt1]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshattunk
        '[IGE][_HAT][Mt2]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshattatok
        '[IGE][_HAT][Mt3]': ('FIN', 'V+acc_Indef+Dec+Past+Hat+nom_Pl3'),  # moshattak

        '[IGE][_HAT][TFe1]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshatnám
        '[IGE][_HAT][TFe2]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshatnád
        '[IGE][_HAT][TFe3]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Sg3+acc_SgPl3'),  # moshatná
        '[IGE][_HAT][TFt1]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshatnánk
        '[IGE][_HAT][TFt2]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshatnátok
        '[IGE][_HAT][TFt3]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Pl3+acc_SgPl3'),  # moshatnák

        '[IGE][_HAT][IFe1]': ('FIN', 'V+acc_Def+Con+Pres+Hat+nom_Sg1_Pron+acc_SgPl2_Pron'),  # moshatnálak
        '[IGE][_HAT][Fe1]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshatnék
        '[IGE][_HAT][Fe2]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshatnál
        '[IGE][_HAT][Fe3]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Sg3'),  # moshatna
        '[IGE][_HAT][Ft1]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshatnánk
        '[IGE][_HAT][Ft2]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshatnátok
        '[IGE][_HAT][Ft3]': ('FIN', 'V+acc_Indef+Con+Pres+Hat+nom_Pl3'),  # moshatnának

        '[IGE][_HAT][TPe1]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshassam
        '[IGE][_HAT][TPe2]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshassad, moshasd
        '[IGE][_HAT][TPe3]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Sg3+acc_SgPl3'),  # moshassa
        '[IGE][_HAT][TPt1]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshassuk
        '[IGE][_HAT][TPt2]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshassátok
        '[IGE][_HAT][TPt3]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Pl3+acc_SgPl3'),  # moshassák

        '[IGE][_HAT][IPe1]': ('FIN', 'V+acc_Def+Imp+Pres+Hat+nom_Sg1_Pron+acc_SgPl2_Pron'),  # moshassalak
        '[IGE][_HAT][Pe1]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Sg1_Pron+acc_SgPl3'),  # moshassak
        '[IGE][_HAT][Pe2]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Sg2_Pron+acc_SgPl3'),  # moshass, moshassál
        '[IGE][_HAT][Pe3]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Sg3'),  # moshasson
        '[IGE][_HAT][Pt1]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Pl1_Pron+acc_SgPl3'),  # moshassunk
        '[IGE][_HAT][Pt2]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Pl2_Pron+acc_SgPl3'),  # moshassatok
        '[IGE][_HAT][Pt3]': ('FIN', 'V+acc_Indef+Imp+Pres+Hat+nom_Pl3'),  # moshassanak

        '[IGE][INRe1]': ('Inf', 'V+nom_Sg1'),  # mosnom
        '[IGE][INRe2]': ('Inf', 'V+nom_Sg2'),  # mosnod
        '[IGE][INRe3]': ('Inf', 'V+nom_Sg3'),  # mosnia
        '[IGE][INRt1]': ('Inf', 'V+nom_Pl1'),  # mosnunk
        '[IGE][INRt2]': ('Inf', 'V+nom_Pl2'),  # mosnotok
        '[IGE][INRt3]': ('Inf', 'V+nom_Pl3'),  # mosniuk
        '[IGE][INF]': ('Inf', 'V'),  # mosni
        '[IGE][_HAT][INF]': ('Inf', 'V'),  # moshatni
        '[IGE][_HIN]': ('MOD', 'Ger+Ger'),  # mosva
        '[IGE][_HINN]': ('MOD', 'Ger+Ger'),  # mosván
        '[IGE][_HINST]': ('MOD', 'Ger+Ger'),    # hí
        '[IGE][_HIN=ttOn]': ('MOD', 'Ger+Ger')}    # mosottan

det = {'a': 'Det:a#Det+Def', 'az': 'Det:az#Det+Def', 'egy': 'Det:egy#Det+Indef'}

part = {'[_MIB]': '#PartPast',
        '[_MIA]': '#PartFut',
        '[_OKEP]': '#PartPres',
        '[_MIB_SUBJ]': '#PartPast',
        '[_IF=tA]': '#PartPast',
        '[_MIB_SUBJ=tA]': '#PartPast',
        '[_MIB_SUBJ=tA][PL]': '#PartPast+nom_Pl',
        '[_IF=tA][PL]': '#PartPast+nom_Pl',
        '[_IF=tA][PSe1]': '#PartPast+nom_Sg1',
        '[_IF=tA][PSe2]': '#PartPast+nom_Sg2',
        '[_IF=tA][PSe3]': '#PartPast+nom_Sg3',
        '[_IF=tA][PSt1]': '#PartPast+nom_Pl1',
        '[_IF=tA][PSt2]': '#PartPast+nom_Pl2',
        '[_IF=tA][PSt3]': '#PartPast+nom_Pl3',
        '[_OKEP][PL]': '#PartPres+nom_Pl',
        '[_MIB][PL]': '#PartPast+nom_Pl',
        '[_MIA][PL]': '#PartFut+nom_Pl'}

part_re = re.compile('|'.join(re.escape(k) for k in part))

# műveltető, gyakorító
other_verb = {'[_MUV]': ('#V', '+Caus'), '[_GYAK]': ('#V', '+Multi')}
other_verb_re = re.compile('|'.join(re.escape(k) for k in other_verb))

nominals_main_sub = {'FN': 'N',
                     'MN': 'Adj+macro_NPMod',
                     'SZN': 'Num+macro_NPMod',
                     'FN|NM': 'N+Pron',
                     'MN|NM': 'Adj+Pron',
                     'FN|NM|Rel': 'N+Rel+Pron',
                     'NU': 'PostP'}

poss = {'PSe1': 'pers_Sg1_Pron',  # cicám
        'PSe2': 'pers_Sg2_Pron',  # cicád
        'PSe3': 'pers_SgPl3',  # cicája
        'PSt1': 'pers_Pl1_Pron',  # cicánk
        'PSt2': 'pers_Pl2_Pron',  # cicátok
        'PSt3': 'pers_Sg3_Pron',  # cicájuk
        'PSe1i': 'pers_Sg1_Pron',  # cicáim
        'PSe2i': 'pers_Sg2_Pron',  # cicáid
        'PSe3i': 'pers_SgPl3',  # cicái
        'PSt1i': 'pers_Pl1_Pron',  # cicáink
        'PSt2i': 'pers_Pl2_Pron',  # cicáitok
        'PSt3i': 'pers_Sg3_Pron'}  # cicáik

cases = {'NOM': 'Φ',  # ember
         'ACC': 'Acc',  # embert
         'DAT': 'Dat',  # embernek
         'INS': 'Ins',  # emberrel
         'CAU': 'Cau',  # emberért
         'FAC': 'Fac',  # emberré
         'FOR': 'For',  # emberként
         'ESS': 'Ess',  # emberül
         '_ESSMOD': 'Essmod',  # fáradtan
         '_ESSMOD=0': 'Essmod',  # fáradtan
         '_ESSNUM': 'Essnum',  # hárman
         '_MUL': 'Mul',  # hárman
         'KEPPEN': 'Keppen',  # emberképpen
         'TEM': 'Tem',  # órakor
         'INE': 'Ine',  # emberben
         'SUP': 'Sup',  # emberen
         'ADE': 'Ade',  # embernél
         'INL': 'Inl',  # Győrött
         'ILL': 'Ill',  # emberbe
         'SUB': 'Sub',  # emberre
         'ALL': 'All',  # emberhez
         'TER': 'Ter',  # emberig
         'ELA': 'FROM+Ela',  # emberből
         'DEL': 'Del',  # emberről
         'ABL': 'Abl'}  # embertől
case_re = re.compile('|'.join(re.escape('[{0}]'.format(k)) for k in cases))

postp = ('képesti', 'szembeni', 'szemközti', 'alatti', 'általi', 'belüli', 'elleni',
         'előtti', 'feletti', 'fölötti', 'helyetti', 'iránti', 'körüli', 'körülötti',
         'közbeni', 'közötti', 'közti', 'kívüli', 'melletti', 'mellőli', 'miatti', 'mögötti',
         'nélküli', 'szerinti', 'utáni', 'végi', 'túli')

persnum = {'e1': 'Sg1_Pron', 'e2': 'Sg2_Pron', 'e3': 'Sg3_Pron', 't1': 'Pl1_Pron', 't2': 'Pl2_Pron', 't3': 'Pl3_Pron'}
persnum_re = re.compile('|'.join(re.escape('[{0}]'.format(k)) for k in persnum))

properNouns = {'bankszövetség', 'volánbusz'}


def humor_prev_splitter(word, lemma, tag):
    anals = json.loads(requests.get('http://XXX.TODO.hu/humor/dstem/' + word, auth=('USER', 'PASS')).text)[word]

    good_anals = [(lem, t, danal) for lem, t, danal in anals if lem == lemma and t == tag]

    if len(good_anals) > 0:
        prev = []
        notprev = []
        for _, _, danal in good_anals:
            danal = good_anals[0][2]

            if '[IK]+' in danal:
                ik = danal.split('[IK]+', maxsplit=1)[0]
                word = word.replace(ik, '')
                lemma = ik + '|' + lemma.replace(ik, '')
                tag = '[IK]' + tag.replace('[IK]', '')
                prev.append((word, lemma, tag))
            else:
                notprev.append((word, lemma, tag))

        if len(set(prev)) == 1 or len(prev) > len(notprev):
            word, lemma, tag = prev[0]

        elif len(prev) < len(notprev):
            word, lemma, tag = notprev[0]

        # else:
            # raise TypeError('VERB HUMOR ANAL ABMIGOUS PreV: {0}'.format(good_anals))

    # else:
    #    return word, lemma, tag
        # raise TypeError('NO ANAL word: {0}'.format(word))

    return word, lemma, tag


def morph_converter(word):

    # nyitójel
    if word in exceptional_anals:
        return exceptional_anals[word]

    # felbontjuk szóalakra, tőre, elemzésre
    word, lemma, tag = word.split('#')
    main = 'UNK'
    punct_feat = ''
    features = ''

    # ha _ van a szótőben, akkor splittelje
    # a wordöt is?
    if '_' in lemma:
        lemma = lemma.split('_')[-1]
        word = word.split('_')[-1]  # most '_'-nél splitteli, de lehet, hogy szóköz van

    # punct
    if tag.endswith('[PUNCT]'):
        punct_feat = '+PUNCT'
        tag = tag.rsplit('[PUNCT]', maxsplit=1)[0]

    '''
    SZAVAK ESETRAG NÉLKÜL, RÖGTÖN VISSZATÉR VMIVEL
    itt csak főjegy és szótő van
    a főjegy az a szófaj
    '''

    # egyszerű DET
    if tag == '[DET]':
        if lemma in det:
            # szolistabol kiszedi
            return '{0}{1}'.format(det[lemma], punct_feat)
        else:
            return 'Det:{0}#Det{1}'.format(lemma, punct_feat)

    elif tag == '[KOT]':
        # kötőszó (conjugation)
        main = 'Conj'
        lemma += '#Conj'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    elif tag == '[ISZ]':
        # indulatszó (interjection)
        main = 'Interj'
        lemma += '#Interj'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    elif tag == '[PREP]':
        # indulatszó (interjection)
        main = 'Prep'
        lemma += '#Prep'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    elif tag == '[X]':
        # ismeretlen szó
        main = 'UNK'
        lemma += '#UNK'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    elif tag == '[MSZ]':
        # mondatszó
        main = 'Sent'
        lemma += '#Sent'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    # egyszerű igekötő
    elif tag == '[IK]':
        main = 'PreV'
        lemma += '#PreV'
        return '{0}:{1}{2}'.format(main, lemma, punct_feat)

    '''
    SZAVAK ESETRAGGAL VAGY MÁS BONYOLULT ÜGYEKKEL
    a főjegy vagy az esetrag, vagy POS
    vannak még jegyek és derivált jegyek
    '''

    main_pos = ''
    superlat = ''
    # esetragok
    if any('[{0}]'.format(case) in tag for case in cases):
        case_tag = case_re.search(tag).group(0)[1:-1]
        main = cases[case_tag]

    if tag.startswith('[FF]'):
        superlat = '+SuperLative'
        tag = tag.replace('[FF]', '').replace('[_FOK]', '')
    elif '[_FOK]' in tag:
        superlat = '+Lative'
        tag = tag.replace('[_FOK]', '')

    # egyszerű névutó
    if tag == '[NU]':
        main = 'PostP'
        lemma += '#PostP+PostP'
        return '{0}:{1}{2}{3}'.format(main, lemma, superlat, punct_feat)

    # egyszerű MOD
    if tag.startswith('[HA'):
        if 'NM' in tag:
            return 'MOD:{0}#Adv+Pron{1}{2}'.format(lemma, superlat, punct_feat)
        else:
            return 'MOD:{0}#Adv{1}{2}'.format(lemma, superlat, punct_feat)

    if tag.startswith('[DET|NM]'):
        # determináns, névmás esetraggal
        if '[PL]' in tag:
            return '{0}:{1}#Det+Pron+Pl{2}{3}'.format(main, lemma, superlat, punct_feat)
        else:
            return '{0}:{1}#Det+Pron{2}{3}'.format(main, lemma, superlat, punct_feat)
    elif tag.startswith('[SZN|NM]'):
        # számnév, névmás esetraggal
        return '{0}:{1}#Num+Pron+Pl{2}{3}'.format(main, lemma, superlat, punct_feat)

    if tag == '[IGE]':
        return 'FIN:volna#V{0}'.format(punct_feat)

    # bonyolult ige
    if tag.startswith('[IGE]'):
        word, lemma, longtag = humor_prev_splitter(word, lemma, tag)
        prev = ''

        if tag in verb:
            main, features = verb[tag]

        if '[IK]' in longtag:
            if main == 'FIN':
                tag = longtag.replace('[IK]', '', 1)
                prev = '+PreVV+FOC'
            else:
                tag = longtag.replace('[IK]', '', 1)
                prev = '+PreVV'

        if any(participle in tag for participle in part):
            part_tag = part_re.search(tag).group(0)
            if '+' in part_tag:
                main_pos = part[part_tag].split('+')[0].strip('#')
                lemma += part[part_tag].split('+')[0]
                features += part_tag.split('+', maxsplit=1)[1]
                features += '+macro_NPMod'
            else:
                main_pos = part[part_tag].strip('#')
                lemma += part[part_tag]
                features += '+macro_NPMod'

        else:
            lemma += '#V'

        return '{0}:{1}{2}+{3}{4}{5}'.format(main, lemma,  prev, main_pos, features, punct_feat)

    # bonyolult névszó és névutó
    elif tag.startswith(('[FN', '[MN', '[SZN', '[NU')):
        other_pos = ''

        if tag.startswith('[NU'):
            main = 'PostP'
            lemma += '#PostP'
        else:
            # main tags fő szófaj és alszófaj
            split_pos = nominals_main_sub[tag[1:].split(']', 1)[0]]
            main_pos = split_pos.split('+')[0]
            if '+' in split_pos:
                other_pos += '+' + split_pos.split('+')[1]
            if lemma in postp:
                lemma += '#PostP+PostP+'
            else:
                lemma += '#' + main_pos + '+'

        # no PSe1 or does not contain i for PSe1i
        if any('[{0}]'.format(pers_num) in tag for pers_num in persnum):
            persnum_tag = persnum_re.search(tag).group(0)[1:-1]
            features += '+' + persnum[persnum_tag]

        elif any(plural in tag for plural in {'[PL]', 'i]'}):
            features += '+Pl'
        else:
            features += '+Sg'

        # propn
        if lemma[0].isupper() or lemma in properNouns:
            features += '+PropN'

        if '[PS' in tag:
            ind = tag.find('[PS')
            features += '+Pers+' + poss[tag[ind + 1:].split(']', maxsplit=1)[0]]

        return '{0}:{1}{2}{3}{4}{5}{6}'.format(main, lemma, main_pos, other_pos, features, superlat, punct_feat)

    else:
        print(word, lemma, tag)


def readtests():

    with open('anagramma_test.txt') as infile:
        tests = [line.strip() for line in infile]

    return tests


if __name__ == '__main__':

    test_list = readtests()

    with open('humor_to_anagramma2.txt', 'w') as outfile:
        counter = 0
        # print AnaGramma features for words
        for inp in test_list:
            pred_out = morph_converter(inp)
            counter += 1
            if counter % 1000 == 0:
                print(counter)
            print(inp, pred_out, file=outfile)
