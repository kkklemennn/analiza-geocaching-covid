# Analiza gibanja igralcev igre Geocaching v času COVID-19 v Sloveniji

## Procesiranje podatkov pred analizami

Ko že imamo podatke o zakladih in uporabnikih, jih moramo pred samim analiziranjem najprej sprocesirati.

Program _[`razvrstiZaklade.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/razvrstiZaklade.py)_
bere iz datotek `vsi-zakladi-Slovenia.json`, `OSM-slovenske-obcine.geojson`, `OSM-slovenske-statisticne-regije.geojson` in `obcine-v-regijah.json`.
Razvrsti zaklade po občinah in regijah, ter rezultat shrani v `zakladi_lokacije.json`.
Zaženemo ga z ukazom:

```
$ python razvrstiZaklade.py
```

Program _[`pridobiFTF.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/pridobiFTF.py)_ bere iz datoteke `vsi-zakladi-Slovenia.json`.
Pridobi FTF-je igralcev, ter rezultat shrani v `ftf.json`. Zaženemo ga z ukazom:

```
$ python pridobiFTF.py
```

Program _[`dolociLokacijo.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/dolociLokacijo.py)_ bere iz datotek `vsi-zakladi-Slovenia.json`, `vsi-uporabniki-Slovenia.json`, `obcine-v-regijah.json`, `vsi-uporabniki-Slovenia.json`, `OSM-slovenske-obcine.geojson`, `OSM-slo3-place-city-town.geojson`,
`OSM-slovenske-statisticne-regije.geojson` in
`ftfs.json`.
Vsakega igralca klasificira ali je domačin ali tujec; domačinom določi občino in regijo, ter rezultat shrani v `uporabniki_lokacije.json`. Zaženemo ga z ukazom:

```
$ python dolociLokacijo.py
```

Program _[`pridobiSkupine.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/pridobiSkupine.py)_ bere iz datotek `vsi-uporabniki-Slovenia.json`, `vsi-zakladi-Slovenia.json`, `uporabniki_lokacije.json` in `zakladi_lokacije.json`.
Vsakega igralca klasificira ali je domačin ali tujec ter domačinom določi občino in regijo, ter rezultat shrani v `skupine.csv`. Zaženemo ga z ukazom:

```
$ python pridobiSkupine.py
```

## Analiziranje podatkov

V datoteki _[`descStat.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/descStat.py)_ se nahaja koda za pridobivanje splošne statistike o pridobljenih podatkih z Geocachinga. To je večinoma prikazano v diplomski nalogi v poglavju 2.1.2 - Opis podatkov. V tej datoteki so definirane funkcije z opisi in nekaj komentarji s pojasnili.
Program bere iz datotek `vsi-uporabniki-Slovenia.json`, `vsi-zakladi-Slovenia.json`,  
`uporabniki_lokacije.json` in
`zakladi_lokacije.json`.
Za prikaz rezultata (ki je bodisi tekstoven, graf ali oboje) posamezne funkcije je potrebno to funkcijo na koncu programa klicati in zagnati program z ukazom:

```
$ python descStat.py
```

V datoteki _[`analiza.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/analiza.py)_ se nahaja koda za pridobivanje rezultatov analiz, ki so opisani v diplomski nalogi v poglavju 5 - Analzia podatkov. V tej datoteki so definirane funkcije z opisi in nekaj komentarji s pojasnili.
Program bere iz datotek `vsi-uporabniki-Slovenia.json`, `vsi-zakladi-Slovenia.json`,  
`uporabniki_lokacije.json`, `zakladi_lokacije.json`, statistike COVID-19 Sledilnika (`stat.csv`) ter statistike Google in Apple trendov mobilnosti (`2020_SI_Region_Mobility_Report.csv`, `2021_SI_Region_Mobility_Report.csv`, `applemobilitytrends-2021-08-02.csv`).
Za prikaz rezultata (ki je bodisi tekstoven, graf ali oboje) posamezne funkcije je potrebno to funkcijo na koncu programa klicati in zagnati program z ukazom:

```
$ python analiza.py
```

## Koda v ostalih datotekah.

V datoteki _[`GPSUtils.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/GPSUtils.py)_ se nahajajo pomožne funkcije za delo z lokacijskimi podatki.

V datoteki _[`gprahUtils.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/graphUtils.py)_ se nahajajo pomožne funkcije za risanje grafov.

V datoteki _[`helperUtils.py`](https://github.com/kkklemennn/Geocaching-COVID19/blob/main/code/analysis/helperUtils.py)_ se nahajajo pomožne funkcije za delo z datotekami.
