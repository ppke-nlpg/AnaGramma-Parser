#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from re import escape

from engine.mosaic_engine import Mosaic

# TODO: Jelenleg a beírás sorrend szerinti első match-et nézi tovább, ha több is matchel, akkor a többiek így jártak...
# TODO: Szélességi keresést implementálni?

mosaic_list = [[('Polgár', '.*', '.*'),
                ('.*', 'Judit', escape('[FN]') + '.*')],

               [('Donald', '.*', '.*'),
                ('.*', 'Trump', escape('[FN]') + '.*')],

               [('Donald', '.*', '.*'),
                ('.*', 'kacsa', escape('[FN]') + '.*')],

               [('Pázmány', '.*', '.*'),
                ('.*', 'Péter', escape('[FN]') + '.*')],

               [('Pázmány', '.*', '.*'),
                ('Péter', '.*', '.*'),
                ('Katolikus', '.*', '.*'),
                ('.*', 'egyetem', escape('[FN]') + '.*')],

               [('Ferenc', '.*', '.*'),
                ('.*', 'pápa', escape('[FN]') + '.*')],

               [('.*', '.*', escape('[FN][SUP]')),
                ('.*', '(kívül|túl).*', '.*')],
               [('.*', '.*', escape('[FN][NOM]')),
                ('.*', '(című|nevű).*', '.*')],
               ]


if __name__ == '__main__':
    trie = Mosaic(mosaic_list)

    test_text2 = 'Polgár#Polgár#[FN][NOM] Judittal#Judit#[FN][INS] ment#megy#[IGE][Me3] Donald#Donald#[FN][NOM]' \
                 ' Trump#Trump#[FN][NOM] vacsorázni#vacsorázik#[IGE][INF] Donald#Donald#[FN][NOM]' \
                 ' Kacshoz.#kacs#[FN][All][PUNCT]'
    test_text = 'Pázmány#Pázmány#[FN][NOM] Péter#Péter#[FN][Nom] Katolikus#katolikus#[MN][NOM]' \
                ' püspökkel#püspök#[FN][INS] vacsorázott#vacsorázik#[IGE][Me3] a#a#[DET]' \
                ' Pázmány#Pázmány#[FN][NOM] Péter#Péter#[FN][Nom] Katolikus#katolikus#[MN][NOM]' \
                ' Egyetemen#egyetem#[FN][SUP] valaki.#valaki#[FN][NOM][PUNCT]'
    test_text3 = 'Pázmány#Pázmány#[FN][NOM] Péter#Péter#[FN][Nom] Katolikus#katolikus#[MN][NOM]' \
                 ' püspökön#püspök#[FN][SUP] kívüliek#kívüli#[MN][PL][NOM] a#a#[DET] Péteren#Péter#[FN][SUP]' \
                 ' túl#túl#[NU] Egyetemen#egyetem#[FN][SUP] valaki.#valaki#[FN][NOM][PUNCT]'
    test_text4 = 'korábbi#korábbi#TAG elnökjelöltnek.#korábbi#TAG2 Donald#Donald#[FN][NOM] Trump#Trump#[FN][Nom]' \
                 ' ment#megy#[IGE][Me3] Polgár#Polgár#[FN][NOM] Judittal#Judit#[FN][INS]' \
                 ' vacsorázni.#vacsorázik#[IGE][INF][Punct]'
    print(trie.merge_mosaic_tokens(test_text.split()))
    print(trie.merge_mosaic_tokens(test_text2.split()))
    print(trie.merge_mosaic_tokens(test_text3.split()))
    print(trie.merge_mosaic_tokens(test_text4.split()))