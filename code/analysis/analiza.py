import json
import ast
import datetime
import statistics

from pandas.core.indexes import base

import helperUtils
import GPSUtils
import graphUtils

from collections import Counter
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
import plotly.io as pio
pio.renderers.default = "vscode"

uporabniki_data = helperUtils.read_uporabniki()
zakladi_data = helperUtils.read_zakladi()
uporabniki_lokacije = helperUtils.read_uporabniki_lokacije()
zakladi_lokacije = helperUtils.read_zakladi_lokacije()


# Generiranje slovarjev statistike
def najdbe_po_letih():
    leta = {}   # - stevilo najdb po mesecih
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = zaklad["datumObiska"].split(".")
            mesec = datum[1]
            leto = datum[2]
            if leto not in leta:
                leta[leto] = {}
            if mesec in leta[leto]:
                leta[leto][mesec] += 1
            else:
                leta[leto][mesec] = 1
    ordered = {}
    for key in sorted(leta):
        meseci = [int(x) for x in sorted(leta[key])]
        meseci.sort()
        for key2 in meseci:
            if key not in ordered:
                ordered[key] = {}
            ordered[key][str(key2)] = leta[key][str(key2)]
    return ordered


def uporabniki_po_letih():
    leta = {}       # - stevilo najdb po uporabnikih za vsak mesec
    aktivni = {}    # - stevilo aktivnih uporabnikov v mescu
    for u in uporabniki_data:
        username = u["uporabniskoIme"]
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = zaklad["datumObiska"].split(".")
            mesec = datum[1]
            leto = datum[2]
            if leto not in leta:
                leta[leto] = {}
                aktivni[leto] = {}
            if mesec not in leta[leto]:
                leta[leto][mesec] = {}
                aktivni[leto][mesec] = 0
            if username not in leta[leto][mesec]:
                leta[leto][mesec][username] = 1
                aktivni[leto][mesec] += 1
            else:
                leta[leto][mesec][username] += 1

    ordered = {}
    for key in sorted(leta):
        meseci = [int(x) for x in sorted(leta[key])]
        meseci.sort()
        for key2 in meseci:
            if key not in ordered:
                ordered[key] = {}
            ordered[key][str(key2)] = leta[key][str(key2)]
    return ordered


# Shranjevanje statistike v JSON datoteke
def generiraj_statistiko():
    helperUtils.save_to_json(najdbe_po_letih(), 'najdbe_po_letih')
    helperUtils.save_to_json(uporabniki_po_letih(), 'uporabniki_najdbe_po_letih')


# Graf aktivnih uporabnikov: povprecje(2017-2019), 2020, 2021
def graf_aktivnih_po_letih_povp():
    uporabniki_po_letih = helperUtils.read_json("../../data/results/uporabniki_po_letih.json")
    # Izbrišemo nepopolno statistiko
    del uporabniki_po_letih['2021']['7']
    vsote = dict(Counter(uporabniki_po_letih['2017']) + Counter(uporabniki_po_letih['2018']) + Counter(uporabniki_po_letih['2019']))
    povprecje = {k: int(vsote[k] / float((k in uporabniki_po_letih['2017']) + (k in uporabniki_po_letih['2018']) + (k in uporabniki_po_letih['2019']))) for k in vsote}
    leta = {}
    leta["povp"] = povprecje
    leta["2020"] = uporabniki_po_letih["2020"]
    leta["2021"] = uporabniki_po_letih["2021"]
    # Wilcoxonov test: povprecje vs. 2020
    df = pd.DataFrame(leta)
    stat, p = wilcoxon(df['povp'], df['2020'])
    print("povp vs 2020 - stat:",stat,"p:",p)
    # Wilcoxonov test: povprecje mar-jan vs. mar2020-jan2021
    povp = df['povp'][2:]
    covid = df['2020'][2:]
    covid["1"] = int(df.loc["1",:]['2021'])
    povp["1"] = int(df.loc["1",:]['povp'])
    stat, p = wilcoxon(povp, covid)
    print("povp vs covid - stat:",stat,"p:",p)
    graphUtils.izrisi_leta_povp(leta, "Število aktivnih uporabnikov")


# Graf najdb po letih: povprecje(2017-2019), 2020, 2021 [graf_najdb_po_letih_s_povp]
def graf_najdb_po_letih_povp():
    najdbe_po_letih = helperUtils.read_json("../../data/results/najdbe_po_letih.json")
    
    del najdbe_po_letih['2021']['7']    # Izbrišemo nepopolno statistiko
    
    vsote = dict(Counter(najdbe_po_letih['2017']) + Counter(najdbe_po_letih['2018']) + Counter(najdbe_po_letih['2019']))
    povprecje = {k: int(vsote[k] / float((k in najdbe_po_letih['2017']) + (k in najdbe_po_letih['2018']) + (k in najdbe_po_letih['2019']))) for k in vsote}
    leta = {}
    leta["povp"] = povprecje
    leta["2020"] = najdbe_po_letih["2020"]
    leta["2021"] = najdbe_po_letih["2021"]
    df = pd.DataFrame(leta)
    # Wilcoxonov test: povprecje vs. 2020
    stat, p = wilcoxon(df['povp'], df['2020'])
    print("povp vs 2020 - stat:",stat,"p:",p)
    # Wilcoxonov test: povprecje do julija vs. 2021 do julija
    stat, p = wilcoxon(df['povp'][:6], df['2021'][:6])
    print("povp vs 2021 - stat:",stat,"p:",p)
    graphUtils.izrisi_leta_povp(leta, "Število najdb po letih")


# Graf najdb po letih
def graf_najdb_po_letih(od):
    najdbe_po_letih = helperUtils.read_json("../../data/results/najdbe_po_letih.json")
    del najdbe_po_letih['2021']['7']    # Izbrišemo nepopolno statistiko
    graphUtils.izrisi_leta(najdbe_po_letih, str(od), "Število najdb po letih")


# Graf aktivnih uporabnikov po letih
def graf_aktivnih_po_letih(od):
    uporabniki_po_letih = helperUtils.read_json("../../data/results/uporabniki_po_letih.json")
    del uporabniki_po_letih['2021']['7']    # Izbrišemo nepopolno statistiko
    graphUtils.izrisi_leta(uporabniki_po_letih, str(od), "Število aktivnih uporabnikov po letih")


# Graf aktivnosti igralcev: tujci vs. domačini po letih: povprecje(2017-2019), 2020, 2021
def aktivnost_tujci_domacini():
    leta = helperUtils.read_json("../../data/results/uporabniki_najdbe_po_letih.json")
    uporabniki_lokacije = helperUtils.read_json("../../data/processed/uporabniki_lokacije.json")
    aktivnost = {}
    aktivnost["2020"] = {}
    aktivnost["2020"]["domaci"] = {}
    aktivnost["2020"]["tujci"] = {}
    for mesec in leta["2020"]:
        aktivnost["2020"]["domaci"][mesec] = 0
        aktivnost["2020"]["tujci"][mesec] = 0
        for uporabnik in leta["2020"][mesec]:
            if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                aktivnost["2020"]["tujci"][mesec] += 1
            else:
                aktivnost["2020"]["domaci"][mesec] += 1
    aktivnost["2021"] = {}
    aktivnost["2021"]["domaci"] = {}
    aktivnost["2021"]["tujci"] = {}
    for mesec in leta["2021"]:
        aktivnost["2021"]["domaci"][mesec] = 0
        aktivnost["2021"]["tujci"][mesec] = 0
        for uporabnik in leta["2021"][mesec]:
            if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                aktivnost["2021"]["tujci"][mesec] += 1
            else:
                aktivnost["2021"]["domaci"][mesec] += 1
    del aktivnost['2021']["domaci"]['7']
    del aktivnost['2021']["tujci"]['7']
    aktivnost["povp"] = {}
    aktivnost["povp"]["domaci"] = {}
    aktivnost["povp"]["tujci"] = {}
    for i in range(2017,2020):
        for mesec in leta[str(i)]:
            if mesec not in aktivnost["povp"]["domaci"]:
                aktivnost["povp"]["domaci"][mesec] = 0
                aktivnost["povp"]["tujci"][mesec] = 0
            for uporabnik in leta[str(i)][mesec]:
                if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                    aktivnost["povp"]["tujci"][mesec] += 1
                else:
                    aktivnost["povp"]["domaci"][mesec] += 1
    for mesec in aktivnost["povp"]["domaci"]:
        aktivnost["povp"]["domaci"][mesec] = int(aktivnost["povp"]["domaci"][mesec]/3)
        aktivnost["povp"]["tujci"][mesec] = int(aktivnost["povp"]["tujci"][mesec]/3)
    graphUtils.izrisi_tujci_domaci(aktivnost, "Aktivnost domačih in tujih igralcev")


# Graf najdb igralcev: tujci vs. domačini po letih: povprecje(2017-2019), 2020, 2021 
def najdbe_tujci_domacini():
    leta = helperUtils.read_json("../../data/results/uporabniki_najdbe_po_letih.json")
    uporabniki_lokacije = helperUtils.read_json("../../data/processed/uporabniki_lokacije.json")
    aktivnost = {}
    aktivnost["2020"] = {}
    aktivnost["2020"]["domaci"] = {}
    aktivnost["2020"]["tujci"] = {}
    for mesec in leta["2020"]:
        aktivnost["2020"]["domaci"][mesec] = 0
        aktivnost["2020"]["tujci"][mesec] = 0
        for uporabnik in leta["2020"][mesec]:
            if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                aktivnost["2020"]["tujci"][mesec] += leta["2020"][mesec][uporabnik]
            else:
                aktivnost["2020"]["domaci"][mesec] += leta["2020"][mesec][uporabnik]
    aktivnost["2021"] = {}
    aktivnost["2021"]["domaci"] = {}
    aktivnost["2021"]["tujci"] = {}
    for mesec in leta["2021"]:
        aktivnost["2021"]["domaci"][mesec] = 0
        aktivnost["2021"]["tujci"][mesec] = 0
        for uporabnik in leta["2021"][mesec]:
            if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                aktivnost["2021"]["tujci"][mesec] += leta["2021"][mesec][uporabnik]
            else:
                aktivnost["2021"]["domaci"][mesec] += leta["2021"][mesec][uporabnik]
    del aktivnost['2021']["domaci"]['7']
    del aktivnost['2021']["tujci"]['7']
    aktivnost["povp"] = {}
    aktivnost["povp"]["domaci"] = {}
    aktivnost["povp"]["tujci"] = {}
    for i in range(2017,2020):
        for mesec in leta[str(i)]:
            if mesec not in aktivnost["povp"]["domaci"]:
                aktivnost["povp"]["domaci"][mesec] = 0
                aktivnost["povp"]["tujci"][mesec] = 0
            for uporabnik in leta[str(i)][mesec]:
                if (uporabniki_lokacije[uporabnik]["tujec"] == 1):
                    aktivnost["povp"]["tujci"][mesec] += leta[str(i)][mesec][uporabnik]
                else:
                    aktivnost["povp"]["domaci"][mesec] += leta[str(i)][mesec][uporabnik]
    for mesec in aktivnost["povp"]["domaci"]:
        aktivnost["povp"]["domaci"][mesec] = int(aktivnost["povp"]["domaci"][mesec]/3)
        aktivnost["povp"]["tujci"][mesec] = int(aktivnost["povp"]["tujci"][mesec]/3)
    graphUtils.izrisi_tujci_domaci(aktivnost, "Najdbe domačih in tujih igralcev")


# Primerjava stevila najdb s podatki Apple Mobility Trends
def apple_mobility_najdbe():
    # Pridobivanje števila najdb zakladov po datumih
    datumi = {}   # - stevilo najdb po mesecih
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in datumi:
                datumi[datum] = 1
            else:
                datumi[datum] += 1
    df = pd.DataFrame(datumi.items(), columns=['datum', 'stNajdb'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    df = df.loc[df.datum > pd.Timestamp(2020,1,12), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    df1 = helperUtils.read_apple_mobility()
    df1 = df1.iloc[:,6:]
    podatki = df1.T
    podatki.columns = ['driving', 'walking']
    podatki.index = pd.to_datetime(podatki.index)
    podatki = podatki.loc[podatki.index < pd.Timestamp(2021,7,1), ]
    podatki['stNajdb'] = df['stNajdb'].values
    graphUtils.izrisi_apple_mobility(podatki)


# Primerjava stevila aktivnih uporabnikov s podatki Apple Mobility Trends
def apple_mobility_aktivni():
    # Pridobivanje števila aktivnih zakladov po datumih
    leta = {}       # - stevilo najdb po uporabnikih za vsak mesec
    aktivni = {}    # - stevilo aktivnih uporabnikov v mescu
    for u in uporabniki_data:
        username = u["uporabniskoIme"]
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in leta:
                leta[datum] = {}
                aktivni[datum] = 0
            if username not in leta[datum]:
                leta[datum][username] = 1
                aktivni[datum] += 1
            else:
                leta[datum][username] += 1
    df = pd.DataFrame(aktivni.items(), columns=['datum', 'aktivni'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    df = df.loc[df.datum > pd.Timestamp(2020,1,12), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    df1 = helperUtils.read_apple_mobility()
    df1 = df1.iloc[:,6:]
    podatki = df1.T
    podatki.columns = ['driving', 'walking']
    podatki.index = pd.to_datetime(podatki.index)
    podatki = podatki.loc[podatki.index < pd.Timestamp(2021,7,1), ]
    podatki['aktivni'] = df['aktivni'].values
    smooth = pd.DataFrame()
    smooth['driving'] = podatki['driving'].ewm(span = 14).mean()
    smooth['walking'] = podatki['walking'].ewm(span = 14).mean()
    smooth['aktivni'] = podatki['aktivni'].ewm(span = 14).mean()
    graphUtils.izrisi_apple_mobility_smooth(podatki, smooth)
    korelacija = smooth.corr(method ='pearson')
    print('Tabela korelacij:')
    print(korelacija)


# Primerjava stevila najdb zakladov po razlicnih tipih (npr. traditional, mystery, ...)
# Opcijsko lahko dodamo argument normalize=True, ce zelimo normalizirati najdbe
def najdbe_po_tipih(**kwargs):
    normalize = kwargs.get('normalize', False)
    leta = {}
    for trenutni in zakladi_data:
        podrobnosti = open('../../data/downloaded/zakladi/' + str(trenutni['koda']) + '.json')
        zaklad = json.load(podrobnosti)
        logi = zaklad['dnevniskiZapisi']
        for log in logi:
            datum = helperUtils.parse_date(log['datumObiska'])
            datum = str(datum.year) + '-' + str(datum.month)
            if datum not in leta:
                leta[datum] = {}
            if zaklad['tip'] not in leta[datum]:
                leta[datum][zaklad['tip']] = 1
            else:
                leta[datum][zaklad['tip']] += 1
    # Normalizacija
    if (normalize):
        tipi = {}
        for z in zakladi_data:
            if z['tip'] not in tipi:
                tipi[z['tip']] = 1
            else:
                tipi[z['tip']] +=1
        for datum in leta:
            for tip in leta[datum]:
                leta[datum][tip] /= tipi[tip]
    df = pd.DataFrame(leta)
    df = df.T
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.loc[df.index > pd.Timestamp(2017,1,1), ]
    df = df.loc[df.index < pd.Timestamp(2021,7,1), ]
    graphUtils.izrisi_najdbe_po_tipih(df)


# UKREPI:
# 2020-03-20 - Prepoved gibanja izven občine prebivališča
# 2020-04-18 - Sproščanje prepovedi gibanja in pojasnila glede omejitev gibanja med občinami (vikendi).
# 2020-04-30 - Sprostitev gibanja izven občine prebivališča.
# 2020-10-16 - Omejitve za rdeče regije: gibanje izven regije, uporaba mask zunaj, prepoved določenih dejavnosti.
# 2020-10-20 - Rdeča tudi Goriška in Primorsko notranjska
# 2020-10-27 - Prepoved gibanja izven občine prebivališča.
# 2021-02-15 - Ukine se prepoved prehajanja med občinami ali regijaim
# 2021-03-26 - Omejitev gibanja na regijo v Obalno-kraški, Goriški in Koroški regiji
# 2021-04-23 - Odpravljena je omejitev gibanja na statistično regijo

# V katere obcine so v casu ukrepov hodili tujci
def prehajanje_obcin_tujci():
    tujci = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]
                    ulokacija = uporabniki_lokacije[u['uporabniskoIme']]
                    if (ulokacija['tujec'] == 1):
                        if (zlokacija['kraj'] not in tujci):
                            tujci[zlokacija['kraj']] = 1
                        else:
                            tujci[zlokacija['kraj']] += 1
    df = pd.DataFrame(tujci.items(), columns=['name', 'prehajanja'])
    print(df)
    graphUtils.map_prehajanja_obcine(df)


# V katere regije so v casu ukrepov hodili tujci
def prehajanje_regij_tujci():
    tujci = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2):
                #print(str(datum), zaklad['kodaZaklada'], u['uporabniskoIme'])
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]
                    ulokacija = uporabniki_lokacije[u['uporabniskoIme']]
                    if (ulokacija['tujec'] == 1):
                        if (zlokacija['regija'] not in tujci):
                            tujci[zlokacija['regija']] = 1
                        else:
                            tujci[zlokacija['regija']] += 1
    df = pd.DataFrame(tujci.items(), columns=['name', 'prehajanja'])
    print(df)
    graphUtils.map_prehajanja_regije(df)


# V katere obcine so v casu ukrepov domacini hodili iskat zaklade
def map_prehajanja_najdbe():
    obisk = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,4,18) and datum < datetime.date(2020,4,30) and datum.weekday() < 5)
            condition3 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2 or condition3):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    if (uporabniki_lokacije[u['uporabniskoIme']]['tujec'] == 0):
                        zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]['kraj']
                        ulokacija = uporabniki_lokacije[u['uporabniskoIme']]['kraj']
                        if (ulokacija.lower() != zlokacija.lower()):
                            if (zlokacija not in obisk):
                                obisk[zlokacija] = 1
                            else:
                                obisk[zlokacija] += 1
    df = pd.DataFrame(obisk.items(), columns=['name', 'število prehajanj'])
    df = df.sort_values('število prehajanj')
    graphUtils.map_prehajanja_obcine(df)


# Prehajanje obcin/regij, kjer se za eno krsitev steje en igralni dan
# po barvah so locena obmocja iz katerih so igralci doma
def map_prehajanja_krsitev_dan():
    up_kraji = {}
    up_regije = {}
    odatum = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,4,18) and datum < datetime.date(2020,4,30) and datum.weekday() < 5)
            condition3 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2 or condition3):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    if (uporabniki_lokacije[u['uporabniskoIme']]['tujec'] == 0):
                        zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]['kraj']
                        ulokacija = uporabniki_lokacije[u['uporabniskoIme']]['kraj']
                        if (ulokacija.lower() != zlokacija.lower()):
                            if (datum not in odatum):
                                odatum[datum] = []
                            if (u['uporabniskoIme'] not in odatum[datum]):
                                odatum[datum].append(u['uporabniskoIme'])
    for d in odatum:
        for u in odatum[d]:
            kraj = uporabniki_lokacije[u]['kraj'].capitalize()
            regija = uporabniki_lokacije[u]['regija']
            if (kraj not in up_kraji):
                up_kraji[kraj] = 1
            else:
                up_kraji[kraj] +=1
            if (regija not in up_regije):
                up_regije[regija] = 1
            else:
                up_regije[regija] +=1
    
    # Za obcine
    df = pd.DataFrame(up_kraji.items(), columns=['name', 'število prehajanj'])
    df = df.sort_values('število prehajanj')
    graphUtils.map_prehajanja_obcine(df)
    '''
    # Za regije
    df2 = pd.DataFrame(up_regije.items(), columns=['name', 'število prehajanj'])
    df2 = df2.sort_values('število prehajanj')
    graphUtils.map_prehajanja_regije(df2)
    '''


# Prehajanje obcin/regij, kjer stejemo le stevilo igralcev, ki je kadarkoli vsaj enkrat
# krsilo ukrepe, po barvah so locena obmocja iz katerih so igralci doma
def map_prehajanja_krsitev_igralci():
    up_kraji = {}
    up_regije = {}
    igralci = []
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,4,18) and datum < datetime.date(2020,4,30) and datum.weekday() < 5)
            condition3 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2 or condition3):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    if (uporabniki_lokacije[u['uporabniskoIme']]['tujec'] == 0):
                        zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]['kraj']
                        ulokacija = uporabniki_lokacije[u['uporabniskoIme']]['kraj']
                        if (ulokacija.lower() != zlokacija.lower()):
                            if (u['uporabniskoIme'] not in igralci):
                                igralci.append(u['uporabniskoIme'])
    for u in igralci:
        kraj = uporabniki_lokacije[u]['kraj'].capitalize()
        regija = uporabniki_lokacije[u]['regija']
        if (kraj not in up_kraji):
            up_kraji[kraj] = 1
        else:
            up_kraji[kraj] +=1
        if (regija not in up_regije):
            up_regije[regija] = 1
        else:
            up_regije[regija] +=1
    
    # Za obcine
    df = pd.DataFrame(up_kraji.items(), columns=['name', 'število prehajanj'])
    df = df.sort_values('število prehajanj')
    graphUtils.map_prehajanja_obcine(df)
    '''
    # Za regije
    df2 = pd.DataFrame(up_regije.items(), columns=['name', 'število prehajanj'])
    df2 = df2.sort_values('število prehajanj')
    graphUtils.map_prehajanja_regije(df2)
    '''

# Katere so top relacije, iz kje in kam so igralci hodili v casu ukrepov
def relacije_prehajanj():
    obiski = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,4,18) and datum < datetime.date(2020,4,30) and datum.weekday() < 5)
            condition3 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2 or condition3):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    if (uporabniki_lokacije[u['uporabniskoIme']]['tujec'] == 0):
                        zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]['kraj']
                        ulokacija = uporabniki_lokacije[u['uporabniskoIme']]['kraj']
                        if (ulokacija.lower() != zlokacija.lower()):
                            obisk = str(ulokacija.capitalize()+'->'+zlokacija)
                            if (obisk not in obiski):
                                obiski[obisk] = 1
                            else:
                                obiski[obisk] +=1
    df = pd.DataFrame(obiski.items(), columns=['name', 'prehajanja'])
    df = df.sort_values('prehajanja',ascending=False)
    print(df[:15])


# Prehajanje obcin in regij normalizirano (deljeno s stevilom igralcev v obcini/regiji)
def prehajanja_igralci_normal():
    up_regije = {}
    up_kraji = {}
    igralci = []
    lokacije = {}
    lokacijek = {}
    for u in uporabniki_lokacije:
        trenutni = uporabniki_lokacije[u]
        if (trenutni['tujec'] == 0):
            if (trenutni['regija'] not in lokacije):
                lokacije[trenutni['regija']] = 1
            else:
                lokacije[trenutni['regija']] +=1
            if (trenutni['kraj'] not in lokacijek):
                lokacijek[trenutni['kraj']] = 1
            else:
                lokacijek[trenutni['kraj']] +=1
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = helperUtils.parse_date(zaklad['datumObiska'])
            condition1 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,4,30))
            condition2 = (datum > datetime.date(2020,4,18) and datum < datetime.date(2020,4,30) and datum.weekday() < 5)
            condition3 = (datum > datetime.date(2020,10,27) and datum < datetime.date(2021,2,15))
            if(condition1 or condition2 or condition3):
                if (zaklad['kodaZaklada'] in zakladi_lokacije):
                    if (uporabniki_lokacije[u['uporabniskoIme']]['tujec'] == 0):
                        zlokacija = zakladi_lokacije[zaklad['kodaZaklada']]['kraj']
                        ulokacija = uporabniki_lokacije[u['uporabniskoIme']]['kraj']
                        if (ulokacija.lower() != zlokacija.lower()):
                            if (u['uporabniskoIme'] not in igralci):
                                igralci.append(u['uporabniskoIme'])
    for u in igralci:
        regija = uporabniki_lokacije[u]['regija']
        kraj = uporabniki_lokacije[u]['kraj']
        if (regija not in up_regije):
            up_regije[regija] = 1
        else:
            up_regije[regija] +=1
        if (kraj not in up_kraji):
            up_kraji[kraj] = 1
        else:
            up_kraji[kraj] +=1
    normal = {}
    normalk = {}
    for regija in up_regije:
        normal[regija] = (up_regije[regija] / lokacije[regija]) * 100
    for kraj in up_kraji:
        normalk[kraj] = (up_kraji[kraj] / lokacijek[kraj]) * 100

    df = pd.DataFrame(normal.items(), columns=['name', 'prehajanja'])
    df = df.sort_values('prehajanja')
    dfk = pd.DataFrame(normalk.items(), columns=['name', 'prehajanja'])
    dfk = dfk.sort_values('prehajanja')
    graphUtils.map_prehajanja_regije_normal(df)
    #graphUtils.map_prehajanja_obcine_normal(dfk)


# Stetje velikosti skupin in prikaz skupin s pripadajocim stevilom najdb za casa covid in pred njim
def skupine_in_velikosti():
    df = pd.read_csv('../../data/processed/skupine.csv')
    velikost_skupin = {}
    for index, row in df.iterrows():
        skupina = row['skupina']
        skupina = set(ast.literal_eval(skupina))
        if len(skupina) not in velikost_skupin:
            velikost_skupin[len(skupina)] = 1
        else:
            velikost_skupin[len(skupina)] +=1
        print(row['skupina'], row['covid'], row['pred'])
    graphUtils.trendSkupin(df)
    print('-----------------')
    print('Velikosti skupin:')
    print(json.dumps(velikost_skupin, indent=4))
    print('-----------------')


# Dolocanje lokacije skupin
def lokacije_skupin():
    df = pd.read_csv('../../data/processed/skupine.csv')
    lokacije = {}
    for index, row in df.iterrows():
        skupina = row['skupina']
        skupina = set(ast.literal_eval(skupina))
        trenutna = {}
        for igralec in skupina:
            regija = uporabniki_lokacije[igralec]['regija']
            if regija not in trenutna:
                trenutna[regija] = 1
            else:
                trenutna[regija] +=1
        # Ce je skupina sestavljena iz igralcev iz vec regij
        if (len(trenutna) > 1):
            # Pogledamo ce je 50-50 in takih regij ne upostevamo
            razlicne = all(value == trenutna[regija] for value in trenutna.values())
            if (razlicne):
                regijafinal = None
                if 'Različne' not in lokacije:
                    lokacije['Različne'] = 1
                else:
                    lokacije['Različne'] +=1
            # Najdemo regijo z vecinskim delezem
            else:
                regijafinal = max(trenutna, key=trenutna.get)
        else:
            regijafinal = regija 
        if regijafinal is not None:
            if regijafinal not in lokacije:
                lokacije[regijafinal] = 1
            else:
                lokacije[regijafinal] +=1
    df = pd.DataFrame(lokacije.items(), columns=['name', 'število skupin'])
    df = df.sort_values('število skupin',ascending=False)
    graphUtils.map_skupine_regije(df)
    print(df)


# Kako je vpliv potrjenih primerov in cepljenja vplival na stevilo najdb
def potrjeni_primeri_najdbe():
    df = pd.read_csv('../../data/raw/COVID-19_Sledilnik/stats.csv')
    potrjeni = pd.DataFrame()
    potrjeni['date'] = df['date']
    potrjeni['cases.confirmed'] = df['cases.confirmed'].ewm(span = 14).mean()
    potrjeni['cepljeni'] = (df['vaccination.administered.todate']/1000)
    potrjeni.date = pd.to_datetime(potrjeni.date)
    potrjeni = potrjeni.loc[potrjeni.date > pd.Timestamp(2020,3,23), ]
    potrjeni = potrjeni.loc[potrjeni.date < pd.Timestamp(2021,7,1), ]
    datumi = {}
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in datumi:
                datumi[datum] = 1
            else:
                datumi[datum] += 1
    df = pd.DataFrame(datumi.items(), columns=['datum', 'stNajdb'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    df = df.loc[df.datum > pd.Timestamp(2020,3,23), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    potrjeni['stNajdb'] = df['stNajdb'].values
    potrjeni['stNajdb'] = potrjeni['stNajdb'].ewm(span = 14).mean()
    graphUtils.izrisi_covid_sledilnik_najdbe(potrjeni)
    korelacija = potrjeni.corr(method ='pearson')
    print('Tabela korelacij:')
    print(korelacija)

# Kako je vpliv potrjenih primerov in cepljenja vplival na stevilo aktivnih
def potrjeni_primeri_aktivni():
    df = pd.read_csv('../../data/raw/COVID-19_Sledilnik/stats.csv')
    potrjeni = pd.DataFrame()
    aktivni = pd.DataFrame()
    potrjeni['date'] = df['date']
    potrjeni['cases.confirmed'] = (df['cases.confirmed']/10).ewm(span = 30).mean()
    potrjeni.date = pd.to_datetime(potrjeni.date)
    potrjeni = potrjeni.loc[potrjeni.date > pd.Timestamp(2020,3,23), ]
    potrjeni = potrjeni.loc[potrjeni.date < pd.Timestamp(2021,7,1), ]
    # Pridobivanje števila aktivnih zakladov po datumih
    leta = {}       # - stevilo najdb po uporabnikih za vsak mesec
    aktivni = {}    # - stevilo aktivnih uporabnikov v mescu
    for u in uporabniki_data:
        username = u["uporabniskoIme"]
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in leta:
                leta[datum] = {}
                aktivni[datum] = 0
            if username not in leta[datum]:
                leta[datum][username] = 1
                aktivni[datum] += 1
            else:
                leta[datum][username] += 1
    df = pd.DataFrame(aktivni.items(), columns=['datum', 'aktivni'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    df = df.loc[df.datum > pd.Timestamp(2020,3,23), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    potrjeni['aktivni'] = df['aktivni'].values
    potrjeni['aktivni'] = potrjeni['aktivni'].ewm(span = 30).mean()
    graphUtils.izrisi_covid_sledilnik_aktivni(potrjeni)


# Primerjava Google Mobility Trends z najdbami
def google_mobility_najdbe():
    # Pridobivanje števila najdb zakladov po datumih
    datumi = {}   # - stevilo najdb po mesecih
    for u in uporabniki_data:
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in datumi:
                datumi[datum] = 1
            else:
                datumi[datum] += 1
    df = pd.DataFrame(datumi.items(), columns=['datum', 'stNajdb'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    dfbase = df.loc[df.datum < pd.Timestamp(2020,2,7), ]
    dfbase = dfbase.loc[dfbase.datum > pd.Timestamp(2020,1,2), ]
    df = df.loc[df.datum > pd.Timestamp(2020,2,14), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    # The baseline is the median value, for the corresponding day of the week, during the 5-week period Jan 3–Feb 6, 2020.
    # Torej ce je trenutni dan ponedeljek, vzamemo za baseline median value vseh ponedeljkov Jan 3–Feb 6, 2020
    # Najprej izracunamo izhodisce
    baseline = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for index, row in dfbase.iterrows():
        #print(row['datum'].dayofweek)
        day = row['datum'].dayofweek
        baseline[day].append(row['stNajdb'])
    for day in baseline:
        baseline[day] = statistics.median(baseline[day])
    # Racunanje procentualne spremembe z izhodicem
    sprememba = {}
    for index, row in df.iterrows():
        day = row['datum'].dayofweek
        change = (row['stNajdb']*100/baseline[day])-100
        datum = str(row['datum'].year) + '-' + str(row['datum'].month) + '-' + str(row['datum'].day)
        sprememba[datum] = change
    spr = pd.DataFrame(sprememba.items(), columns=['datum', 'stNajdb'])
    # Branje podatkov
    podatki = helperUtils.read_google_mobility()
    podatki.index = pd.to_datetime(podatki.index)
    podatki = podatki.loc[podatki.index < pd.Timestamp(2021,7,1), ]
    podatki['stNajdb'] = spr['stNajdb'].values
    # Smoothing
    podatki = podatki.ewm(span = 14).mean()
    # Izris
    graphUtils.izrisi_google_mobility(podatki)
    # Korelacija
    korelacija = podatki.corr(method ='pearson')
    print('Korelacije s stevilom najdb:')
    print(korelacija['stNajdb'])


# Primerjava Google Mobility Trends z aktivnimi igralci
def google_mobility_aktivni():
    # Pridobivanje števila aktivnih zakladov po datumih
    leta = {}       # - stevilo najdb po uporabnikih za vsak mesec
    aktivni = {}    # - stevilo aktivnih uporabnikov v mescu
    for u in uporabniki_data:
        username = u["uporabniskoIme"]
        for zaklad in u["seznamNajdenihZnotrajDrzave"]:
            datum = str(helperUtils.parse_date(zaklad['datumObiska']))
            if datum not in leta:
                leta[datum] = {}
                aktivni[datum] = 0
            if username not in leta[datum]:
                leta[datum][username] = 1
                aktivni[datum] += 1
            else:
                leta[datum][username] += 1
    df = pd.DataFrame(aktivni.items(), columns=['datum', 'aktivni'])
    df['datum'] = pd.to_datetime(df.datum)
    df = df.sort_values(by=['datum'])
    dfbase = df.loc[df.datum < pd.Timestamp(2020,2,7), ]
    dfbase = dfbase.loc[dfbase.datum > pd.Timestamp(2020,1,2), ]
    df = df.loc[df.datum > pd.Timestamp(2020,2,14), ]
    df = df.loc[df.datum < pd.Timestamp(2021,7,1), ]
    # The baseline is the median value, for the corresponding day of the week, during the 5-week period Jan 3–Feb 6, 2020.
    # Najprej izracunamo izhodisce
    baseline = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for index, row in dfbase.iterrows():
        #print(row['datum'].dayofweek)
        day = row['datum'].dayofweek
        baseline[day].append(row['aktivni'])
    for day in baseline:
        baseline[day] = statistics.median(baseline[day])
    # Racunanje procentualne spremembe z izhodicem
    sprememba = {}
    for index, row in df.iterrows():
        day = row['datum'].dayofweek
        change = (row['aktivni']*100/baseline[day])-100
        datum = str(row['datum'].year) + '-' + str(row['datum'].month) + '-' + str(row['datum'].day)
        sprememba[datum] = change
    spr = pd.DataFrame(sprememba.items(), columns=['datum', 'aktivni'])
    # Branje podatkov
    podatki = helperUtils.read_google_mobility()
    podatki.index = pd.to_datetime(podatki.index)
    podatki = podatki.loc[podatki.index < pd.Timestamp(2021,7,1), ]
    podatki['aktivni'] = spr['aktivni'].values
    # Smoothing
    podatki = podatki.ewm(span = 14).mean()
    # Izris
    graphUtils.izrisi_google_mobility_aktivni(podatki)
    # Korelacija
    korelacija = podatki.corr(method ='pearson')
    print('Korelacije s stevilom aktivnih igralcev:')
    print(korelacija['aktivni'])

