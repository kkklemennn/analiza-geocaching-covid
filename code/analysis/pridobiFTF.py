# Pridobivanje vseh FTF-jev uporabnikov

import json
import helperUtils

vsi = helperUtils.read_uporabniki()

ftfs = {}

for trenutni in vsi:
    podrobnosti = open('data/zakladi/' + str(trenutni['koda']) + '.json')
    zaklad = json.load(podrobnosti)
    trenutni = len(zaklad['dnevniskiZapisi'])-1
    log = zaklad['dnevniskiZapisi'][trenutni]
    ftf = False
    while (log['tip'] != 'Found it'):
        trenutni -= 1
        if (trenutni < 0):
            ftf = True
            break
        log = zaklad['dnevniskiZapisi'][trenutni]
    prvi_datum = log['datumObiska']
    
    if (not ftf):
        while (trenutni >= 0):
            log = zaklad['dnevniskiZapisi'][trenutni]
            if (log['datumObiska'] != prvi_datum):
                break
            if (log['tip'] == 'Found it'): # lahko da je owner updatal koordinate, ali pa da je potekala debata v write note
                user = log['avtorZapisa']['uporabniskoIme']
                if user not in ftfs:
                    ftfs[user] = []
                trenutniZaklad = {}
                trenutniZaklad['koda'] = zaklad['koda']
                trenutniZaklad['lat'] = zaklad['lokacija']['lat']
                trenutniZaklad['lon'] = zaklad['lokacija']['lon']
                trenutniZaklad['datum'] = prvi_datum
                ftfs[user].append(trenutniZaklad)
            trenutni-=1

helperUtils.save_to_json(ftfs, "ftfs") 
