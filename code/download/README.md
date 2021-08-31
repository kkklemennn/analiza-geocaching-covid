# Zagon pridobivanja podatkov iz Geocaching

Najprej se v isti mapi, kjer se nahaja program `caches_scraper.py` kreira nova datoteka `config.yaml` z elektronskim naslovom in geslom za dostop do Geocaching.

```
email: zamenjaj-z-elektronskim-naslovom
geslo: zamenjaj-z-geslom
```

Na koncu program poženemo z naslednjim ukazom.

```
$ python -u caches_scraper.py
```

Program v mapi _data/download/_ najprej ustvari datotko `vsi-zakladi-Slovenia.json`, kjer so zbrani bolj splošni podatki o zakladih. Nato se v tej mapi kreira nova mapa _zakladi_, kamor program shranjuje nove datoteke z imenom _`GCkoda`_`.json`, ki vsebujejo podrobnosti o posameznih zakladih.

Za tem program podobno še stori za podatke z uporabniki. Program v mapi _data/download/_ najprej ustvari datotko `vsi-uporabniki-Slovenia.json`, kjer so zbrani bolj splošni podatki o uporabnikih. Nato se v tej mapi ustvari nova mapa _zakladi_, kamor program shranjuje nove datoteke z imenom _`idUporabnika`_`.json`, ki vsebujejo podrobnosti o posameznih uporabnikih.
