import datetime
from scipy.stats import wilcoxon
import pandas as pd
import json

import graphUtils
import helperUtils

uporabniki_data = helperUtils.read_uporabniki()
zakladi_data = helperUtils.read_zakladi()
uporabniki_lokacije = helperUtils.read_uporabniki_lokacije()
zakladi_lokacije = helperUtils.read_zakladi_lokacije()

# Stevilo igralcev po regijah od 2017
def stevilo_igralcev_po_regijah():
    lokacije = {}
    for u in uporabniki_data:
        username = u['uporabniskoIme']
        seznamNajdenih = u['seznamNajdenihZnotrajDrzave']
        for zaklad in seznamNajdenih:
            zaklad['datumObiska'] = helperUtils.parse_date(zaklad['datumObiska'])
        seznamNajdenih.sort(key=lambda item:item['datumObiska'])
        zadnji = len(seznamNajdenih)-1
        if seznamNajdenih[zadnji]['datumObiska'] >= datetime.date(2017,1,1):
            if uporabniki_lokacije[username]['tujec'] == 0:
                if (uporabniki_lokacije[username]['regija'] not in lokacije):
                    lokacije[uporabniki_lokacije[username]['regija']] = 1
                else:
                    lokacije[uporabniki_lokacije[username]['regija']] +=1
    df = pd.DataFrame(lokacije.items(), columns=['Regija', 'stIgralcev'])
    df = df.sort_values('stIgralcev',ascending=False)
    print(df)
    print(df.sum())

# Stevilo zakladov po regijah
def stevilo_zakladov_po_regijah():
    lokacije = {}
    for z in zakladi_lokacije:
        trenutni = zakladi_lokacije[z]
        if trenutni['regija'] not in lokacije:
            lokacije[trenutni['regija']] = 1
        else:
            lokacije[trenutni['regija']] +=1
    df = pd.DataFrame(lokacije.items(), columns=['Regija', 'stZakladov'])
    df = df.sort_values('stZakladov',ascending=False)
    print(df)
    print(df.sum())

# Stevilo zakladov po tipih
def stevilo_zakladov_po_tipih():
    tipi = {}
    for z in zakladi_data:
        if (z['koda'] in zakladi_lokacije):
            if z['tip'] not in tipi:
                tipi[z['tip']] = 1
            else:
                tipi[z['tip']] +=1
    df = pd.DataFrame(tipi.items(), columns=['Tip', 'stZakladov'])
    df = df.sort_values('stZakladov',ascending=False)
    print(df)
    print(df.sum())

def stevilo_eventov():
    # Podatkov o eventih se ne da dobiti na Geocaching, ker so arhivirani
    # Podatki so bili pridobljeni na:
    # https://project-gc.com/Maps/mapcompare/?profile_name=kkklemennn&country=Slovenia&nonefound=on&ownfound=on&hidden_fromyyyy=2020&hidden_frommm=1&hidden_fromdd=1&hidden_toyyyy=2021&hidden_tomm=1&hidden_todd=11&type%5B%5D=Event+Cache&showarchived=on&submit=Filter
    events17 = {
        "01": 2,"02": 1,"03": 3,"04": 9,"05": 3,"06": 4,"07": 10,"08": 5,"09": 3,"10": 2,"11": 3,"12": 5
    }
    events18 = {
        "01": 4,"02": 1,"03": 3,"04": 3,"05": 3,"06": 7,"07": 9,"08": 6,"09": 4,"10": 2,"11": 3,"12": 5
    }
    events19 = {
        "01": 11,"02": 3,"03": 4,"04": 6,"05": 7,"06": 2,"07": 3,"08": 5,"09": 4,"10": 4,"11": 4,"12": 5
    }
    events20 = {
        "01": 6,"02": 4,"03": 1,"04": 0,"05": 1,"06": 1,"07": 1,"08": 3,"09": 0,"10": 0,"11": 0,"12": 0
    }
    events21 = {
        "01": 0,"02": 0,"03": 0,"04": 0,"05": 1,"06": 2
    }
    df17 = pd.DataFrame(events17.items())
    df18 = pd.DataFrame(events18.items())
    df19 = pd.DataFrame(events19.items())
    df20 = pd.DataFrame(events20.items())
    df21 = pd.DataFrame(events21.items())

    povp = df17
    povp = (povp[1] + df18[1] + df19[1])/3
    stat, p = wilcoxon(povp, df20[1])
    print("povp vs 2020 - stat:",stat,"p:",p)
    graphUtils.izrisi_evente(df17, df18, df19, df20, df21)

# Stevilo domacih in tujih igralcev, ki so bili aktivni v casu od 2017
def stevilo_domaci_tujci():
    lokacije = {
        'domaci': 0,
        'tujci': 0
    }
    for u in uporabniki_data:
        username = u['uporabniskoIme']
        seznamNajdenih = u['seznamNajdenihZnotrajDrzave']
        for zaklad in seznamNajdenih:
            zaklad['datumObiska'] = helperUtils.parse_date(zaklad['datumObiska'])
        seznamNajdenih.sort(key=lambda item:item['datumObiska'])
        zadnji = len(seznamNajdenih)-1
        if seznamNajdenih[zadnji]['datumObiska'] >= datetime.date(2017,1,1):
            if uporabniki_lokacije[username]['tujec'] == 0:
                lokacije['domaci'] += 1
            else:
                lokacije['tujci'] += 1
    print(lokacije)

# Stevilo vseh analiziranih dnevniskih zapisov
def stevilo_dnevniskih_zapisov():
    stZapisov = 0
    for trenutni in zakladi_data:
        podrobnosti = open('../../data/downloaded/zakladi/' + str(trenutni['koda']) + '.json')
        zaklad = json.load(podrobnosti)
        logi = zaklad['dnevniskiZapisi']
        for log in logi:
            datumObiska = helperUtils.parse_date(log['datumObiska'])
            if (datumObiska >= datetime.date(2017,1,1)):
                stZapisov += 1
    print(stZapisov)
        