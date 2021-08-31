import json
import re

import helperUtils
import GPSUtils

zakladi_data = helperUtils.read_zakladi()
uporabniki_data = helperUtils.read_uporabniki()
obcine_list = helperUtils.get_obcine_list()
vsi = helperUtils.read_uporabniki()
obcine = helperUtils.read_obcine()
mesta = helperUtils.read_mesta()
regije = helperUtils.read_regije()
ftfs = helperUtils.read_ftfs()

# Pridobi skrite zaklade uporabnika
def get_skriti(uporabnik):
    skriti = []
    for zaklad in zakladi_data:
        if (zaklad["lastnik"][3:] == uporabnik):
            if (zaklad["koda"] not in skriti):
                trenutni = {}
                trenutni['koda'] = zaklad['koda']
                for u in uporabniki_data:
                    for z in u["seznamNajdenihZnotrajDrzave"]:
                        if (z["kodaZaklada"] == zaklad["koda"]):
                            trenutni["lat"] = z["lokacija"]["lat"]
                            trenutni["lon"] = z["lokacija"]["lon"]
                            trenutni["datum"] = zaklad["datumPostavitve"]
                            skriti.append(trenutni)
                            break
                    else:
                        continue
                    break
    return skriti

# Poisce ali obstaja kraj in mu dodeli regijo
def isci_kraj(kraj):
    lokacija = {}
    for regija in obcine_list:
        if kraj.lower() in map(str.lower,obcine_list[regija]):
            lokacija['kraj'] = kraj
            lokacija['regija'] = regija
            lokacija['tujec'] = 0
            break
    return lokacija

uporabniki_lokacije = {}

# Gre cez vse uporabnike, jih klasificira domaci/tujci
# ter doloci kraj in regijo
for trenutni in vsi:
    lokacija_uporabnika = {}
    podrobnosti = open('data/uporabniki/' + str(trenutni['id']) + '.json')
    uporabnik = json.load(podrobnosti)
    
    # Ce ima uporabnik na platformi podano lokacijo
    if ('lokacija' in uporabnik):
        # Primeri:
        # 1) 5r: Maribor, Slovenia
        # 2) JozeB1: N 46°40.670 E 015°59.660
        # 3) MIGT: Ljubljana/Slovenija
        # 4) kerschbach: Slovenia (EU) - Črešnjevec, Slov. Bistrica
        # 5) kkklemennn: Murska Sobota
        # 6) kamijaha: Slovenia
        # Primer 1)
        if (',' in str(uporabnik['lokacija'])):
            lokacija = uporabnik['lokacija'].split(",")
            lokacija = [l.strip().lower() for l in lokacija]
            for l in lokacija:
                lokacija_uporabnika = isci_kraj(l)
                if (bool(lokacija_uporabnika)): break
            if (lokacija_uporabnika is None):
                if (('slovenia' or 'slovenija') in lokacija):
                    lokacija_uporabnika['tujec'] = 0
                else:
                    lokacija_uporabnika['tujec'] = 1
        
        # Primer 2)
        elif (re.findall(r'[N/S]\s?\d\d[°/\s]?\d{2}.\d{3}\,?\s?[E/W]\s?\d{2,3}[°/\s]?\d{2}.\d{3}', uporabnik['lokacija'])):
            if (not re.findall(r'°/\s', uporabnik['lokacija'])):
                uporabnik['lokacija'] = uporabnik['lokacija'].replace("°", "° ")
            if (not re.findall(r'E\s', uporabnik['lokacija'])):
                uporabnik['lokacija'] = uporabnik['lokacija'].replace("E", "E ")
            if (not re.findall(r'N\s', uporabnik['lokacija'])):
                uporabnik['lokacija'] = uporabnik['lokacija'].replace("N", "N ")
            if (not re.findall(r'W\s', uporabnik['lokacija'])):
                uporabnik['lokacija'] = uporabnik['lokacija'].replace("W", "W ")
            if (not re.findall(r'S\s', uporabnik['lokacija'])):
                uporabnik['lokacija'] = uporabnik['lokacija'].replace("S", "S ")

            lokacija = GPSUtils.pretvori_v_decimalni_zapis(uporabnik['lokacija'])
            kraj = GPSUtils.get_obcina(lokacija['lon'], lokacija['lat'])
            if (kraj is not None):
                lokacija_uporabnika = isci_kraj(kraj)
            if (not bool(lokacija_uporabnika)):
                lokacija_uporabnika['tujec'] = 1
        
        # Primer 3)
        if ('/' in str(uporabnik['lokacija'])):
            lokacija = uporabnik['lokacija'].split("/")
            lokacija = [l.strip().lower() for l in lokacija]
            for l in lokacija:
                lokacija_uporabnika = isci_kraj(l)
                if (bool(lokacija_uporabnika)): break
        
        # Primer 4)
        if ('-' in str(uporabnik['lokacija'])):
            lokacija = uporabnik['lokacija'].split("-")
            lokacija = [l.strip().lower() for l in lokacija]
            for l in lokacija:
                lokacija_uporabnika = isci_kraj(l)
                if (bool(lokacija_uporabnika)): break

        # Primer 5)
        if (len(lokacija_uporabnika) < 2):
            if ('tujec' in lokacija_uporabnika and lokacija_uporabnika['tujec'] == 0):
                lokacija_uporabnika = isci_kraj(uporabnik['lokacija'])
            else:
                lokacija_uporabnika = isci_kraj(uporabnik['lokacija'])
                    
        
        # Primer 6)
        if (not bool(lokacija_uporabnika)):
            if (re.findall(r'slovenij?a', ''.join(uporabnik['lokacija']), re.IGNORECASE)):
                lokacija_uporabnika['tujec'] = 0
        
    # Ce uporabnik nima podane lokacije jo poskusimo aproksimirati
    if (not bool(lokacija_uporabnika)):
        # Če ima ratio več od 0.22 je domačin, če ne je tujec
        # 0.22 sem dobil kot povprečje Top10 iskalcev iz SLO (vir: https://www.cacherstats.com/)
        ratio = float(len(uporabnik['seznamNajdenihZnotrajDrzave']))/float(uporabnik['steviloNajdenihZakladov']) if uporabnik['steviloNajdenihZakladov'] > 0 else 0
        if (ratio >= 0.22):
            lokacija_uporabnika['tujec'] = 0
        else:
            lokacija_uporabnika['tujec'] = 1
        
    # Za domacine, ki nimajo podane lokacije
    if (len(lokacija_uporabnika) == 1 and lokacija_uporabnika['tujec'] == 0):
        
        kraji = {}

        # Pridobivanje FTF-jev uporabnika
        if (uporabnik['uporabniskoIme'] in ftfs):
            ft1 = ftfs[uporabnik['uporabniskoIme']]
            for ftf in ft1:
                ftf['color'] = 'red'    # Za potrebe vizualizacije na zemljevidu
                kraj = GPSUtils.najblizje_mesto(ftf['lat'], ftf['lon'])
                if kraj not in kraji:
                    kraji[kraj] = {}
                if 'ftf' not in kraji[kraj]:
                    kraji[kraj]['ftf'] = 1
                else:
                    kraji[kraj]['ftf'] += 1
        else:
            ft1 = []


        # Pridobivanje skritih zakladov uporabnika
        ft2 = get_skriti(uporabnik['uporabniskoIme'])
        for skriti in ft2:
            skriti['color'] = 'blue'    # Za potrebe vizualizacije na zemljevidu
            ft1.append(skriti)
            kraj = GPSUtils.najblizje_mesto(skriti['lat'], skriti['lon'])
            if kraj not in kraji:
                kraji[kraj] = {}
            if 'skriti' not in kraji[kraj]:
                kraji[kraj]['skriti'] = 1
            else:
                kraji[kraj]['skriti'] += 1


        # Iskanje zakladov najdenih v prvih 3 iskalnih dneh
        prvih = []
        seznamNajdenih = uporabnik['seznamNajdenihZnotrajDrzave']
        for zaklad in seznamNajdenih:
            zaklad['datumObiska'] = helperUtils.parse_date(zaklad['datumObiska'])
        seznamNajdenih.sort(key=lambda item:item['datumObiska'])
        datumindex = 0
        datum = None
        for zaklad in seznamNajdenih:
            if (datum == None):
                datum = zaklad['datumObiska']
            elif (datum != zaklad['datumObiska']):
                datum = zaklad['datumObiska']
                datumindex +=1
            if(datumindex == 3):
                break
            trenutni = {}
            trenutni['koda'] = zaklad['kodaZaklada']
            trenutni['lat'] = zaklad['lokacija']['lat']
            trenutni['lon'] = zaklad['lokacija']['lon']
            trenutni['datum'] = zaklad['datumObiska'].strftime("%d.%m.%y")
            prvih.append(trenutni)
        for prve in prvih:
            prve['color'] = 'green' # Za potrebe vizualizacije na zemljevidu
            ft1.append(prve)
            kraj = GPSUtils.najblizje_mesto(prve['lat'], prve['lon'])
            if kraj not in kraji:
                kraji[kraj] = {}
            if 'prve' not in kraji[kraj]:
                kraji[kraj]['prve'] = 1
            else:
                kraji[kraj]['prve'] += 1
        
        maxtry = 3
        
        # Doloci kraj na podlagi skupin: FTF, skriti, 3 iskalni dni
        def doloci_kraj(maxtry):
            domacik = None
            domaciv = 0
            for kraj in kraji:
                if (len(kraji[kraj].keys()) == maxtry):
                    skupaj = sum(kraji[kraj].values())
                    if (skupaj > domaciv):
                        domaciv = skupaj
                        domacik = kraj
                    elif (skupaj == domaciv and 'skriti' in kraji[kraj] and 'skriti' in kraji[domacik]):   # Ce je stevilo enako, imajo skriti vecjo tezo
                        if (kraji[kraj]['skriti'] > kraji[domacik]['skriti']):
                            domaciv = skupaj
                            domacik = kraj
            if (domacik != None):
                return domacik
            else:
                maxtry -= 1
                return doloci_kraj(maxtry)

        domaci_kraj = doloci_kraj(maxtry)
        lokacija_uporabnika = isci_kraj(domaci_kraj)

        # Ce mesto ni obcina, poiscemo v kateri obcini je mesto
        if (domaci_kraj is not None and len(lokacija_uporabnika) < 1):
            kraj_koord = GPSUtils.kraj_v_koord(domaci_kraj)
            obcina = GPSUtils.get_obcina(kraj_koord['lon'], kraj_koord['lat'])
            lokacija_uporabnika = isci_kraj(obcina)
    
    uporabniki_lokacije[uporabnik['uporabniskoIme']] = lokacija_uporabnika

helperUtils.save_to_json(uporabniki_lokacije, "uporabniki_lokacije")