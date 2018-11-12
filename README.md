AnaGramma-Parser
================

Egy pszicholingvisztikai indíttatású elemző modell

Részben vagy egészben történő felhasználás esetén az alábbi cikket
kell meghivatkozni:
Prószéky Gábor, Indig Balázs, Miháltz Márton, Sass Bálint:
"Egy pszicholingvisztikai indíttatású számítógépes nyelvfeldolgozási modell felé"
X. Magyar Számítógépes Nyelvészeti Konferencia MSzNy. 2014. január 16-17 (2014).

### Függőségek:

- Python 3.5 (*Nix alapú rendszeren, preferáltan Linux)
- NLTK 3.0
- [PurePOSPy](https://github.com/ppke-nlpg/purepospy) (a megfelelő verzió szükséges)
- Humor morfológiai elemző REST API-n keresztüli eléréssel hasonlóan az [emMorpPy](https://github.com/ppke-nlpg/emmorphpy)-hez.

### Használata:

1. Két helyen a kódban meg kell adni a megfelelő elérésiutakat a PurePOS és a Humor REST API-hoz (ling_rules/morphology_converter/morphologyConverter.py:231 és engine/windowedMorphology.py:102)
2. ./test.sh futtatásával a példamondatokon lefut a teszt a forráskódban definiált mondatokon.


### Nyelvi szabályok:

A rendszer négy egymással konzisztens lépésre épül:

1. A töbtagúnév esetek feldolgozása a szófaji egyértelműsítés után: ling_rules/mosaic.py
2. Morfológia: Humor kód -> Elemző jellemzők konvertálása: ling_rules/morphology_converter/morphologyConverter.py
3. Minták feldolgozása: Az egyes tokenek jellemzői definiálják a teendőiket (pl. __dinamikus jellemzők__, __keresletek__), amiket egy külön lépésben végrehajt a program: ling_rules/patternsAndActions.py
4. A definiált __keresők__ implementációi: A program futása során ezek a programrészletek futna le a __keresők__ működése közben: ling_rules/mainActions.py
5. (+1) Az igekötők és vonzatkeretek szótára külön fájlban kapott helyet: ling_rules/verbDictionary.py


### Kapcsolódó modulok:

- [Manócska](https://github.com/ppke-nlpg/manocska): Integrált igei vonzatkerettár, mely az elemző vonzatkeret-szótáraként használható
- [VFrame](https://github.com/ppke-nlpg/vframe): Az igék vonztatkeret-lehetőségeinek leszűkítésére használt eljárás, beépítésre került az elemzőbe
- [Nom-or-What](https://github.com/ppke-nlpg/nom-or-what): A morfológiai "nominatívusz" egyértelműsítésére szolgáló eljárás, beépítésre került az elemzőbe
- [Whats wrong, Python?](https://github.com/ppke-nlpg/whats-wrong-python): Nyelvtechnológiai programok kimenetének és a kimenetek különbségeinek vizualizációjára is használható könyvtár (béta állapotú), felhasználható mint az elemző vizuális kimenete
- [EmMorphPy](https://github.com/ppke-nlpg/emmorphpy): A Humor morfológiai elemzőhöz is használt REST API azóta továbbfejlesztett változata, az elemzőben a Humor REST API-ját szolgáltatja
- [PurePOS](https://github.com/ppke-nlpg/purepos): Szófaji egyértelműsítő, az elemzőben ideiglenesen került felhasználásra
- [PurePOSPy](https://github.com/ppke-nlpg/purepospy): Python wrapper és REST API a PurePOS-hoz, az elemzőben ideiglenesen került felhasználásra


Technikai kérdésekkel kapcsolatban Indig Balázst (indig.balazs@itk) lehet keresni.
