#/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A szoftver licence: LGPL, amíg máshogy nem döntünk.
http://www.gnu.org/licenses/lgpl.html

Részben vagy egészben történő felhasználás esetén az alábbi cikket
kell meghivatkozni:
Prószéky Gábor, Indig Balázs, Miháltz Márton, Sass Bálint:
"Egy pszicholingvisztikai indíttatású számítógépes nyelvfeldolgozási modell felé"
X. Magyar Számítógépes Nyelvészeti Konferencia MSzNy. 2014. január 16-17 (2014).
"""

import sys
import os
import codecs
import re
import copy
from collections import OrderedDict, defaultdict
import socket
import pickle


# Modul include-ok

from humor_dummy import Humor
from pos_model import pickle_POS, init_POS
from pos_model import pickle_MGuesser, init_MGuesser


# Konstansok
LISTING = u"#FELS"
VERB_NO_PREVERB = u"#IKNIGE"
PREVERB = u"#IK"
POSS = u"#BIRTOK"
POS_TRESHOLD = 5  # A legjobb n változat a score alapján


# Szeparátorok
PSEP = ur" "  # pattern-ek szeparátor-karaktere
ISEP = u";"  # info-bejegyzések szeparátor-karaktere
LSTLEMMASEP = u"++"
MORPHSEP = u"+"
AT = u"@"  # pozíciót (=hányadik szó a mondatban) jelöli
TAB = u"\t"  # TABULÁTOR KARAKTER LITERÁLIS

# Osztályok


# Ez nem tud semmit a threadekről csak a mechanizmust végzi
class Tthreads:
    """
    A különféle futó szálakat tartja nyilván
    thread = név-hez rendelt { attr-value hash }
    """
    threads = {}

    def __init__(self):
        self.empty()

    def empty(self):
        self.threads = {}

    def exists(self, thread):
        return thread in self.threads

    def list(self):
        return self.threads.keys()

    def count(self):
        return len(self.threads)

    def delete(self, name):
        del self.threads[name]

    def print_one(self, name):
        printout(u" (" + name + u" ::", u"")
        for attr in sorted(self.threads[name].keys()):
            printout(u" (" + unicode(attr) + u"="
                           + unicode(self.threads[name][attr]) + u")", u"")
        printout(u")")

    def print_out(self):
        if self.threads.keys():
            printout(u" ** futó szálak =")
            for name in sorted(self.threads.keys()):
                printout(TAB, u"")  # újsor
                self.print_one(name)

    def start(self, name, attrs_ref):
        if name in self.threads:
            printout(u"HIBA: start( " + name +
                     u" ) MÁR VOLT ILYEN SZÁL: FELÜLÍROM!")
        self.threads[name] = attrs_ref
        printout(u" ** start( " + name + u" )")

    def stop(self, name):
        if name in self.threads:
            self.delete(name)  # XXX kéne nézni, hogy hány van!
            printout(u" ** stop( " + name + u" )")
        else:
            printout(u"HIBA: stop( " + name + u" ) NEM VOLT ILYEN SZÁL!")


# Ez nem tud semmit a participantokról csak a mechanizmust végzi
class Tpartics:
    """
    A különféle szereplőket és tulajdonságaikat tartja nyilván
    participant = van egy id-je ami a lista indexe
    és vannak tulajdonságai és értékei(= hash)
    """
    partics = []

    def __init__(self):
        self.empty()

    def empty(self):
        self.partics = []

    def length(self):
        return len(self.partics)

    def lasti(self, diff=0):
        return self.length() - 1 + diff

    def partic_print_out(self, ind):
        for (a, v) in sorted(self.partics[ind].iteritems()):
            printout(TAB + unicode(ind) + u" :: " + a + u" : " + unicode(v))

    def partics_print_out(self):
        if self.partics:
            printout(u" .. szereplők:")
            for i in range(0, self.length()):
                self.partic_print_out(i)
            printout(u" .. szereplők vége")

    """
    A szereplőt az épp aktuális mondatsorszámmal teszi el,
    amit majd a new _sentence() szentesít + tesz előkereshetővé
    partic egy dictionary, amiben kötelező elem az idx és az sidx!
    stack.stackitem_print_out-ot meghívja ezért van stack paramétere
    """
    def add_partic(self, partic, stack):
        if (self.length() > 0 and self.partics[-1][u"sidx"] == partic[u"sidx"]
                              and self.partics[-1][u"idx"] == partic[u"idx"]):
            self.partics[-1] = partic
            printout(u" ii szereplő már hozzáadva(pl '-jÁnAk'), felülírás:")
        else:
            self.partics.append(partic)
            printout(u" ii szereplő hozzáadása:")
        printout(u" ii szereplő adatai :: " + unicode(partic[u"sidx"])
                                      + "/" + unicode(partic[u"idx"]))
        stack.stackitem_print_out(partic[u"idx"])
        for (a, v) in sorted(partic.iteritems()):
            if (a != u"idx" and a != u"sidx"):
                printout(TAB + TAB + a + u" : " + unicode(v))


# Ez nem tud semmit a mondatokról csak a mechanizmust végzi
class Tsentences:
    """
    A mondatok végső stack állapotát tartja nyilván.
    Egy elem egy stack típus.
    """
    sentences = []

    def __init__(self):
        self.empty()

    def empty(self):
        self.sentences = []

    def length(self):
        return len(self.sentences)

    def lasti(self, diff=0):
        return self.length() - 1 + diff

    """
    Ez az aktuális mondat száma, ami MÉG nincs benne a listában!
    Az első indextől kezdődik!!!
    """
    def curr_sentence(self, diff=0):
        return self.length() + diff

    def sentence_print_out(self, ind):
        self.sentences[ind].stack_print_out()

    def sentences_print_out(self):
        if self.sentences:
            printout(u" .. mondatok:")
            # Az első indextől kezdődik!!!
            for i in range(1, self.length()):
                self.sentence_print_out(i)
            printout(u" .. mondatok vége")


# Ez nem tud semmit a stackbeli elemekről csak a mechanizmust végzi
# Az add _explicit() az egyedüli érdekes függvény
class Tstack:
    """
    (függőben lévő) elemek (pl.: NP) tárolására
    w => szó + i => infó róla + p => szülő indexe / undef
    p segítségével lehet fát építeni itt!
    már hozzávettük-e az aktuális tokent?
    ha igen, akkor csak a hozzá tartozó info
    egészülhet ki egy újabb feltétel teljesülése esetén
    -- ld.: add _explicit()
    """
    stack = []

    added = False
    new_elem = True

    def __init__(self):
        self.empty()

    def empty(self):
        self.stack = []
        self.new_elem = True
        self.added = False

    def length(self):
        return len(self.stack)

    def lasti(self, diff=0):
        return self.length() - 1 + diff

    def curr_elem(self, info):
        """
        A stack-en lévő lezárt v. lezáratlan utsó elem típusa mi
        XXX mire is jó ez? -- 2 dolgot kever össze...
        """
        return self.length() > 0 and re.search(info, self.stack[-1][u"i"])

    def stackitem_print_out(self, ind):
        elem = self.stack[ind]
        if u"p" in elem:
            if elem[u"p"] == set():
                parent = u""
            else:
                parent = u" [>"
                for i in elem[u"p"]:
                    parent += AT + unicode(i) + u", "
                parent = parent[:-2] + u"]"
            printout(TAB + unicode(ind) + u" :: " + elem[u"w"]
                                        + u" # " + elem["l"]
                                        + u" // " + elem["i"] + parent)

    def stack_print_out(self):
        if self.stack:
            printout(u" .. stack:")
            for i in range(0, self.length()):
                self.stackitem_print_out(i)
            printout(u" .. stack vége")

    def generate_elems(self):
        """
        A stack-ban lévő elemeket visszakereshessük úgy is,
        hogy típushoz ("infó"-hoz) index;
        egy típushoz több index is (lista) tartozhat
        """
        elems = defaultdict(list)
        for i in range(0, self.length()):
            # Csak a top-level elemeket nézi
            if self.stack[i][u"p"] == set():
                # A nemlétezőhöz kell hozzáadni először: default dict
                elems[self.stack[i][u"i"]].append(i)
        # Lezárjuk a defaultdict -et már nem lehet a nemlétezőhöz appendelni
        elems.default_factory = None
        return elems

    """
    Megjegyzés: Default argumentumnál így kell csinálni:
    f(arg=func()) # Ez az f konstrukciójának idejében kiértékeli az
    arg-ot és onnantól azt viszi tovább
    A helyeys megoldás:
    f(*_arg):
       arg= _arg or func() így mindig kiértékeli
    ITT MOST NINCS HASZNÁLVA, CSAK LEHETŐSÉGKÉNT MEGHAGYTAM.
    """
    def elems_print_out(self, *_elems):
        elems = _elems or self.generate_elems()
        if len(elems) > 0:
            printout(u" ** elemek:", u"")
            for elem in sorted(elems.keys()):
                printout(u" (" + elem + u")" + AT
                  + u",".join(map(lambda x: unicode(x), elems[elem])), u"")
            printout(u"")  # újsor

    # egy stack-beli elemhez hozzáad egy szót (+ infót)
    def add_explicit(self, word, lemm, info=u'', _parent=set()):
        parent = _parent.copy()
        if not self.added:
            if self.new_elem:
                self.new_elem = False
                self.stack.append({u"w": word,
                                   u"l": lemm,
                                   u"i": info,
                                   u"p": parent})
            else:
                """
                Updateli a parenteket brute-force módon
                XXX Ez csúnya megoldás, nem akarom a kódot sem szépíteni.
                XXX HACK a névutó miatt
                """
                if not re.search(u"mellett|közé", lemm):
                    for i in range(0, self.length() - 1):
                        if self.lasti() in self.stack[i][u"p"]:
                            self.stack[i][u"p"].remove(self.lasti())
                            self.stack[i][u"p"].add(self.lasti(2))  # lasti + 2

                # Hozzáadja a szót
                self.stack.append({u"w": word,
                                   u"l": lemm,
                                   u"i": info,
                                   u"p": parent})
                if info:
                    info_new = info  # felülír, ha van új!
                else:
                    info_new = self.stack[-2][u"i"]
                if parent:
                    parent_new = parent.copy()  # felülír, ha van új!
                else:
                    parent_new = self.stack[-2][u"p"].copy()
                # XXX HACK a névutó miatt
                if re.search(u"mellett|közé", lemm):
                    lemm = self.stack[-2][u"l"]
                self.stack.append({u"w": self.stack[-2][u"w"] + u" "
                                       + self.stack[-1][u"w"],  # hozzátesz
                                   u"l": lemm,  # mindig az utsó!
                                   u"i": info_new,
                                   u"p": parent_new})
                self.stack[-2][u"p"].add(self.lasti())
                self.stack[-3][u"p"].add(self.lasti())
                """
                Névutóknál persze nem: megoldva! :)
                ha már hozzá van adva, akkor csak az infó egészül ki
                ugyebár ilyenkor egy 2. feltétel is teljesül a szóra
                """
        else:
            if info:
                self.stack[-1][u"i"] += ISEP + info

        # megjegyezzük, hogy ezt a tokent már hozzáadtuk
        self.added = True


class pilotParser:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments

        """
        Ez a "deepcopy"-hoz kell.
        Mivel MatchObjecteket nem lehet deepcopy-zni:
        http://bugs.python.org/issue416670
        """

        if len(args) >0 and len(kwargs) >0:
            printout(u"ParserInit: Ilyet nem lehet csinálni!")
            sys.exit(1)

        if len(args) >0:
            silent = args[0]
            stack_start = Tstack()
            threads_start = Tthreads()
            partics_start = Tpartics()
            sentences_start = Tsentences()
        else:
            silent = False
            stack_start = kwargs[u"parserState"][u"stack"]
            threads_start = kwargs[u"parserState"][u"threads"]
            partics_start = kwargs[u"parserState"][u"partics"]
            sentences_start = kwargs[u"parserState"][u"sentences"]

        # Globalok

        """
        (függőben lévő) elemek (pl.: NP) tárolására
        w => szó + i => infó róla + p => szülő indexe / undef
        p segítségével lehet fát építeni itt!
        stack index
        """
        self.stack = stack_start

        """
        a különféle futó szálakat tartja nyilván
        thread = név-hez rendelt { attr-value hash }

        A threads lehetséges elemei:
        THREAD_TYPE = enum(LISTING=u"#FELS",
                   VERB_NO_PREVERB=u"#IKNIGE",
                   PREVERB=u"#IK",
                   POSS=u"#BIRTOK")

        Részletesen (vázlatosan):
        LISTING = u"#FELS"
            A listingnek van neve ami fent látható.
            Van neki POS-ja ami egy index
            és van neki PTN(pattern) je ami a stacknek az infoja, ami string

        VERB_NO_PREVERB = u"#IKNIGE"
        Ennek egy eleme van: az ige ami a lemma és egy pos

        PREVERB = u"#IK"
        pos és az ik lemmája

        POSS = u"#BIRTOK"
        ennek csak pos ja van
        """
        self.threads = threads_start

        """
        Ez az osztály tartatja nyilván a szereplőket
        Az stack-index(idx) és a mondat-index(sidx)-en, ami kötelező.
        Semmit nem tud a belsejéről.
        """
        self.partics = partics_start

        """
        Ez az osztály tartatja nyilván a végleges mondat stackeket
        semmit nem tud a belsejéről.
        """
        self.sentences = sentences_start

        """
        JELENLEG TÖBB MINTÁRA IS MATCHELHET EGYSZERRE:
        A TAGEK KOMBINÁCIÓJA MIATT!!
        EZ TUDNA MŰKÖDNI AZZAL IS? NEM. ÉRDEKTELEN AZ ALÁBBI!
        NEM: Csak a szöveget tudja visszaadni.
        A group ot úgy adja vissza, hogy mindegyik, max None az értéke.

        Ezt lehetne gyorsítani majd:

        Named groups-al vagyolva megmondja melyik groupra matchelt.

            for regex, type in rules:
                groupname = 'GROUP%s' % i dx
                regex_parts.append('(?P<%s>%s)' % (groupname, regex))
                self.group_type[groupname] = type
                i dx += 1

            self.regex = re.compile('|'.join(regex_parts))

        Ezek után:

         m = self.regex.match(self.buf, self.pos)
                if m:
                    groupname = m.lastgroup
                    tok_type = self.group_type[groupname]

        Ötlet forrása: http://eli.thegreenplace.net/2013/06/25/regex-based-lexical-analysis-in-python-and-javascript/
        """
        self.ELEMEK = OrderedDict([
                    (re.compile(u"^\.#\.#\[PUNCT\]$"), self.dot_PUNCT),
                    (re.compile(u"^;#;#\[PUNCT\]$"), self.semicolon_PUNCT),
                    (re.compile(u"^,#,#\[PUNCT\]$"), self.comma_PUNCT),
                    (re.compile(u"^[^#]+#amely#[^#]+$"), self._amely_),
                    (re.compile(u"^[^#]+#az?#\[DET\]$"), self._aUaz_DET),
                    (re.compile(u"^[^#]+#egy#\[DET\]$"), self._egy_DET),
                    (re.compile(u"^[^#]+#[^#]+#[^#]+\[PSe3i?\][^#]*$"), self.__PSe3),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[MN\][^#]*\[NOM\][^#]*$"), self.__MN_NOM),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[SZN\][^#]*\[NOM\][^#]*$"), self.__SZN_NOM),
                    (re.compile(u"^[^#]+#[^#]+#[^#]+\[_MIB\][^#]*\[NOM\][^#]*$"), self.__MIB_NOM),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[FN\][^#]*\[NOM\][^#]*$"), self.__FN_NOM),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[FN\][^#]*\[DAT\][^#]*$"), self.__FN_DAT),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*(\[FN\]|\[FN\|NM\])[^#]*\[(ACC|DEL|INE|SUP)\][^#]*$"), self.__FNcase),
                    (re.compile(u"^[^#]+#[^#]+#[^#]+\[PSe3i?\][^#]*(\[(NOM|DAT|ACC|DEL|INE|SUP|INS|SUB|TER|ELA)\])?[^#]*$"), self.__birtok),
                    (re.compile(u"^[^#]+#(?:mellett|közé)#\[NU\]$"), self._mellettUkoze_NU),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[IGE\]\[(TM?)?e3\][^#]*$"), self.__IGEe3ATATMe3),
                    (re.compile(u"^[^#]+#[^#]+#\[IK\]$"), self.__IK),
                    (re.compile(u"^[^#]+#[^#]+#[^#]*\[HA\][^#]*$"), self.__HA),
                    (re.compile(u"^[^#]+#és#[^#]*\[KOT\][^#]*$"), self._es_KOT),
                    (re.compile(u"^[^#]+#mert#[^#]*\[KOT\][^#]*$"), self._mert_KOT),
                 ])

        if len(args) >0:
            self.new_sentence(silent)

    # deepcopy helyett (lásd feljtebb)
    def parserState(self):
        return {u"stack" : copy.deepcopy(self.stack),
                 u"threads" : copy.deepcopy(self.threads),
                 u"partics" : copy.deepcopy(self.partics),
                 u"sentences" : copy.deepcopy(self.sentences)
                }

# Actionok

    # mondat végi pont
    def dot_PUNCT(self, w, l, t):
        printout(u" !! mondat végi pont => minden lezárása + eredmény")
        self.end()
        self.evaluate_sentence()
        return True

    # XXX a ;-t egyelőre "mondat végi pont"-nak vesszük
    def semicolon_PUNCT(self, w, l, t):
        printout(u" !! \"mondat végi ;\" => minden lezárása + eredmény")
        self.end()
        self.evaluate_sentence()
        return True

    """
    vessző
    tagmondat vége VAGY felsorolás VAGY közbeszúrás VAGY értelmező
     -- lehet más is? XXX
    """
    def comma_PUNCT(self, w, l, t):
        self.end()
        printout(u" !! vessző -> eddigi elemet lezár")

        # ha már eddig is van egy 'és'-végű fels, akkor azt lezárjuk!
        if self.threads.exists(LISTING) and re.search(u"és" + PSEP + u"[^ ]+$",
                                        self.threads.threads[LISTING][u"ptn"]):
            printout(u" !! van 'és'-végű futó " + LISTING +
                     u"? -> akkor lezárjuk")
            self.close_listing()
            self.end()
            self.stack.added = False

        self.stack.add_explicit(w, l, u"vessző")
        printout(u" !! tagmondat vége? " + LISTING +
                 u"? közbeszúrás? értelmező?")
        # Lehet, hogy több felsorolás van. Jelenleg még csak hibát adunk rá.
        if not self.threads.exists(LISTING):
            self.threads.start(LISTING, {u"pos": self.stack.lasti(-1),
                                    u"ptn": self.stack.stack[-1][u"i"]})
        else:
            printout(u" !! Nem kezdünk új felsorolást, mert már fut egy szál.")
        """
        tudni illik a vessző előtti elemnél kezdődik, ami ugye
        a legnagyobb összerakott elem (top-level), amiről szó lehet
        lezárjuk, önálló elem
        """
        self.end()

        return True

    # 'amely' -> vonatkozó nm
    def _amely_(self, w, l, t):
        printout(u" !! vonatkozó nm -> tagmondat vége volt!")
        if self.stack.curr_elem(u"vessző"):
            printout(u" !! van vessző, oké.")
            """
            XXX ez tuti ilyenkor? MELYIK fels-t zárjuk???
            egyelőre feltettük, hogy csak 1 van
            """
            self.threads.stop(LISTING)
            printout(u" !! thread " + LISTING + u": CANCEL (mert nem is "
                                    + LISTING + u")")

            """
            A vesszőt (utsó elem) töröljük
            Eltároljuk, hogy mire vonatk, ez kelleni fog!
            Egyelőre egyszerűen: az utsó elem,
            ami a legnagyobb összerakott dolog
            Végül elkezdünk egy új mondatot
            -- tudva, hogy az utsó NP-t fejtjük ki!!!
            XXX amely helyett betesszük ua. raggal a megjegyzett lemmát
            izé, nem tuti, hogy új mondat, meglátjuk...
            XXX a vonatkozó névmás alakjának megfelelően
            az 'amely' alak esete miatt. általánosítani!
            """
            self.stack.stack.pop()
            vonatk = self.stack.stack[-1]
            self.evaluate_sentence()
            self.stack.add_explicit(u"l=" + vonatk[u"l"],
                                            vonatk[u"l"],
                                            u"fnNOM")
        else:
            printout(u" ?? nincs vessző, mit tegyünk?")
            self.new_sentence()  # új mondat

        return True

    # a-az-névelő
    def _aUaz_DET(self, w, l, t):
        printout(u" !! a-az-névelő => eddigi elemet lezárjuk.")
        self.end()
        printout(u" !! a-az-névelő = új NP eleje.")
        self.stack.add_explicit(w, l, u"a-az-névelő")

        return True

    # egy-névelő
    def _egy_DET(self, w, l, t):
        printout(u" !! egy-névelő => eddigi elemet lezárjuk.")
        self.end()
        printout(u" !! egy-névelő = új NP eleje.")
        self.stack.add_explicit(w, l, u"egy-névelő")

        return True

    # birtok lásd a birtok(..) fgv-nél
    def __PSe3(self, w, l, t):
        printout(u" !! birtok -> új egység (ha nem névelő|sima-jelzo volt),")
        printout(u" !! aztán majd megkeressük a birtokost")
        # XXX ha nem névelő|sima-* volt, akkor új elem; kül hozzácsapjuk

        if (not self.stack.curr_elem(u"névelő") and
           not self.stack.curr_elem(u"sima-")):
            self.end()

        """
        'az asztalról | könyveit elvette' -> ekkor NEM kell hozzá! XXX
        lehet, hogy birtokváró thread kellene fnNOM/fnDAT esetén? XXX
        """
        self.stack.add_explicit(w, l, u"birtok")

        self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                            u"idx": self.stack.lasti()}, self.stack)
        # külön zárjuk le alább (ld. hekk) XXX
        self.threads.start(POSS, {u"pos": self.stack.lasti()})

        return True

    # mnNOM
    def __MN_NOM(self, w, l, t):
        printout(u" !! sima mn: jelző? NP-fej? állítmány?")

        if self.stack.curr_elem(u"névelő") or self.stack.curr_elem(u"sima-"):
            printout(u" !! névelő|sima-jelzo volt, mehet hozzá")
            self.stack.add_explicit(w, l, u"sima-mn")
        else:
            printout(u" ?? nem névelő volt;jelző? NP-fej? állítmány? mit tegyünk?")
            printout(u" -> tipp: kezdjünk új elemet, aztán meglátjuk")
            self.end()
            self.stack.add_explicit(w, l, u"sima-mn-tán-nem-jelző")
            """
            XXX lehetne azt, h ha a KÖVETŐ token birtok (mindig határozott),
            akkor úgy csinálunk, mintha lett volna a-az-névelő
            XXX ha NP-fej, akkor add_partic kellene
            """

        return True

    # sznNOM -- mnNOM egy az egyben koppintva! XXX
    def __SZN_NOM(self, w, l, t):
        printout(u" !! sima szn: jelző? NP-fej? állítmány?")
        if self.stack.curr_elem(u"névelő") or self.stack.curr_elem(u"sima-"):
            printout(u" !! névelő|sima-jelzo volt, mehet hozzá")
            self.stack.add_explicit(w, l, u"sima-szn")
        else:
            printout(u" ?? nem névelő volt;jelző? NP-fej? állítmány? mit tegyünk?")
            printout(u" -> tipp: kezdjünk új elemet, aztán meglátjuk")
            self.end()
            self.stack.add_explicit(w, l, u"sima-szn-tán-nem-jelző")
            """
            XXX lehetne azt, h ha a KÖVETŐ token birtok (mindig határozott),
            akkor úgy csinálunk, mintha lett volna a-az-névelő
            XXX ha NP-fej, akkor add_partic kellene
            """

        return True

    # bef-mniNOM -- mnNOM egy az egyben koppintva! XXX
    def __MIB_NOM(self, w, l, t):
        printout(u" !! sima bef-mni: jelző? NP-fej? állítmány?")
        if self.stack.curr_elem(u"névelő") or self.stack.curr_elem(u"sima-"):
            printout(u" !! névelő|sima-jelzo volt, mehet hozzá")
            self.stack.add_explicit(w, l, u"sima-bef-mni")
        else:
            printout(u" ?? nem névelő volt;jelző? NP-fej? állítmány? mit tegyünk?")
            printout(u" -> tipp: kezdjünk új elemet, aztán meglátjuk")
            self.end()
            self.stack.add_explicit(w, l, u"sima-bef-mni-tán-nem-jelző")
            """
            XXX lehetne azt, h ha a KÖVETŐ token birtok (mindig határozott),
            akkor úgy csinálunk, mintha lett volna a-az-névelő
            XXX ha NP-fej, akkor add_partic kellene
            """

        return True

    # fnNOM
    def __FN_NOM(self, w, l, t):
        printout(u" !! NOM fn: alany? birtokos? névutó?")
        # XXX nyilván nem mindig jó: "az asztalra könyv kerül"
        self.stack.add_explicit(w, l, u"fnNOM")
        self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                            u"idx": self.stack.lasti()}, self.stack)

        return True

    # fnDAT
    def __FN_DAT(self, w, l, t):
        printout(u" !! DAT fn: birtokos? vonzat? részeshat? (NP-hez hozzá)")
        # XXX nyilván nem mindig jó: "Józsi Pistinek"
        self.stack.add_explicit(w, l, u"fnDAT")
        self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                            u"idx": self.stack.lasti()}, self.stack)

        return True

    # fnCASE (nem NOM és DAT) = egyéb esetek
    def __FNcase(self, w, l, t):
        case = re.sub(u"[^#]*(\[FN\]|\[FN\|NM\])[^#]*\[(ACC|DEL|INE|SUP)\][^#]*", u"\g<2>", t)
        """
        XXX itt nagyon kell a 'róla' típus [FN|NM][DEL][e3] kezelése,
        azaz, hogy megjegyezzük, hogy vmi korábbi e3-ról van szó!
        XXX ha az előző egy NOM-os ("birtokosra/névutóra váró") NP,
        akkor azt lezárjuk!
        XXX 'szó róla' -- a 'róla' lehetne a 'szó' vonzata???
        de ezt ne csináljuk (asszem), legyen inkább az igéé mindig!
        Erre valók  az igei vonzatkeretek szerintem.
        """
        printout(u" !! " + case + u" fn: NP vége / lehet utána mni pl.!")
        if self.stack.curr_elem(u"fnNOM"):
            printout(u" !! előző: fnNOM, úh azt lezárjuk.")
            self.end()

        self.stack.add_explicit(w, l, u"fn" + case)
        self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                            u"idx": self.stack.lasti()}, self.stack)
        """
        end # mert esetragos volt (és nem NOM, DAT)
        XXX asszem mégse kell, mert majd a névelő lezárja!
        hé, de nem lenne jó, ha mégis lezárnánk?
        """

        return True

    # névutó
    def _mellettUkoze_NU(self, w, l, t):
        printout(u" !! névutó -- előtte/utána lezár")
        printout(u" !! a névutó le tud zárni felsorolást (?!) [még mit tud? XXX]")
        """
        A névutó le tud zárni felsorolást, pl.: 'a, b és c mellett'
        névutó mindenképp zárja le az előzőt
        (aztán majd külön lépésben hozzávesszük a névutót)
        """
        self.end()

        """
        NU által kiváltott FELS-lezárás
        Megcsinálja a felsorolás elemet a stackben
        és ezért kell hackelni lentebb
        """
        if self.threads.exists(LISTING):  # többivel nem törődünk
            self.close_listing()
            self.end()        # Önálló elemet képzett
            self.stack.added = False  # és még nem raktuk bele az aktuális szót

        """
        Végül hozzá a NU-t, NU-nál megmarad az "előző" lemma
        + nem változtat az előző elemek függőségi viszonyain
        -> Ezért kell a hack az add_explicitben
        """
        self.stack.new_elem = False
        self.stack.add_explicit(w, l, u"névutó:" + l)
        self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                            u"idx": self.stack.lasti()}, self.stack)
        self.end()

        return True

    """
    A = halmaz-metszet/logikai-és jel
    IGE:e3 IGE:Te3 IGE:TMe3
    """
    def __IGEe3ATATMe3(self, w, l, t):
        printout(u" !! ige => eddigi elemet lezárjuk.")
        self.end()

        # tagadás vizsgálata
        if (self.stack.length() >= 1 and
            re.search(u"tagadószó", self.stack.stack[-1][u"i"])):
            tagadas_print = u"\nTAGADÁS!!!"
            # * plusz infó ~ új elem
            tagadas_info = ISEP + u"tagadott"  # jegy: "tagadott ige"
            # * parent
            self.stack.stack[-1][u"p"].add(self.stack.lasti(1))  # lasti + 1
            # XXX alárendeljük a tagadószót az ige alá!!!
        else:
            tagadas_print = u""
            tagadas_info  = u""

        # IGE:e3
        if t.find(u"[IGE][e3]") > -1:
            printout(u" !! ige -- alany:e3" + tagadas_print)
            self.stack.add_explicit(w, l, u"ige:e3" + tagadas_info)

        # IGE:Te3
        if t.find(u"[IGE][Te3]") > -1:
            printout(u" !! ige -- alany:e3 -- TÁRGYAS!" + tagadas_print)
            """
            XXX itt nagyon kell egy (ismeretlen) e3 tárgy felvétele,
            amit aztán lehet egyeztetni (unifikálni) vmivel
            """
            self.stack.add_explicit(w, l, u"ige:Te3" + tagadas_info)

        # IGE:TMe3
        if t.find(u"[IGE][TMe3]") > -1:
            printout(u" !! ige -- alany:e3 -- TÁRGYAS!" + tagadas_print)
            """
            XXX itt nagyon kell egy (ismeretlen) e3 tárgy felvétele,
            amit aztán lehet egyeztetni (unifikálni) vmivel
            """
            self.stack.add_explicit(w, l, u"ige:TMe3" + tagadas_info)

        # igekötőre várunk, ha nincs
        if not t.find(u"[IK]") > -1:  # not igekotos(l, t):
            self.threads.start(VERB_NO_PREVERB, {u"pos": self.stack.lasti(),
                                                 u"lemma": l})

        printout(u" !! ige után is lezárjuk.")
        self.end()  # ige után is lezárjuk!!!

        return True

    # igekötő
    def __IK(self, w, l, t):
        printout(u" !! igekötő, keressünk hozzá igét (= új szál) + előtte/utána lezár")
        self.end()
        self.stack.add_explicit(w, l, u"igekötő")
        self.threads.start(PREVERB, {u"pos": self.stack.lasti(), u"ik": l})
        self.end()

        return True

    # hatszó
    def __HA(self, w, l, t):

        printout(u" !! határozószó -- mondatszintre vesszük XXX")
        if l == u"nem":  # XXX
            advinfo = u"Adv-mondaté" + ISEP + u"tagadószó"
        else:
            advinfo = u"Adv-mondaté"
        self.stack.add_explicit(w, l, advinfo)

        return True

    # kötőszó: "és"
    def _es_KOT(self, w, l, t):
        printout(u" !! és -- koordinál (" + LISTING +
                 u")? tagmondatokat választ szét? előtte/utána lezárjuk")
        self.end()
        self.stack.add_explicit(w, l, u"és")
        if not self.threads.exists(LISTING):  # ha még nem fut felsorolás
            self.threads.start(LISTING, {u"pos": self.stack.lasti(-1),
                                         u"ptn": self.stack.stack[-1][u"i"]})
        self.end()

        return True

    # "mert" -- mondatokat szétválasztó kötoszó
    def _mert_KOT(self, w, l, t):
        printout(u" !! mert -- tagmondatokat választ szét. előtte/utána lezárjuk")

        # XXX "amely"-bol másolva 1-az-1-ben
        if self.stack.curr_elem(u"vessző"):
            printout(u" !! van vessző, oké.")
            """
            XXX ez tuti ilyenkor? MELYIK fels-t zárjuk???
            egyelőre feltettük, hogy csak 1 van
            """
            self.threads.stop(LISTING)
            printout(u" !! thread " + LISTING + u": CANCEL (mert nem is "
                                    + LISTING + u")")

            self.stack.stack.pop()
            """
            A vesszőt (utsó elem) töröljük (fent)
            eltároljuk, hogy mire vonatk, ez kelleni fog!
            ITT MÉG NEM HASZNÁLJUK A VONATK ot.
            #vonatk = self.stack.stack[-1] # egyelőre egyszerűen: az utsó elem
                                           # ami a legnagyobb összerakott dolog
            Lezárjuk ami eddig volt és kiértékeljük.
            ebben már elkezdünk egy új mondatot
            """
            self.end()
            self.evaluate_sentence()

            self.stack.add_explicit(w, l, u"mert")
            self.end()
        else:
            printout(u" ?? nincs vessző, mit tegyünk?")
            self.new_sentence()  # új mondat

        return True

    """
    ITT A BIRTOK: A "V.MI-nek a V.MI-je" röviden "nAk a" szerkezet
    a többi nincs kezelve még.

    Behackelve a patternek közé. Valamivel szebb így.

    Az esetek NOM,DAT,stb. feldolgozása nem jár elem lezárással, ezért
    fel kell őket dolgozni és itt lezárni. Ez mással is előfordulhat
    Erre kéne(?) egy pszeudo állapot, hogy végül mindenképp lezárja az
    aktuális elemet.

    XXX hekk: birtok lezárása, rögtön nem lehetett,
    mert még jöhetett hozzá fn$case
    ezen lehetne változtatni, hogy egyáltalán ne kelljen ilyen
    dupla hozzáadogatás...
    Hogyan?
    """
    def __birtok(self, w, l, t):
        if self.stack.curr_elem(u"birtok"):  # and processed:
            self.end()
            """
            ez fel is dolgozza rögtön a POSS szálat!
            = rögtön megkeressük a birtokost
            + és lezárjuk a POSS szálat
            end()-be beletenni nem volt jó...
            """
            self.close_poss()
        return True

    """
    Az e nd() és a new _sentence() mindenhez hozzá kell, hogy férjen.
    Ezért vannak a legfelső szinten.
    Egy stack -beli elemet lezár
    """
    def end(self):
        # csak ha van mit, azaz nem pont most nyitottuk
        if not self.stack.new_elem:
            self.stack.new_elem = True

            # LISTING UPDATE
            if self.threads.exists(LISTING):
                printout(u" !! thread " + LISTING + u": UPDATE ", u"")
                """
                'ptn' update: mindig "dinamikus" ki kell számítani a 'ptn'-t:
                A top-level elemek infója összefűzve
                XXX Vigyázni kell a negatív kezdő indexekre!
                XXX egyelőre itt is feltesszük, hogy csak 1 van...
                """
                self.threads.threads[LISTING][u"ptn"] = u" ".join(
                [ item[u"i"]
                  for item in self.stack.stack[ self.threads.threads[LISTING][u"pos"]:self.stack.lasti() + 1 ]
                   if item[u"p"] == set()
                ])
                self.threads.print_one(LISTING)

            # LISTING LEZÁRÁSA
            ## IDE KÉNE JÖNNIE

            # IGE-IGEKÖTŐ SZÁL LEZÁRÁSA
            if (self.threads.exists(PREVERB) and
                self.threads.exists(VERB_NO_PREVERB)):
                self.close_preverb()
                self.stack.added = False

            """
            AZ EGYÉB SZÁLAK KIÍRÁSA
            XXX külön végignézegetjük, hogy mely thread-ek "not-impl"
            """
            for name in set(self.threads.list()) - set([LISTING, PREVERB,
                                                   VERB_NO_PREVERB, POSS]):
                printout(u" !! thread-update-not-impl:", u"")
                self.threads.print_one(name)

    def new_sentence(self, silent=False):
        self.sentences.sentences.append(self.stack.stack)
        if not silent:
            printout(u"==========")
            printout(u" ii " + unicode(self.sentences.curr_sentence())
                   + u". számú mondat következik")
        #Takarítás
        self.stack.empty()
        """
        új mondatnál minden még futó thread-et törlünk
        ez nem tuti, hogy jó megoldás XXX
        """
        self.threads.empty()

    # Ez segédfüggvény: a stack.end alatt szerepel egyedül
    def close_preverb(self):
        ik = self.threads.threads[PREVERB]
        ige = self.threads.threads[VERB_NO_PREVERB]
        printout(u" !! megvan az ige+ik: ", u"")
        printout(ik[u"ik"] + u"|" + ige[u"lemma"], u" ")
        printout(AT + unicode(ik[u"pos"]) + u"|" + AT + unicode(ige[u"pos"]))

        # * stop = mindkét szál kész :)
        self.threads.stop(PREVERB)
        self.threads.stop(VERB_NO_PREVERB)

        # * plusz infó ~ új elem
        # LÉNYEG: könyvelés MINDKÉT helyen (~ dependencia-kapcsolat!)
        self.stack.stack[ik[u"pos"]][u"i"] += (ISEP + u"ige"
                                           + AT + unicode(ige[u"pos"]))
        self.stack.stack[ige[u"pos"]][u"i"] += (ISEP + u"ik"
                                            + AT + unicode(ik[u"pos"])
                                            + ISEP + u"tő=" + ik[u"ik"]
                                            + MORPHSEP + ige[u"lemma"])
        # plusz még a tövet is átírjuk ik-s tőre!
        self.stack.stack[ige[u"pos"]][u"l"] = (ik[u"ik"] + MORPHSEP
                                            + ige[u"lemma"])

        # * parent beállítása (add("új") itt nem kell, mert az ige már megvan!)
        self.stack.stack[ik[u"pos"]][u"p"].add(ige[u"pos"])

    # Ők csak a patternekből hívódnak

    """
    Ezt is bele kéne rakni az end()-be, de nem lehet mert függ a környezetétől
    XXX előtte mindenképp le kell zárni, h ez egy önálló stackitem legyen!
    = A függvény meghívása előtt mindenképp kell egy end()
    NINCS BENNE MÁR END(). A kérdés hogy mi legyen vele?
    """
    def close_listing(self):
        printout(" !! close " + LISTING + u"!")
        thread = self.threads.threads[LISTING]
        """
        XXX itt annak kéne megfogalmazva lennie, hogy
        "van nyitott LISTING thread, aminek jó formájú ptn-je van"
        csakis ekkor zárjuk le!

        "( A.NOM , B.NOM és C.NOM ) mellett" -> FELS lezárul (jó ptn!)
        "A.NOM , B.NOM és ( C.SUP kívül ... )" -> FELS nyitva marad!!!
        persze esetleg lehet majd ez is, ami gond lesz:
        "A.NOM , B.NOM és ( C.NOM mellett ... )"

        ugye a feltétel: jó LISTING ptn kell -- általánosítandó!
        pl.: fnNOM vessző fnNOM és fnNOM
        de ilyen is van: ige:e3 vesszo sima-mn és ige:e3 (!) :)
        """
        ptn = thread[u"ptn"].split(PSEP)

        if  (   ( len(ptn) == 5 and ptn[0] == ptn[2] == ptn[4]  and ptn[1] == u"vessző" and ptn[3] == u"és" )
            or  ( len(ptn) == 3 and ptn[0] == ptn[2]                and ptn[1] == u"és" )
            or  ( len(ptn) == 5 and re.search(u"ige:e3|sima-mn", ptn[0])
                                and re.search(u"ige:e3|sima-mn", ptn[2])
                                and re.search(u"ige:e3|sima-mn", ptn[4])
                                and ptn[1] == u"vessző" and ptn[3] == u"és" )
            ):

            # * stop XXX egyelőre itt is feltesszük, hogy csak 1 van...
            printout(u" !! thread " + LISTING + ": CLOSE")
            self.threads.stop(LISTING)  # kész a felsorolás -- jó itt

            first = thread[u"pos"]
            last = self.stack.lasti()
            printout(u" !! merge_stackitems_felsorolas: " + unicode(first)
                                                  + u".." + unicode(last))

            """
            XXX az van, hogy már lezártuk (mert az is jónak tűnt),
            de igaziból csak most kéne lezárni=ezért csinálunk inkább egy
            új "felsőbb" elemet (igaziból ez csak annyi, hogy "alsóbb" elemek
            is lehetnek a stack-en)

            Hogy lehetne megvalósítani?
             +3] új ötlet (hoppá!) betesszük új elemként a stack tetejére,
             és az új elem rész-elemeinél jelezzük a stack-en,
             hogy az adott elem "helyett" van egy felsőbb szintű elem!!! EZ JÓ!
            XXX - threads-ben is kéne update nem trivi -- egyelőre not-impl!
            -> LISTING/ptn-re megvalósítva: ptn dinamikus számítása által!
            """
            """
            A ",", "és", "nem"-eket kiszedtem az if-ből, mert a fában
            a felsorolás részei mint speciális kötőelem szerintem.
            """
            for i in range(first, last + 1):
                # Itt csak a top-level elemeket nézzük
                if self.stack.stack[i][u"p"] == set():
                    # parent beállítása egyúttal
                    self.stack.stack[i][u"p"].add(self.stack.lasti() + 1)

            mw = u" ".join(map(lambda x: x[u"w"], self.stack.stack[first:last + 1]))
            ml = LSTLEMMASEP.join([i[u"l"] for i in self.stack.stack[first:last + 1]
                                             if i[u"w"] != u"," and
                                                i[u"w"] != u"és" and
                                                i[u"w"] != u"nem" and
                                                self.stack.lasti() + 1 in i[u"p"]
                                  ])
            mi = self.stack.stack[last]["i"]  # az utsó!! XXX

            # * add("új") + parent -- hozzáadjuk a FELS-t képviselő új elemet
            self.stack.add_explicit(mw, ml, mi)
            self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                                u"idx": self.stack.lasti()}, self.stack)
        else:
            printout(u" XX nem jó formájú " + LISTING + u"-ptn:", u"")
            printout(u"'" + thread[u"ptn"] + u"'")

    """
    EZT elvileg már bele kéne tenni az end() be, de most minden PS tagra
    meghívódik manuálisan
    MERT az end() többször is meghívódik egy szóhoz és ezért itt csak
    bonyolítaná a dolgokat
    ÚJRA KÉNE GONDOLNI
    """
    def close_poss(self):
        if self.threads.exists(POSS):
            printout(u" !! close " + POSS + u"!")
            """
            thread = threads[POSS]
            itt keressük a birtokhoz a birtokost,
            ha megvan, összeteszzük a birtokost
            + birtokot (+ lezárjuk a szálat)
            XXX finomítani kell: 'nak a' kezelése
            """

            # Itt csak a top-level elemeket nézzük
            stack_top_elements = filter(lambda x: x[u"w"] != u"," and
                                                x[u"w"] != u"és" and
                                                x[u"w"] != u"nem" and
                                                x[u"p"] == set(),
                                                self.stack.stack)
            if (len(stack_top_elements) >= 2 and
                    (re.search(u"fnNOM|fnDAT", stack_top_elements[-2][u"i"]))):
                birtokos = list_rindex(self.stack.stack,
                                            stack_top_elements[-2])
                birtok   = list_rindex(self.stack.stack,
                                            stack_top_elements[-1])
                printout(u" !! megvan a birtokos!")
                # * stop
                self.threads.stop(POSS)
                # * add("új")
                self.stack.added = False
                self.stack.add_explicit(self.stack.stack[birtokos][u"w"]
                                        + u' '
                                        + self.stack.stack[birtok][u'w'],
                                          self.stack.stack[birtok][u"l"],
                                          self.stack.stack[birtok][u"i"])
                self.partics.add_partic({u"sidx": self.sentences.curr_sentence(),
                                         u"idx":  self.stack.lasti()},
                                                  self.stack)
                # * parent
                self.stack.stack[birtokos][u"p"].add(self.stack.lasti())
                self.stack.stack[birtok][u"p"].add(self.stack.lasti())
                # * end("új")
                self.end()
            else:
                printout(u" XX nincs meg a birtokos (" + POSS + u")")
                # ekkor is lezárjuk (szomorúan), de lehet, h nem kéne!
                self.threads.stop(POSS)

    # Mondatról való végső vélemény/összefoglaló kialakítása
    def evaluate_sentence(self):
        # (1) LEZÁR MIDNEN SZÁLAT (AMIT KELL)
        self.close_threads_on_sentence_end()

        # (2) ÉRTÉKELI AMI VAN
        self.mondat_osztalyozas()

        # (3) TOVÁBB LÉP ÉS TAKARÍT
        printout(u"")  # újsor
        self.new_sentence()  # új mondatot kezdünk

    # Ez segédfüggvény: a close_ threads_on_sentence_end alatt szerepel egyedül
    def close_listing_ertelmezo(self):
        ptn = self.threads.threads[LISTING][u"ptn"]

        ptn = re.sub(u"birtok;?", "", ptn)
        """
        XXX hú, ez hekkparádé így arról van szó, hogy
         * a 'birtok' itt egy olyan infó, ami 'nemlényegi',
         * a 'fnNOM' meg egy olyan infó, ami 'lényegi'
         itt csak a lényegi infó kell
          => ezt a 2 infó-típust elkülönítve kellene kezelni...
        lehetőségek:
         * 'i'-ben egy speciális jellel megjelölve
         * másik mezőben (de akkor meg bonyi lehet a szinkronizálás...)
        """
        printout(u" ?? lehet, hogy értelmező?")
        if re.search(u"^([^ ]+)" + PSEP
                   + u"vessző"   + PSEP
                   + u"\\1"      + PSEP
                   + u"(?!\\1)", ptn):
            printout(u" !! megvan az értelmező! :)")
            pos = self.threads.threads[LISTING][u"pos"]

            """
            Itt csak a top-level elemeket nézzük
            amikor megkeressük a konkrét stack-beli pozíciókat
            XXX ezt jobban kéne, pl. tárolni valahol ezt az infót...
            """
            l = filter(lambda x: x[u"p"] == set(), self.stack.stack[pos + 1:])
            pos1 = list_rindex(self.stack.stack, l[0])
            pos2 = list_rindex(self.stack.stack, l[1])

            # * plusz infó ~ új elem
            self.stack.stack[pos][u"i"] += (ISEP + u"értelmező"
                                        + AT + unicode(pos2))
            # * parent
            # az értelmezett lesz a vessző p-je
            self.stack.stack[pos1][u"p"].add(pos)
            # az értelmezett lesz az értelmezo p-je
            self.stack.stack[pos2][u"p"].add(pos)

            self.stack.stack_print_out()
        else:
            printout(u" XX nem értelmező")

    # Ez segédfüggvény: a evaluate_ sentence alatt szerepel egyedül
    def close_threads_on_sentence_end(self):
        # mi gyűlt fel
        self.stack.stack_print_out()
        self.stack.elems_print_out()

        if self.threads.exists(VERB_NO_PREVERB):
            printout(u" !! " + VERB_NO_PREVERB + u" simán megszüntetendő")
            self.threads.stop(VERB_NO_PREVERB)

        # FELS: először megpróbáljuk simán lezárni :)
        if self.threads.exists(LISTING):
            self.close_listing()
            if not self.threads.exists(LISTING):
                self.stack.stack_print_out()  # ha lezáródott
                """
                FELS: ha még mindig van (sikertelen lezárás),
                és a kezdete ilyen: 'A , A B',
                akkor lezárjuk és a 2. A-t értelmezőként elemezzük
                """
            else:
                # XXX EZ ÍGY INKÁBB ROSSZ MINT JÓ! JÓL GONDOLOM?
                self.close_listing_ertelmezo()
                # * stop
                self.threads.stop(LISTING)

        # a még mindig megmaradt thread-ek:
        if self.threads.count() > 0:
            printout(u"MEGMARADT elvarratlan thread-ek:")
            self.threads.print_out()

    # Ez segédfüggvény: a evaluate_ sentence alatt szerepel egyedül
    def mondat_osztalyozas(self):
        # itt készítjük el az aktuális elems-t
        self.stack.elems_print_out()
        elems = self.stack.generate_elems()

        kesz = False

        # kiértékelés
        printout(u" >>", u"")

        #### (1) mondattípus: ige + (pár) fnCASE + (esetleg pár) Adv-mondaté

        ige_fn_adv = True
        ige = False
        """
        XXX hogy is lehetne ezt a feltételt kicsit egyszerűbben összerakni?
        ige mindenképp kell + az ige mellett lehet: NP, Adv

        Lineáris keresés, ami mindenképp végigmegy a vektoron,
        két független dolgot vizsgál:
        jelentése: van-e igénk a mondatban?) és az ige_fn_adv változót
        jelentése: csak ige|névszói_csoport|adv van-e a mondatban?
        """
        for elem in sorted(elems.keys()):
            if (not re.search(u"fn...", elem) and
                not re.search(u"^névutó:", elem) and
                not re.search(u"Adv-mondaté", elem) and
                not re.search(u"ige:(TM?)?e3", elem) and
                elem != u"vessző"):
                """
                a vessző megengedése durva hack
                XXX a "Később, a római..." mondatkezdet miatt általánosítani!
                tudni illik hogy csak fn és Adv van benne
                XXX az ige:...-ot az előzőben is be kell írni... :)
                """
                ige_fn_adv = False
            if re.search(u"ige:(TM?)?e3", elem):
                ige = True

        """
        Ezt a két dolgot/feltételt állítjuk be egyszerre.
        Az ige -t true-re állítjuk, ha találunk egy igét (trivi).
        Az ige_fn_adv -t false-ra állítjuk, ha találunk
        ige|névszói_csoport|adv-tól különbözőt.
        Itt a névutós csoport is névszói csoportnak számít,
        mert a ragok meg a névutók azonosan kezelendők.
        (Ahogy oda is írtam, az egy hack, hogy még pluszban a vesszőt
        is megengedjük...)
        """

        if not kesz and ige and ige_fn_adv:
            explicitalany = False
            printout(u" sima igés mondat.", u"")
            for elem in sorted(elems.keys()):
                # biztosítottuk, hogy legyen ige
                if re.search(u"ige:(TM?)?e3", elem):
                    # XXX egyelőre bután az elsőt veszi (hiába van akár több)
                    i = elems[elem][0]
                    printout(u" állítmány(" + elem + u")["
                            + AT + unicode(i) + "]: '"
                            + self.stack.stack[i][u"w"] + u"'.", u"")
                elif re.search(u"fnNOM", elem):
                    # XXX egyelőre bután az elsőt veszi (hiába van akár több)
                    i = elems[elem][0]
                    printout(u" alany(" + elem + u")["
                            + AT + unicode(i) + u"]: '"
                            + self.stack.stack[i][u"w"] + u"'.", u"")
                    explicitalany = True
                else:  # itt mindet végigvesszük (pl. több Adv...)
                    for i in elems[elem]:
                        if elem == u"vessző":
                            hack = u"(hack!)"
                        else:
                            hack = u""
                        printout(u" " + elem + hack + "["
                                + AT + unicode(i) + u"]: '"
                                + self.stack.stack[i][u"w"] + u"'.", u"")
                    """
                    XXX egyelőre bután az elsőt veszi (hiába van akár több)
                    'róla' kezelése kell: ugye ez is 'vmi korábbi'-ra utal
                    """
            if not explicitalany:
                # XXX általánosítani!
                printout(u" alany igerag alapján: e3.", u"")
            kesz = True

        #### (2) mondattípus: birtokos + birtok (és kész)
        # XXX ezt kicsit fel kéne turbózni az indexek kiírásával
        if ( not kesz and len(elems.keys()) == 2 and
             u"birtok" in elems and "fnDAT" in elems and
             len(elems[u"birtok"]) == 1 and len(elems[u"fnDAT"]) == 1
           ):
            printout(u" ez egy puszta birtokos szerk.", u"")
            if elems[u"birtok"][0] < elems[u"fnDAT"][0]:
                printout(u" fordított sorrendű.", u"")
            printout(u" alany: e3 (vmi korábbi).", u"")
            printout(u" állítmány: '"
                    + self.stack.stack[elems[u"birtok"][0]][u"w"]
                    + u"'.", u"")
            kesz = True

        ### (3) mondattípus: két NOM-ból álló azonosító mondat ('Apám katona.')
        # XXX ez nem ellenorzi, hogy valóban pontosan 2 elem van-e!
        if ( not kesz and
           ( len(elems.keys()) == 1 and
             re.search(u"fnNOM", elems.keys()[0])
           ) or
           # mert lehet pl. 'fnNOM' + 'birtok;fnNOM'
           ( len(elems.keys()) == 2 and
             re.search(u"fnNOM", elems.keys()[0]) and
             re.search(u"fnNOM", elems.keys()[1])
           )
           ):
            printout(u" azonosító mondat: 1. alany + 2. állítmány (rendesen kiírni XXX)", u"")
            kesz = True

        #### (X) nem sikerült értelmezni a mondatot
        if not kesz:
            printout(u" !! not-impl mondat...", u"")

    def parser_step(self, w, l, t):
        printout(u"\n" + w + u" (" + l + u") -- " + t)   # Elválasztó
        # Globális # hozzáadtuk-e az aktuális stack-item-hez
        self.stack.added = False
        proc = False
        for patt in self.ELEMEK.iterkeys():
            if patt.match(w + u"#" + l + u"#" + t):
                #try:
                      # elméletileg pontosan egyet kéne feldolgoznia,
                      # ám gyakorlatilag...
                    proc = self.ELEMEK[patt](w, l, t)
                    """
                except Exception as e:
                    print e, patt.pattern, elemek[patt].__name__
                    raise e
                    """
                    #break # Ez nincs mert a tagok kombinálódhatnak
        if not proc:
            printout(u" !! not-processed")

        # stack...
        self.stack.stack_print_out()
        self.stack.elems_print_out()
        self.threads.print_out()
        self.partics.partics_print_out()


class fullMorphology:

    def __init__(self, lb, g):
        self.lexicon_based = lb
        self.guesser = g

    """
    megcsinálja a (word, lemma, tag) hármasokat
    a map egységesíti a formátumot
    ha nincs lexikon-alapú elemzés, akkor guessel
    """
    def analyze(self, word):
        return (map(lambda x: (word,
                                x[0],
                                x[1]),
                    self.lexicon_based.analyze(word)) or
                map(lambda x: (word,
                                x[0:x.index(u'[')],
                                x[x.index(u'['):]),
                    self.guesser.guess(word)))

merge_morph_l = lambda x: u"#".join(x)


"""
A legutolsó szóra és a POS_THRESHOLD-ra szűri a tag listát
WLT = (w,l,t)
candidates = [([WLT],state)]
Itt rengeteg descart szorzás és szűrés van.
Egymásba ágyazott while ciklusokkal és szűréssel oldható meg szépen
Iterátorral, vagy sokszor megy végig,
vagy pedig sok lehetőséget néz végig fölöslegesen
vagy hashel egy csomó mindent és abban keres
Elemek: Eddigi jelöltek X (Morfológia | POS) | POS
A lenti megoldás:
Csinál egy WLT dict-et a tag mint kulcs alapján
A POS-t partícionálja (Tag_{n-1},Tag_n)-re miközben
a morfológiára (Tag_n) szűr és csinál egy hash-t a dicthez
A T_{n-1} re átfuttatja a candidate_eket és a jót descartozza a morfológiával
Majd összenézi az összes taget, hogy csak a jó kombinációkat vegye
Végül a jókat még 0:n ig is összenézi!
Mindeközben gyűjti és kiírja a fölösleges Debug infókat
"""
def merge_candidates(candidates, anals, pos_tags):
    printout(u"\n\nAz aktuális szó morfológiai elemzése: %s" %
             u"\t".join(map(merge_morph_l, anals)))

    # Dict-et étpít: { t => [(w,l), (w,l2), ... ] }
    morph_tags = defaultdict(list)
    for w, l, t in anals:
        morph_tags[t].append((w, l, t))
    morph_tags.default_factory = None  # Lezárja a dict-et

    # Szűr a morfológia alapján
    tags_new = defaultdict(list)
    tags_used = {}
    tags_morph = []
    for tags, score in pos_tags:
        if tags[-1] in morph_tags:  # Jó
            """
            Csinál egy hash-t a régi tagekből a hasonlítgatáshoz
            Az újból WLT hármasokat mint lehetséges folytatási osztály
            Ha több tagja lehet az n. szónak akkor több folytatás is lehet,
            egy n-1 -es sorozathoz!
            """
            tags_new[u"\t".join(tags[0:-1])].append((morph_tags[tags[-1]],
                                                    score))
            tags_used[u"\t".join(tags)] = (False, score)  # Felhasználjuk?
        else:  # A morfológia szűrte ki
            tags_morph.append(u"%s %f" % (u"\t".join(tags), score))

    tags_new.default_factory = None  # Lezárja a dict-et

    new_cand = []
    bad_cand = []
    # (TAG_HASH_FOR_POS, [WLT], PARSER_STATE, SCORE)
    for pos_hash, anals, state, score in candidates:
        if not pos_hash or pos_hash in tags_new:
            for WLTs, pos_score in tags_new[pos_hash]:
                # Új hash: a WLTs lista első (0) elemének tagjából (2)
                new_pos_hash = u"%s\t%s" % (pos_hash, WLTs[0][2])
                new_pos_hash = new_pos_hash.strip()  # Új mondatoknál érdekes.

                """
                Külön jó az n-1. és az n. tag de együtt is meg kell nézni!
                Még így is lehet több lemma egy taghez és elszaladhat a dolog!
                """
                if new_pos_hash not in tags_used:
                    break

                tags_used[new_pos_hash] = (True, pos_score)  # Felhasználtuk.

                # Az összes analt létrehozza
                for WLT in WLTs:
                    new_anals = anals + [WLT]
                    """
                    Ez akkor kell, ha többfelé folytatjuk az elemzést,
                    különben elég a referencia is.
                    """
                    new_cand.append((new_pos_hash,
                                     new_anals,
                                     pilotParser(parserState=state.parserState()),
                                     pos_score))
        else:
            # A nem folytatható analok adataiból ami kell: WLT
            bad_cand.append(u"%s %f" % (u"\n".join(map(merge_morph_l, anals)),
                                        score))

    tags_new_good = []
    tags_new_bad = []
    for key, val in tags_used.iteritems():
        if val[0]:
            tags_new_good.append((u"%s %f" % (key, val[1])))
        else:
            tags_new_bad.append((u"%s %f" % (key, val[1])))

    if tags_morph:
        printout(u"\nPOS -- Elvetett tagsorozat (morfológia) (%d):" %
                 len(tags_morph))
        for tags in tags_morph:
            printout(tags)

    if tags_new_bad:
        printout(u"\nPOS -- Elvetett tagsorozat (%d):" %
                 len(tags_new_bad))
        for tags in tags_new_bad:
            printout(tags)

    if tags_new_good:
        printout(u"\nPOS -- Egyező tagsorozat (%d):" %
                 len(tags_new_good))
        for tags in tags_new_good:
            printout(tags)

    if bad_cand:
        printout(u"\nAbba hagyjuk az elemzést (%d):" %
                 len(bad_cand))
        for sent in bad_cand:
            printout(sent, u"\n\n")

    if new_cand:
        printout(u"\nFolytatjuk az elemzést (%d):" %
                 len(new_cand))
        for (pos_hash, anals, state, score) in new_cand:
            printout(u"%s\n%f" % (u"\n".join(map(merge_morph_l, anals)),
                                  score), u"\n\n")

    out = []
    for (pos_hash, anals, state, score) in new_cand:
        printout(u"\n---------------------------------------------------\n")
        printout(u"Következő elemzési lépés:\n%s" %
                 u"\n".join(map(merge_morph_l, anals)), u"\n\n")
        w, l, t = anals[-1]
        state.parser_step(w, l, t)
        printout(u"\nVÉGE: Következő elemzési lépés")
        out.append((pos_hash, anals, state, score))

    return out

# Utility függvények


# Kiíró függvény, ami magában foglalja az encode-olást.
def printout(text, newline=u"\n"):
    sys.stdout.write((text + newline).encode('utf-8'))
    sys.stdout.flush()


# Kiíró függvény, ami magában foglalja az encode-olást.
def printerr(text, newline=u"\n"):
    sys.stderr.write((text + newline).encode('utf-8'))
    sys.stderr.flush()


"""
Fájlbeolvasó, ami magába foglaja a hibakezelést.
Mindent berak egyszerre a memóriába.
Nagy fájlokon nem szabad használni!!!
"""
def openf(filename):
    try:
        with codecs.open(filename, 'r', 'utf-8') as in_file:
            return in_file.readlines()
    except IOError:
        printerr(u"Nem sikerült megnyitni a fájlt: '"
                 + filename.decode("utf-8") + u"' !")
        sys.exit(1)


"""
Jelenleg nincs használva!
Enum típus <3.4 es pythonhoz
Forrás: http://stackoverflow.com/a/1695250
"""
def enum(**enums):
    return type('Enum', (), enums)


"""
A string.index() függvény megfelelője lista elemek keresésére,
list.index() csak ez hátulról-előre nézi az első előfordulást...
"""
def list_rindex(in_list, item):
    return len(in_list) - 1 - in_list[::-1].index(item)


"""
Jelenleg nincs használva!
Fura, hogy ilyen nincs alapból a pythonban:
 A filter függvény, ha a predikátum nem igaz, kiszedi a listából az elemet.
 Ez a függvény beteszi ezeket az elemeket egy másik listába.
Forrás: http://stackoverflow.com/a/4578605
"""
def partition(pred, iterable):
    trues = []
    falses = []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


"""
Listát Unique-ol (akkor kell, ha nem lehet set()-et használni:
Pl.: lista a listában)
Forrás: http://stackoverflow.com/a/7974218
"""
import itertools


def unique(a):
    indices = sorted(range(len(a)), key=a.__getitem__)
    indices = set(next(it) for k, it in
                  itertools.groupby(indices, key=a.__getitem__))
    return [x for i, x in enumerate(a) if i in indices]


class POS_server:

    def __init__(self, port=50000):
        self.server_port = port

    # Forrás: http://ilab.cs.byu.edu/python/socket/echoclient.html
    def tag(self, sent, tresh=POS_TRESHOLD):
        host = 'localhost'
        port = self.server_port
        size = 65536
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        #print "Connected. Sending..."
        s.send(pickle.dumps(sent))
        #print "Sent. Receiveing..."
        data = s.recv(size)
        s.close()
        #print 'Received:', data
        return pickle.loads(data)


class MGuesser_server:

    def __init__(self, port=60000):
        self.server_port = port

    # Forrás: http://ilab.cs.byu.edu/python/socket/echoclient.html
    def guess(self, word):
        host = 'localhost'
        port = self.server_port
        size = 65536
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        #print "Connected. Sending..."
        s.send(word.encode("utf8"))
        #print "Sent. Receiveing..."
        data = s.recv(size)
        s.close()
        #print 'Received:', data
        return pickle.loads(data)


def load_models(POS, MGuesser):
    if not os.path.isfile(POS[u'model_file']):
        printout(u"Creating pickle of the POS model...", u"")
        pickle_POS(POS[u'model_file'], POS[u'training_data'])
        printout(u"Done")

    if not os.path.isfile(MGuesser['model_file']):
        printout(u"Creating pickle of the Morphological guesser model...", u"")
        pickle_MGuesser(MGuesser['model_file'], MGuesser['training_data'])
        printout(u"Done")

    printout(u"Loading POS model...", u"")
    model = init_POS(POS[u'model_file'], Humor())
    printout(u"Done")

    printout(u"Loading Morphological guesser model...", u"")
    guesser = init_MGuesser(MGuesser['model_file'])
    printout(u"Done")

    return (model, guesser)


# main
def main():
    POS = {}
    MGuesser = {}

    # Ha az utolsó argument "TEST" akkor a teszt adatokat tölti be
    # (sokkal gyorsabb).
    test = sys.argv[-1].decode('utf-8')
    test = None  # u"TEST"

    if test == u"TEST":
        # Szeged korpusz 100 mondata teszt célokra
        POS[u'training_data']   = os.path.abspath(u"util/elemzo_pos_model/sz100.txt")
        POS[u'model_file']      = os.path.abspath(u"szeged_POS_model_test")

        MGuesser['training_data']   = os.path.abspath(u"util/elemzo_pos_model/sz100.txt")
        MGuesser['model_file']      = os.path.abspath(u"szeged_MGuesser_model_test")

    else:
        # Szeged korpusz
        POS[u'training_data']   = os.path.abspath(u"util/elemzo_pos_model/szeged_corpus.txt")
        POS[u'model_file']      = os.path.abspath(u"szeged_POS_model")

        MGuesser['training_data']   = os.path.abspath(u"util/elemzo_pos_model/szeged_corpus.txt")
        MGuesser['model_file']      = os.path.abspath(u"szeged_MGuesser_model")

    server = None
    if not server == None:
        (POS, MGuesser) = load_models(POS, MGuesser)
    else:
        (POS, MGuesser) = (POS_server(), MGuesser_server())

    morph = fullMorphology(Humor(), MGuesser)

    if test == u"TEST":
        # Teszt
        print POS.tag(u"Alma fája kutya macska".split())
        print MGuesser.guess(u"alma")
        print morph.analyze(u"alma")
        exit(1)

    if len(sys.argv) < 2 or sys.argv[1] == u"-h":
        printerr(u"A program használata: "
                 + sys.argv[0].encode('utf-8')
                 + u" beolvasandó_fájl.txt !")
        sys.exit(1)
    fajl = sys.argv[1]

    #fajl = u"input/fuge.tokenized.txt"
    #fajl = u"input/inforadio_elso10.tokenized.txt"
    #fajl = u"input/index_hu_leadek.tokenized.txt"

    # Új paragrafusnál, az első szót feldolgozza külön. Új egység.
    new_paragraph = True
    start = 0
    for line in openf(fajl):
        line = re.sub(u'\n', u"", line)
        # Ha érdektelen a sor kihagyjuk.
        if len(line) > 0 and line[0] != u"#":
            if new_paragraph:
                words = line.split(u" ")[0:1]
                """
                Az első szót feldolgozza
                (TAG_HASH_FOR_POS, [WLT], PARSER_STATE, SCORE)
                """
                anals = morph.analyze(words[0])
                printout(u"Az aktuális szó morfológiai elemzése: %s" %
                         u"\t".join(map(merge_morph_l, anals)))

                good_candidates = map(lambda x: (x[2],  # TAG_HASH
                                                 [x],    # WLT
                                                  pilotParser(True),
                                                  0.0),  # Score
                                      anals)
                for H, WLT, P, S in good_candidates:
                    P.parser_step(WLT[0][0], WLT[0][1], WLT[0][2])
                new_paragraph = False
                start = 1
                POS.cache = {}  # Cache ürítés ha új paragrafust kezdünk.
            else:
                words = []  # A POS-tagger nem lát túl a mondathatáron
                good_candidates = map(lambda (HASH, WLTs, state, score):
                                               (u"", WLTs, state, score),
                                        good_candidates)
                start = 0

            for tok in line.split(u" ")[start:]:
                """
                Itt három dolgot csinál:
                1) A morfológiai elemzést (morph.analyze)
                2) A szavak alapján a POS score-okat (POS.tag)
                3) Egy lépésben szűri a POS jelölteket:
                  a) A küszöb fölött van-e a score
                  b) Az aktuális szóra nézve a morfológiával egyezik
                  c) A függőben lévő lehetőségeket szűri, a többi szó alapján
                4) Elvégzi a következő parser lépést
                """
                words.append(tok)
                good_candidates = merge_candidates(good_candidates,
                                                   morph.analyze(tok),
                                                   POS.tag(words, POS_TRESHOLD))
                if not good_candidates:
                    printout(u"HIBA: Minden lehetőség elfogyott!")
                    sys.exit(1)
        else:
            new_paragraph = True
    sys.exit(0)


if __name__ == "__main__":
    main()
