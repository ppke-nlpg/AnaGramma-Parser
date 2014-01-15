AnaGramma-Parser
================

Egy pszicholingvisztikai indíttatású elemző modell

Részben vagy egészben történő felhasználás esetén az alábbi cikket 
kell meghivatkozni:
Prószéky Gábor, Indig Balázs, Miháltz Márton, Sass Bálint:
"Egy pszicholingvisztikai indíttatású számítógépes nyelvfeldolgozási modell felé"
X. Magyar Számítógépes Nyelvészeti Konferencia MSzNy. 2014. január 16-17 (2014).

Függőségek: 
- python 2.7 (*Nix alapú rendszeren, preferáltan linux) 
- NLTK 3.0

Használata:

1.	A szerverek elindítása:
		cd pos_model
		python prob_model.py szeged_POS_model --server 50000 &
		python morph_guesser.py --server 60000 &
		cd ..

1.	A fő program futtatása, miután a szerverek készen állnak:
		python pilot.py input/inforadio_elso10.tokenized.txt
	*FIGYELEM! A FUTÁSI IDŐ HOSSZÚ LEHET!*

1.	A szerverek leállítása:
		killall -9 python

Minták az input és output mappában találhatók.
A futásidőkről a kimenet fájlok végén lehet tájékozódni.

A szeged_*_model* fájlok a Szeged korpusz[1] felhasználásával készültek.

[1] Csendes, Dóra, et al. 
"Kézzel annotált magyar nyelvi korpusz: a Szeged Korpusz."
II. Magyar Számıtógépes Nyelvészeti Konferencia (2003): 238-245.


Technikai kérdésekkel kapcsolatban Indig Balázst (indig.balazs@itk) lehet keresni.
