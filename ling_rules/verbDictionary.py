#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# TODO: A manócska gitrepo-ban van a megfelelő fájl... Úgyis meghal. Innen kiszedtem.
# from ling_rules.manocska.vframe_dict.vframe_dict import verb_prev_restrs_dict as manocska_prev_restrs

"""
Itt megmondjuk, hogy az ige (aminek jelezzük a szófaját a későbbi olvashatóság miatt pl. vár#V)
milyen igekötőket tud magával elképzelni és azokkal együtt lehet-e INF vonzata.

pl. a meg#PreV mellett a ? -azt jelenti, hogy lehet inf-je (de nem kötelező)
    az X pedig hogy nem lehet INF semmiképpen

Az üres dict {} azt jelenti, hogy nincs igekötője. (és INF-je sincs.)
Az X: '?' pedig azt jelenti, hogy igekötő nélkül lehet INF-je.
"""
# verb_prev_restrs_dict = manocska_prev_restrs  # TODO: ITT MEGHAL!
# """
verb_prev_restrs_dict = {
    'ajánl#V': {'meg#PreV': '?', 'be#PreV': '?', 'fel#PreV': 'X'},
    'fogad#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'be#PreV': 'X', 'fel#PreV': 'X'},
    'lép#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'fel#PreV': 'X'},
    'kap#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'fel#PreV': 'X'},
    'kezd#V': {'el#PreV': '?', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'X': '?'},
    'választ#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'szét#PreV': 'X'},
    'egyeztet#V': {'le#PreV': 'X'},
    'kritizál#V': {},
    'tart#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'szét#PreV': 'X', 'fel#PreV': 'X'},
    'nő#V': {'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'fel#PreV': 'X'},
    'támogat#V': {},
    'hibázik#V': {},
    'kapcsolódik#V': {'be#PreV': 'X'},
    'foglalkozik#V': {},
    'hoz#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'haza#PreV': 'X'},
    'tárgyal#V': {'meg#PreV': 'X'},
    'nevez#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X'},
    'vár#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'be#PreV': 'X'},
    'indul#V': {'el#PreV': '?', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X', 'X': '?'},
    'sújt#V': {'le#PreV': 'X'},
    'vesztegel#V': {},
    'vesz#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X'},
    'indít#V': {'el#PreV': 'X', 'meg#PreV': 'X', 'be#PreV': 'X'},
    'szeret#V': {'X': '?'},
    'beszél#V': {'meg#PreV': 'X', 'ki#PreV': 'X', 'be#PreV': 'X'},
    'következik#V': {},
    'megy#V': {'el#PreV': 'X'},
    'ugat#V': {},
    'utál#V': {},
    }
# """
HOVA = {'All', 'Sub'}
HOL = {'Sup', 'Ine'}

"""
Itt megmondjuk, hogy milyen frame-k jöhetnek az egyes igékhez,
 amiknek a VFrame már felderítette a PreV és INF viszonait.
 A szótár kulcsa egy hármas, mely (jelenleg) egyértelműen meghatározza az ige keretét:
    - Ige töve jelölve a szófajt (pl. vár#V)
    - A PreV töve jelölve a szófajt (pl. meg#PreV) vagy X ha nincs
    - Az INF viszonya: 
        - X = nincs,
        - ?! = lehet neki vagy meg is találtunk,
        - ! = találtunk (szükséges megtalálni eddigre)
 A szótár értéke egy lista, ami Tuple-okat tartalmaz, amik az egyes argumentumok.
 A Tuple-ok jelenleg két részből állnak a név és a keresési feltétel (main, subcond, other).
"""
verb_frames = {
    ('ajánl#V', 'X', '?!'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('Dat', {'main': 'Dat'})],
    ('ajánl#V', 'fel#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('Dat', {'main': 'Dat'}),
         ('szerint', {'main': 'PostP', 'stem': 'szerint#PostP'})],
    ('beszél#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Del', {'main': 'Del'}),
         ('HOL', {'main': HOL})],
    ('egyeztet#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Ins', {'main': 'Ins'})],
    ('fogad#V', 'el#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'})],
    ('lép#V', 'fel#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Cau', {'main': 'Cau'})],
    ('foglalkozik#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Ins', {'main': 'Ins'}),
         ('HOL', {'main': HOL})],
    ('hibázik#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}})],
    ('hoz#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('HOVA', {'main': HOVA})],
    ('indít#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('szerint', {'main': 'PostP', 'stem': 'szerint#PostP'})],
    ('indul#V', 'X', '?!'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('HOVA', {'main': HOVA})],
    ('kapcsolódik#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('HOVA', {'main': 'All'})],
    ('kap#V', 'meg#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'})],
    # Explicit van infünk... A képviselők kezdhetnek vagy a képviselők tárgyalni így a tárgyalni lesz!
    ('kezd#V', 'X', '!'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Inf', {'main': 'Inf'})],
    ('kritizál#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('alatt', {'main': 'PostP', 'stem': 'alatt#PostP'}),
         ('Acc', {'main': 'Acc'})],
    ('választ#V', 'meg#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}})],
    ('nevez#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'subcond': {'NOM_OR_GEN': {'?', 'Nom'}}, 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('Dat', {'main': 'Dat'})],
    ('nő#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('miatt', {'main': 'PostP', 'stem': 'miatt#PostP'})],
    ('sújt#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('által', {'main': 'PostP', 'stem': 'által#PostP'})],
    ('szeret#V', 'X', '?!'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'})],
    ('támogat#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Ins', {'main': 'Ins'}),
         ('Acc', {'main': 'Acc'})],
    ('tárgyal#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Del', {'main': 'Del'})],
    ('tart#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Dat', {'main': 'Dat'}),
         ('Acc', {'main': 'Acc'})],
    ('vár#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'subcond': {'NOM_OR_GEN': {'?', 'Nom'}}, 'other': {'N'}}),
         ('Acc', {'main': 'Acc'}),
         ('HOL', {'main': HOL})],
    ('vesztegel#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('HOL', {'main': HOL})],
    ('vesz#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc[rész]', {'main': 'Acc', 'stem': 'rész#N'}),
         ('HOL', {'main': HOL})],
    ('vesz#V', 'el#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}})],
    ('következik#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}})],
    ('megy#V', 'el#PreV', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Ill', {'main': 'Ill'})],
    ('ugat#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}})],
    ('utál#V', 'X', 'X'):
        [('Nom', {'main': 'Nom', 'other': {'N'}}),
         ('Acc', {'main': 'Acc'})],

}
