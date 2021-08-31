import datetime
import json
import pandas as pd
import ast
import helperUtils


uporabniki_data = helperUtils.read_uporabniki()
zakladi_data = helperUtils.read_zakladi()
uporabniki_lokacije = helperUtils.read_uporabniki_lokacije()
zakladi_lokacije = helperUtils.read_zakladi_lokacije()

skupinevse = []

# Razdeli skupino ki je iskala v enem dnevu v vse podskupine
def dan_v_skupine(fullset):
    listrep = list(fullset)
    n = len(listrep)
    return [[listrep[k] for k in range(n) if i&1<<k] for i in range(2**n)]

# UKREPI:
# 2020-03-20 - Prepoved zbiranja na javnih mestih
# 2020-05-15 - Sprostitev zbiranja do 50 ljudi	
# 2020-11-13 - Prepovedano zbiranje ljudi (razen za ožje družinske člane in člane istega gospodinjstva)
# 2021-02-15 - Dovoljeno je zbiranje do 10 ljudi
# 2021-04-01 - Prepovedano je zbiranje ljudi, slavja, shodi, poroke, praznovanja.
# 2021-04-23 - Dovoljeno je zbiranje do 10 ljudi

# Najdemo vse skupine od 2017 ko je bilo zbiranje dovoljeno
for trenutni in zakladi_data:
    podrobnosti = open('../../data/downloaded/zakladi/' + str(trenutni['koda']) + '.json')
    zaklad = json.load(podrobnosti)
    logi = zaklad['dnevniskiZapisi']
    datumi = {}
    for log in logi:
        datum = helperUtils.parse_date(log['datumObiska'])
        condition1 = (datum >= datetime.date(2017,1,1))
        condition2 = (datum < datetime.date(2020,3,20) or datum > datetime.date(2020,5,15))
        condition3 = (datum < datetime.date(2020,11,13) or datum > datetime.date(2021,2,15))
        condition4 = (datum < datetime.date(2021,4,1) or datum > datetime.date(2021,4,23))
        if (condition1 and condition2 and condition3 and condition4):
            user = log['avtorZapisa']['uporabniskoIme']
            if (log['tip'] == 'Found it' and uporabniki_lokacije[user]['tujec'] == 0):
                datum = str(datum.year) + '-' + str(datum.month) + '-' +str(datum.day)
                if datum not in datumi:
                    datumi[datum] = []
                if user not in datumi[datum]:
                    datumi[datum].append(user)
    for d in datumi:
        trenutni = set(datumi[d])
        if (len(trenutni) > 1):
            if trenutni not in skupinevse:
                skupinevse.append(trenutni)

# Najdemo vse skupine skupaj s podskupinami v casu COVID-19 ko je bilo zbiranje prepovedano
ponavljanja = {}
for trenutni in zakladi_data:
    podrobnosti = open('../../data/downloaded/zakladi/' + str(trenutni['koda']) + '.json')
    zaklad = json.load(podrobnosti)
    logi = zaklad['dnevniskiZapisi']
    datumi = {}
    for log in logi:
        datum = helperUtils.parse_date(log['datumObiska'])
        condition2 = (datum > datetime.date(2020,3,20) and datum < datetime.date(2020,5,15))
        condition3 = (datum > datetime.date(2020,11,13) and datum < datetime.date(2021,2,15))
        condition4 = (datum > datetime.date(2021,4,1) and datum < datetime.date(2021,4,23))
        user = log['avtorZapisa']['uporabniskoIme']
        if (condition2 or condition3 or condition4):
            if (log['tip'] == 'Found it' and uporabniki_lokacije[user]['tujec'] == 0):
                datum = str(datum.year) + '-' + str(datum.month) + '-' +str(datum.day)
                if datum not in datumi:
                    datumi[datum] = []
                if user not in datumi[datum]:
                    datumi[datum].append(user)
    for d in datumi:
        trenutni = set(datumi[d])
        zdaj = dan_v_skupine(trenutni)
        for z in zdaj:
            z=set(sorted(z))
            if(len(z) > 1):
                if str(sorted(z)) not in ponavljanja:
                    ponavljanja[str(sorted(z))] = {}
                    ponavljanja[str(sorted(z))]['covid'] = 1
                else:
                    ponavljanja[str(sorted(z))]['covid'] +=1

# Iscemo ce so skupine za casa covid iskale skupaj tudi pred covidom
for skupinapred in ponavljanja:
    skupinapred = set(ast.literal_eval(skupinapred))
    for skupina in skupinevse:
        if (skupinapred.issubset(skupina)):
            if 'pred' not in ponavljanja[str(sorted(skupinapred))]:
                ponavljanja[str(sorted(skupinapred))]['pred'] = 1
            else:
                ponavljanja[str(sorted(skupinapred))]['pred'] +=1


skupine = pd.DataFrame(ponavljanja).T
skupine = skupine.sort_values(['covid', 'pred'], ascending=[False, False])

skupine = skupine[skupine['covid'] > 2]
skupine = skupine[skupine['pred'] > 2]

# Razdelitev vseh skupin s podskupinami na prave skupine
zbiranja = {}
for index, row in skupine.iterrows():
    skupina = row.name
    skupina = set(ast.literal_eval(skupina))
    if (str(sorted(skupina)) not in zbiranja):
        zbiranja[str(sorted(skupina))] = {}
        zbiranja[str(sorted(skupina))]['covid'] = row['covid']
        zbiranja[str(sorted(skupina))]['pred'] = row['pred']
        zbiranja[str(sorted(skupina))]['nadskupina'] = 0
    if (len(skupina) > 2):
        for s in zbiranja:
            s = set(ast.literal_eval(s))
            if (s == skupina):
                break
            if (s.issubset(skupina) and (zbiranja[str(sorted(s))]['nadskupina']==0) and (len(s)==len(skupina)-1)):
                zbiranja[str(sorted(s))]['covid'] -= row['covid']
                #zbiranja[str(sorted(s))]['pred'] -= row['pred']
                zbiranja[str(sorted(s))]['nadskupina'] =1

df = pd.DataFrame(zbiranja).T
df.index.name = 'skupina'
df = df.sort_values(['covid', 'pred'], ascending=[False, False])
df = df[df['covid'] > 4]
df.pop('nadskupina')
df.to_csv('../../data/processed/skupine.csv')
