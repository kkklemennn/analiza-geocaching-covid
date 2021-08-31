# Razvrsti zaklade v obcine in regije

import json

import helperUtils
import GPSUtils

zakladi_data = helperUtils.read_zakladi()

obcine = helperUtils.read_obcine()
regije = helperUtils.read_regije()
obcine_list = helperUtils.get_obcine_list()

def isci_kraj(kraj):
    lokacija = {}
    for regija in obcine_list:
        if kraj.lower() in map(str.lower,obcine_list[regija]):
            lokacija['kraj'] = kraj
            lokacija['regija'] = regija
            break
    return lokacija

zakladi_lokacije = {}
ignore = ['Community Celebration Event', 'Event', 'Mega-Event']

for trenutni in zakladi_data:
    podrobnosti = open('../../data/downloaded/zakladi/' + str(trenutni['koda']) + '.json')
    zaklad = json.load(podrobnosti)
    lokacija = zaklad['lokacija']
    if (trenutni['tip'] not in ignore):
        kraj = GPSUtils.get_obcina(lokacija['lon'], lokacija['lat'])
        if kraj != None:
            lokacija = isci_kraj(kraj)
            zakladi_lokacije[trenutni['koda']] = lokacija
        else:
            print("Napaka:",trenutni['koda'], trenutni['ime'])
        
helperUtils.save_to_json(zakladi_lokacije, "zakladi_lokacije")