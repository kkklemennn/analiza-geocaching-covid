# -*- coding: utf-8 -*-

import re
import pycountry
import requests
import yaml
import json
import os
from bs4 import BeautifulSoup as bS
from os import path, listdir
from datetime import datetime, timedelta


BASE_URL = "https://www.geocaching.com"
CACHES_PER_PAGE = 50
TIMEFORMAT = "%m/%d/%Y-%H:%M:%S"


# Funkcija za razčlenjevanje odgovorov (responsev)
def parse(response):
    return bS(response.text, "html.parser")


# Neceli deli koordinat na portalu geocaching.com so zapisani v
# minutah, zato jih pretvorimo v decimalni zapis
def pretvori_v_decimalni_zapis(koordinate):
    split = koordinate.replace("°", "").split(" ")
    if len(split[0]) == 1 and not split[0][0].isdigit():
        lat = float(split[1]) + float(split[2]) / 60
        lon = float(split[4]) + float(split[5]) / 60
        return {"lat": lat, "lon": lon}
    return {"lat": 0.0, "lon": 0.0}


def odstej(datum, delta=5):
    razclenjen_datum = datum.split(".")
    dan, mesec, leto = razclenjen_datum[0], razclenjen_datum[1], razclenjen_datum[2]
    prejsnji_dan = datetime(int(leto), int(mesec), int(dan)) - timedelta(days=delta)
    return prejsnji_dan.month, prejsnji_dan.day, prejsnji_dan.year


# Logika nastavljanja statusa zaklada
def vrni_status(vrstica):
    if vrstica.find('a', {'class': 'upgrade'}):
        return "Premium"
    elif vrstica.find('span', {'class': 'status'}):
        return vrstica.find('span', {'class': 'status'}).text
    else:
        return "Default"


def pridobi_po_vrsticah(tabela, zacetni_index):
    struktura_elementov = []
    if not tabela:
        return struktura_elementov
    vrstice = tabela.find_all('tr')[zacetni_index:]
    for vrstica in vrstice:
        podatki = vrstica.find_all('td')
        if len(podatki) >= 2:
            struktura_elementov.append({
                "tip": podatki[-2].text.strip(),
                "stevilo": int(podatki[-1].text.strip().replace(",", ""))
            })
    return struktura_elementov


def skrajna_najdba(podatki):
    return {
        "koda": podatki.find('a').text.split(" - ")[0],
        "ime": podatki.find('a').text.split(" - ")[1],
        "kraj": re.findall(r'\((.*?)\)', podatki.text)[0],
        "lokacija": pretvori_v_decimalni_zapis(' '.join(podatki.text.strip().split(" ")[-6:]))
    }


# Pridobivanje nastavitvenih podatkov iz YAML datoteke
def vrni_nastavitvene_podatke():
    nastavitveni_podatki_pot = path.join(path.dirname(__file__), './config.yaml')
    if not path.exists(nastavitveni_podatki_pot):
        print("Datoteka config.yaml ni ustvarjena.")
        exit(0)
    with open(nastavitveni_podatki_pot) as nastavitveni_podatki_datoteka:
        return yaml.safe_load(nastavitveni_podatki_datoteka)


def ustvari_direktorije():
    data_pot = path.join(path.dirname(__file__), '../../data/downloaded')
    if not path.exists(data_pot):
        os.makedirs(data_pot)

    zakladi_pot = path.join(path.dirname(__file__), '../../data/downloaded/zakladi')
    if not path.exists(zakladi_pot):
        os.makedirs(zakladi_pot)

    uporabniki_pot = path.join(path.dirname(__file__), '../../data/downloaded/uporabniki')
    if not path.exists(uporabniki_pot):
        os.makedirs(uporabniki_pot)


class CachesGetter:
    def __init__(self, ime_drzave="Slovenia", obiski_uporabnika=False, lastnosti_uporabnika=True):

        """
        :param ime_drzave: Ime države, katere podatke želimo pridobiti
        :param obiski_uporabnika: parameter določa, ali bomo prebrali podatke
                o vseh obiskih posameznega uporabnika
        :param lastnosti_uporabnika: parameter določa, ali bomo prebrali podatke
                o lastnostih uporabnika (npr. struktura najdenih zakladov)
        """

        # Ustvarimo novo sejo
        self.session = requests.Session()

        # Nastavimo razredne spremenljivke
        self.ime_drzave = ime_drzave
        self.obiski_uporabnika = obiski_uporabnika
        self.lastnosti_uporabnika = lastnosti_uporabnika
        self.drzava = None

        self.stevilo_zakladov_v_drzavi = None
        self.iskanje_po_drzavi_url = None

        self.vsi_zakladi = {}
        self.vsi_uporabniki = {}

    def pridobi_podatke(self):

        # Izvedi prijavo na geocaching.com
        self.prijava()

        # Preveri veljavnost vpisane drzave in nastavi podatke o drzavi
        self.nastavi_drzavo()

        # Pridobivanje podatkov po fazah
        self.pridobi_seznam_vseh_zakladov()
        self.pridobi_podrobnosti_zakladov()
        self.pridobi_seznam_vseh_uporabnikov()
        self.pridobi_podrobnosti_uporabnikov()

    def prijava(self):
        prijavna_stran_url = BASE_URL + "/account/signin"
        prijavna_stran_response = self.session.get(prijavna_stran_url)
        prijavna_stran = parse(prijavna_stran_response)

        recaptcha = prijavna_stran.find('div', {'class': 'g-recaptcha'})

        # Če obstaja element recaptcha, prijavna stran zahteva reševanje reCaptche
        # V tem primeru v sejo dodamo piškotke
        if recaptcha is not None:

            print("Prijava zahteva recaptcho, prijavi se v portal 'ročno' in skopiraj"
                  "\n in prilepi Cookie atribut v glavi zahtevka za geocaching.com", end="")
            cookie_string = input("Cookie\n")
            self.session.headers.update({'Cookie': cookie_string})
        else:
            cookies = dict(prijavna_stran_response.cookies)
            request_verification_token = prijavna_stran.find('input', {'name': '__RequestVerificationToken'}).get(
                'value')

            print("Prijava ...", end=" ")

            nastavitveni_podatki = vrni_nastavitvene_podatke()
            payload = {
                'Password': nastavitveni_podatki["geslo"],
                'UsernameOrEmail': nastavitveni_podatki["email"],
                '__RequestVerificationToken': request_verification_token
            }

            login_response = self.session.post(prijavna_stran_url, data=payload, cookies=cookies)
            login = parse(login_response)
            if login.find('input', {'id': 'UsernameOrEmail'}):
                print("Prijava ni bila uspešna! Preveri elektronski naslov ali geslo.")
                exit(0)
            else:
                print(u'\u2713')

    def nastavi_drzavo(self):
        # Pridobimo seznam vseh možnih držav v spremenljivko options
        iskanje = self.get_request(BASE_URL + "/play/search")
        select = iskanje.find('select', {'id': 'SearchFiltersViewModel_SelectedAvailableCountriesAndRegions'})
        options = select.findAll('option')

        # Veljavne drzave so tiste, ki jih najdemo tako v seznamu na geocaching.com in kot tudi
        # na v seznamu držav v knjižnici pycountry
        for option in options:
            value = option.get('value')
            [geo_type, code] = value.split(':')
            if geo_type == 'country' and option.text == self.ime_drzave:
                for country in pycountry.countries:
                    if country.name == option.text:
                        country.code = code
                        self.drzava = country
                        return

        print("Neveljavna država")
        exit(0)

    # Pridobljeno stevilo primerjamo kasneje s številom vseh pridobljenih zakladov za namen preverjanja
    def pridobi_stevilo_zakladov_v_drzavi(self):
        self.iskanje_po_drzavi_url = BASE_URL + '/play/search?origin={}&ot=2&g={}' \
            .format(self.drzava.name, self.drzava.code)
        iskanje_po_drzavi = self.get_request(self.iskanje_po_drzavi_url)

        self.stevilo_zakladov_v_drzavi = int(
            iskanje_po_drzavi.find('h1', {'class': 'controls-header'}).text.split(' ')[0].replace(",", ""))

        print("Zakladov v državi: " + str(self.stevilo_zakladov_v_drzavi))

    def pridobi_seznam_vseh_zakladov(self):
        self.pridobi_stevilo_zakladov_v_drzavi()

        iskanje_po_drzavi_sortirano = self.get_request(self.iskanje_po_drzavi_url + "&sort=PlaceDate")
        datum_postavitve_prvega_zaklada = iskanje_po_drzavi_sortirano \
            .find('tbody') \
            .find('tr', {'data-rownumber': '0'}) \
            .find('td', {'data-column': 'PlaceDate'}) \
            .text.strip()

        # Datum zacetnega datuma pri iskanju mora biti starejši od datuma postavitve prvega zaklada
        mesec, dan, leto = odstej(datum_postavitve_prvega_zaklada)
        stevilo_zadetkov = self.stevilo_zakladov_v_drzavi

        while stevilo_zadetkov > 1000:
            iskanje_po_datumu = self.get_request(
                self.iskanje_po_drzavi_url + "&sort=PlaceDate&pad={}-{}-{}&utr=false".format(leto, mesec, dan))

            stevilo_zadetkov = int(iskanje_po_datumu
                                   .find('h1', {'class': 'controls-header'})
                                   .text.split(' ')[0].replace(",", ""))

            # Število iteracij nam pove kolikokrat se izvede pridobivanje naslednjih
            # 50 zadetkov/zakladov, saj jih naenkrat lahko pridobimo le 50
            stevilo_iteracij = min(20,
                                   int(stevilo_zadetkov / CACHES_PER_PAGE + (stevilo_zadetkov % CACHES_PER_PAGE > 0)))

            for iteracija in range(stevilo_iteracij):
                for _i in range(3):
                    zacetni_index = str(iteracija * CACHES_PER_PAGE)
                    iskanje_po_datumu_iteracija = BASE_URL + "/play/search/more-results?origin=" \
                                                             "{}&ot=2&g={}&sort=PlaceDate&pad=" \
                                                             "{}-{}-{}&startIndex={}&selectAll=false" \
                        .format(self.drzava.name, self.drzava.code, leto, mesec, dan, zacetni_index)

                    iskanje_po_datumu_response = self.session.get(iskanje_po_datumu_iteracija)

                    # Kot odgovor pri zahtevi za naslednjih 50 zadetkov prejmemo json zapis, katerega "HtmlString"
                    # atribut vsebuje html niz znakov za dopolnjevanje tabele zadetkov
                    json_response = json.loads(iskanje_po_datumu_response.text)
                    html_podatki_o_zadetkih = bS(json_response['HtmlString'], "html.parser")

                    # Poiščemo vse vrstice za novo pridobljene zaklade
                    zakladi_vrstice = html_podatki_o_zadetkih.findAll('tr')

                    # Za vsak novo pridobljen zaklad pridobimo njegove podrobnosti
                    for vrstica in zakladi_vrstice:
                        self.pridobi_lastnosti_zaklada(vrstica)

            id_zadnje_dodanega_zaklada = list(self.vsi_zakladi)[-1]
            mesec, dan, leto = odstej(self.vsi_zakladi[id_zadnje_dodanega_zaklada]['datumPostavitve'])

        stevilo_pridobljenih = len(self.vsi_zakladi)
        print("Pridobljenih: ", str(stevilo_pridobljenih), end=" ")
        if stevilo_pridobljenih == self.stevilo_zakladov_v_drzavi:
            print(u'\u2713')
            self.posodobi_seznam_vseh_zakladov()
        else:
            print(u'\u2717')
            exit(0)

    # Funkcija za pridobivanje podrobnosti
    def pridobi_lastnosti_zaklada(self, vrstica):

        # Pridobimo id zaklada
        cache_id = vrstica.get('data-id')

        # Če je zaklad že v slovarju pridobljenih zakladov v trenutnem zagonu bota, podrobnosti ne pridobimo
        if cache_id in self.vsi_zakladi:
            return

        self.vsi_zakladi[cache_id] = {
            "koda": cache_id,
            "ime": vrstica.get('data-name'),
            "povezava": BASE_URL + "/geocache/" + cache_id,
            "lastnik": vrstica.find('span', {'class': 'owner'}).text,
            "tip": vrstica.find('span', {'class': 'cache-details'}).text.split(" | ")[0],
            "status": vrni_status(vrstica),
            "tezavnost": float(vrstica.find('td', {'data-column': 'Difficulty'}).text.strip().replace(",", ".")),
            "teren": float(vrstica.find('td', {'data-column': 'Terrain'}).text.strip().replace(",", ".")),
            "velikost": vrstica.find('td', {'data-column': 'ContainerSize'}).text.strip(),
            "steviloFavoritov": int(vrstica.find('td', {'data-column': 'FavoritePoint'}).text),
            "datumPostavitve": vrstica.find('td', {'data-column': 'PlaceDate'}).text.strip(),
            "datumZadnjeNajdbe": vrstica.find('td', {'data-column': 'DateLastVisited'}).text.strip(),
            "zadnjaOsvezitevNaSeznamu": datetime.now().strftime(TIMEFORMAT),
        }

    def posodobi_seznam_vseh_zakladov(self):
        obstojeci_seznam_zakladov = {}
        vsi_zakladi_pot = path.join(path.dirname(__file__), '../../data/downloaded/vsi-zakladi-{}.json'.format(self.drzava.name))
        if path.isfile(vsi_zakladi_pot):
            vsi_zakladi_datoteka = open(vsi_zakladi_pot)
            obstojeci_seznam_zakladov = {obstojeci_zaklad["koda"]: obstojeci_zaklad for obstojeci_zaklad in
                                         json.load(vsi_zakladi_datoteka)}

        for novi_zaklad_id in self.vsi_zakladi:
            podatki_spremenjeni = True
            if len(obstojeci_seznam_zakladov) > 0:
                novi_podatki_zaklada = self.vsi_zakladi[novi_zaklad_id]
                obstojeci_podatki_zaklada = obstojeci_seznam_zakladov.get(novi_zaklad_id, None)
                if obstojeci_podatki_zaklada:
                    # V for zanki se sprehodimo čez vse lastnosti zaklada in preverimo,
                    # ce so novi podatki zaklada enaki obstojecim podatkom zaklada
                    for key in novi_podatki_zaklada:
                        if key != "zadnjaOsvezitevNaSeznamu" and novi_podatki_zaklada[key]\
                                != obstojeci_podatki_zaklada[key]:
                            break
                    else:
                        # Zanka se je izvedla brez prekinitve, podatki se torej niso spremenili
                        podatki_spremenjeni = False

            # Ce datoteka s seznamom vseh drzav se ne obstaja (dolzina seznama je enaka 0)
            # ali pa podatki zaklada se ne obstajajo v obstojecem seznamu, pustimo spremenljivko podatki_spremenjeni
            # nastavljeno na vrednost True
            if podatki_spremenjeni:
                # Če se podatki spremenijo, potem je cas zadnje spremembe enak casu zadnje osvezitve
                self.vsi_zakladi[novi_zaklad_id]["zadnjaSpremembaNaSeznamu"] = self.vsi_zakladi[novi_zaklad_id][
                    "zadnjaOsvezitevNaSeznamu"]
            else:
                # Če se podatki niso spremenili, potem je cas zadnje spremembe enak casu spremembe,
                # ki je zapisan v obstojecem seznamu zakladov
                self.vsi_zakladi[novi_zaklad_id]["zadnjaSpremembaNaSeznamu"] = \
                    obstojeci_seznam_zakladov[novi_zaklad_id][
                        "zadnjaSpremembaNaSeznamu"]

        # V JSON datoteko zapisemo posodobljen seznam vseh zakladov
        with open(vsi_zakladi_pot, 'w') as fp:
            json.dump([self.vsi_zakladi[zaklad_id] for zaklad_id in self.vsi_zakladi], fp)

    def pridobi_podrobnosti_zakladov(self):
        print("Pridobivanje podrobnosti zakladov")
        vsi_zakladi_pot = path.join(path.dirname(__file__), '../../data/downloaded/vsi-zakladi-{}.json'.format(self.drzava.name))
        vsi_zakladi_datoteka = open(vsi_zakladi_pot)
        seznam_zakladov = json.load(vsi_zakladi_datoteka)

        for index, zaklad in enumerate(seznam_zakladov):
            print(index, zaklad["koda"])
            zaklad_pot = path.join(path.dirname(__file__), '../../data/downloaded/zakladi/{}.json'.format(zaklad["koda"]))
            if not path.isfile(zaklad_pot):
                # Datoteka s podrobnostmi zaklada, se ne obstaja, zato pridobimo nove podrobnosti zaklada
                self.zapisi_podrobnosti_zaklada(zaklad, zaklad_pot)
            else:
                # Datoteka s podrobnostmi zaklada ze obstaja
                if datetime.strptime(zaklad["zadnjaOsvezitevNaSeznamu"], TIMEFORMAT) < \
                        datetime.strptime(zaklad["zadnjaSpremembaNaSeznamu"], TIMEFORMAT):
                    # Podrobnosti ne osvezujemo, saj je cas zadnje osvezitve lastnosti na seznamu starejsi ("manjsi")
                    # cas zadnje spremembe lastnosti na seznamu, kar pomeni, da se lastnosti zaklada niso spremenile
                    pass
                else:
                    zaklad_obstojeci_podatki_datoteka = open(zaklad_pot)
                    zaklad_obstojeci_podatki = json.load(zaklad_obstojeci_podatki_datoteka)

                    cas_zadnje_osvezitve_podrobnosti = zaklad_obstojeci_podatki["zadnjaOsvezitevPodrobnosti"]
                    # Če od zadnjega osvezevanja podrobnosti ni pretekel 1 teden, lahko osvezevanje preskocimo
                    if (datetime.now() < datetime.strptime(cas_zadnje_osvezitve_podrobnosti, TIMEFORMAT) + timedelta(days = 7)):
                        pass
                    else:
                        self.zapisi_podrobnosti_zaklada(zaklad, zaklad_pot, zaklad_obstojeci_podatki)

    def zapisi_podrobnosti_zaklada(self, zaklad, zaklad_pot, zaklad_obstojeci_podatki=None):
        podrobnosti_zaklada_bs = self.get_request(zaklad["povezava"])

        # Pridobimo podrobnosti, dosegljive na strani zaklada
        zaklad["kratek_opis"] = podrobnosti_zaklada_bs.find('span', {
            'id': 'ctl00_ContentBody_ShortDescription'}).text

        zaklad["dolg_opis"] = podrobnosti_zaklada_bs.find('span', {
            'id': 'ctl00_ContentBody_LongDescription'}).text

        zaklad["lokacija"] = pretvori_v_decimalni_zapis(
            podrobnosti_zaklada_bs.find('span', {'id': 'uxLatLon'}).text)

        zaklad["steviloDnevniskihZapisov"] = int(podrobnosti_zaklada_bs
                                                 .find('div', {'id': 'ctl00_ContentBody_bottomSection'})
                                                 .find('div', {'class': 'InformationWidget'})
                                                 .find('h3').text.strip().split(" ")[0].replace(",", ""))

        # Pridobimo vse dnevniske zapise obravnavanega zaklada
        self.pridobi_dnevniske_zapise_zaklada(podrobnosti_zaklada_bs, zaklad)

        zaklad["zadnjaOsvezitevPodrobnosti"] = datetime.now().strftime(TIMEFORMAT)

        if not zaklad_obstojeci_podatki:
            zaklad["zadnjaSpremembaPodrobnosti"] = zaklad["zadnjaOsvezitevPodrobnosti"]
        else:
            for key in ["kratek_opis", "dolg_opis", "lokacija", "steviloDnevniskihZapisov", "dnevniskiZapisi"]:
                if zaklad_obstojeci_podatki[key] != zaklad[key]:
                    # Obstojece podrobnosti zaklada se ne ujemajo z novo pridobljenimi, podrobnosti zakladi so
                    # se spremenile, zato je cas zadnje spremembe podrobnosti enak casu zadnje osvezevitve podrobnosti
                    zaklad["zadnjaSpremembaPodrobnosti"] = zaklad["zadnjaOsvezitevPodrobnosti"]
                    break
            else:
                # Vse podrobnosti so enake obstojecim, zato se cas zadnje spremembe podrobnosti prepise iz obstojecih
                # podatkov
                zaklad["zadnjaSpremembaPodrobnosti"] = zaklad_obstojeci_podatki["zadnjaSpremembaPodrobnosti"]

        with open(zaklad_pot, 'w') as fp:
            json.dump(zaklad, fp)

    def pridobi_dnevniske_zapise_zaklada(self, podrobnosti_zaklada_bs, zaklad):
        script_tags = podrobnosti_zaklada_bs.find_all('script')
        #print(script_tags)
        user_token = re.findall(r"userToken = '\w+'", str(script_tags))[0].split("'")[1]
        #print(user_token)
        idx = 1
        num = "100"

        zaklad["dnevniskiZapisi"] = []
        while True:
            logbook_url = BASE_URL + "/seek/geocache.logbook?tkn=" + user_token + "&idx=" + str(idx) + "&num=" + num
            logbook_page = self.session.get(logbook_url)
            logbook_data = json.loads(logbook_page.text)
            logs = logbook_data['data']

            for log in logs:
                zaklad['dnevniskiZapisi'].append({
                    'id': log['LogID'],
                    'guid': log['LogGuid'],
                    'tip': log['LogType'],
                    'text': log['LogText'],
                    'datumZapisa': log['Created'],
                    'datumObiska': log['Visited'],
                    'idAvtorja': log['AccountID'],
                    'guidAvtorja': log['AccountGuid'],
                    'slike': log['Images'],
                    'avtorZapisa': {
                        'uporabniskoIme': log['UserName'],
                        'id': log['AccountID'],
                        'guid': log['AccountGuid'],
                        'steviloNajdenihZakladov': log['GeocacheFindCount'],
                        'steviloSkritihZakladov': log['GeocacheHideCount'],
                        'steviloIzzivov': log['ChallengesCompleted'],
                        'stopnjaClanstva': log['MembershipLevel']
                    }
                })

            total_pages = int(logbook_data['pageInfo']['totalPages'])
            if idx == total_pages:
                break
            idx += 1

    def pridobi_seznam_vseh_uporabnikov(self):
        print("Pridobivanje vseh uporabnikov")
        zakladi_direktorij = path.join(path.dirname(__file__), '../../data/downloaded/zakladi')
        zakladi_seznam_poti = [f for f in listdir(zakladi_direktorij) if path.isfile(path.join(zakladi_direktorij, f))]

        for zaklad_pot in zakladi_seznam_poti:
            zaklad_pot = path.join(zakladi_direktorij, zaklad_pot)
            zaklad_datoteka = open(zaklad_pot)
            zaklad = json.load(zaklad_datoteka)
            #print(zaklad_pot)

            #print(len(zaklad["dnevniskiZapisi"]))
            for zapis in zaklad["dnevniskiZapisi"]:
                uporabnik = zapis['avtorZapisa']
                uporabnik['zadnjaOsvezitev'] = datetime.now().strftime(TIMEFORMAT)
                if uporabnik['id'] not in self.vsi_uporabniki:
                    uporabnik['seznamNajdenihZnotrajDrzave'] = []
                    self.vsi_uporabniki[uporabnik['id']] = uporabnik
                self.vsi_uporabniki[uporabnik['id']]['seznamNajdenihZnotrajDrzave'].append({
                    'kodaZaklada': zaklad['koda'],
                    'lokacija': zaklad['lokacija'],
                    'datumObiska': zapis['datumObiska'],
                    'datumZapisa': zapis['datumZapisa']
                })
            #break
            #print(len(self.vsi_uporabniki))

        self.posodobi_seznam_vseh_uporabnikov()

    def posodobi_seznam_vseh_uporabnikov(self):
        obstojeci_seznam_uporabnikov = {}
        vsi_uporabniki_pot = path.join(path.dirname(__file__),
                                       '../../data/downloaded/vsi-uporabniki-{}.json'.format(self.drzava.name))

        if path.isfile(vsi_uporabniki_pot):
            vsi_uporabniki_datoteka = open(vsi_uporabniki_pot)
            obstojeci_seznam_uporabnikov = {obstojeci_uporabnik["id"]: obstojeci_uporabnik
                                            for obstojeci_uporabnik in json.load(vsi_uporabniki_datoteka)}

        for novi_uporabnik_id in self.vsi_uporabniki:
            podatki_spremenjeni = True
            if len(obstojeci_seznam_uporabnikov) > 0:
                novi_podatki_uporabnika = self.vsi_uporabniki[novi_uporabnik_id]
                obstojeci_podatki_uporabnika = obstojeci_seznam_uporabnikov.get(novi_uporabnik_id, None)

                if obstojeci_podatki_uporabnika:
                    for key in ['steviloNajdenihZakladov', 'steviloSkritihZakladov', 'steviloIzzivov']:
                        if obstojeci_podatki_uporabnika[key] == novi_podatki_uporabnika[key]:
                            break
                    else:
                        podatki_spremenjeni = False
            # Ce smo ugotovili, da so se podatki uporabnika na seznamu vseh uporabnikov spremenili, potem
            # je cas zadnje spremembe enak casu zadnje osvezitve na seznamu vseh uporabnikov
            if podatki_spremenjeni:
                self.vsi_uporabniki[novi_uporabnik_id]['zadnjaSprememba'] = self.vsi_uporabniki[novi_uporabnik_id][
                    'zadnjaOsvezitev']
            # Ce se podatki niso spremenili je cas zadnje spremembe enak casu spremembe na obstojecem seznamu
            # uporabnikov
            else:
                self.vsi_uporabniki[novi_uporabnik_id]["zadnjaSprememba"] = \
                    obstojeci_seznam_uporabnikov[novi_uporabnik_id]["zadnjaSprememba"]

        # V JSON datoteko zapisemo posodobljen seznam vseh uporabnikov
        with open(vsi_uporabniki_pot, 'w') as fp:
            json.dump([self.vsi_uporabniki[uporabnik_id] for uporabnik_id in self.vsi_uporabniki], fp)

    def pridobi_podrobnosti_uporabnikov(self):
        vsi_uporabniki_pot = path.join(path.dirname(__file__),
                                       '../../data/downloaded/vsi-uporabniki-{}.json'.format(self.drzava.name))
        vsi_uporabniki_datoteka = open(vsi_uporabniki_pot)
        seznam_uporabnikov = json.load(vsi_uporabniki_datoteka)

        seznam_uporabnikov.reverse()

        for index, uporabnik in enumerate(seznam_uporabnikov):
            uporabnik_pot = path.join(path.dirname(__file__), '../../data/downloaded/uporabniki/{}.json'
                                      .format(uporabnik['id']))
            print(index, uporabnik['id'], uporabnik['uporabniskoIme'])
            # Datoteka s podrobnostmi uporabnika ne obstaja, zato pridobimo podrobnosti uporabnika
            if not path.isfile(uporabnik_pot):
                self.zapisi_podrobnosti_uporabnika(uporabnik, uporabnik_pot)
            # Datoteka s podrobnostmi uporabnika obstaja, podrobnosti pridobimo samo v nekaterih situacijah
            else:
                # Cas zadnje osvezitve na seznamu je starejsi od casa zadnje spremembe, zato podrobnosti uporabnika
                # ne posodabljamo
                if datetime.strptime(uporabnik['zadnjaOsvezitev'], TIMEFORMAT) \
                        < datetime.strptime(uporabnik['zadnjaSprememba'], TIMEFORMAT):
                    pass
                else:
                    uporabnik_obstojeci_podatki_datoteka = open(uporabnik_pot)
                    uporabnik_obstojeci_podatki = json.load(uporabnik_obstojeci_podatki_datoteka)

                    # Ce so bile podrobnosti osvezene v zadnjih 7 dneh, jih ne osvezujemo
                    cas_zadnje_osvezitve_podrobnosti = uporabnik_obstojeci_podatki['zadnjaOsvezitevPodrobnosti']

                    if (datetime.now() < datetime.strptime(cas_zadnje_osvezitve_podrobnosti, TIMEFORMAT) + timedelta(days = 7)):
                        pass
                    else:
                        self.zapisi_podrobnosti_uporabnika(uporabnik, uporabnik_pot, uporabnik_obstojeci_podatki)

    def zapisi_podrobnosti_uporabnika(self, uporabnik, uporabnik_pot, uporabnik_obstojeci_podatki=None):

        uporabnikova_stran_zakladi_bs = self.get_request(
            BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=geocaches")

        uporabnik['steviloPrejetihFavoritov'] = \
            int(uporabnikova_stran_zakladi_bs
                .find('span', {'id': 'ctl00_ProfileHead_ProfileHeader_Label_FavoritePointsTotal'})
                .text.split(" ")[0].replace(",", ""))

        uporabnik['datumPridruzitve'] = uporabnikova_stran_zakladi_bs \
            .find('span', {'id': 'ctl00_ProfileHead_ProfileHeader_lblMemberSinceDate'}) \
            .text.split(" ")[1]

        uporabnik['datumZadnjegaObiskaPortala'] = uporabnikova_stran_zakladi_bs \
            .find('span', {'id': 'ctl00_ProfileHead_ProfileHeader_lblLastVisitDate'}) \
            .text.split(" ")[-1]

        location_span_element = uporabnikova_stran_zakladi_bs\
            .find('span', {'id': 'ctl00_ProfileHead_ProfileHeader_lblLocationTxt'})

        if location_span_element:
            uporabnik['lokacija'] = location_span_element.text.split(":")[1].strip()

        zakladi_tabeli = uporabnikova_stran_zakladi_bs.findAll('table')

        uporabnik['strukturaNajdenihZakladov'] = pridobi_po_vrsticah(zakladi_tabeli[0], 2)
        uporabnik['strukturaSkritihZakladov'] = pridobi_po_vrsticah(zakladi_tabeli[1], 2)

        # Pridobi podatke o predstavitvi (trenutno se ne pridobiva nic)
        #uporabnikova_stran_predstavitev_bs = self.get_request(
        #    BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=profile")

        # Pridobi podatke o sledljivckih
        uporabnikova_stran_sledljivcki_bs = self.get_request(
            BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=trackables")

        tabela_odkriti_sledljivcki = uporabnikova_stran_sledljivcki_bs \
            .find('table', {'id': 'ctl00_ContentBody_ProfilePanel1_dlCollectibles'})
        tabela_sledljivcki_v_lasti = uporabnikova_stran_sledljivcki_bs \
            .find('table', {'id': 'ctl00_ContentBody_ProfilePanel1_dlCollectiblesOwned'})

        uporabnik['strukturaOdkritihSledljivckov'] = pridobi_po_vrsticah(tabela_odkriti_sledljivcki, 2)
        uporabnik['strukturaSledljivckovVLasti'] = pridobi_po_vrsticah(tabela_sledljivcki_v_lasti, 2)

        # Pridobi podatke o suvenirjih
        uporabnikova_stran_suvenirji_bs = self.get_request(
            BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=souvenirs")

        uporabnik["suvenirji"] = []
        seznam_suvenirjev = uporabnikova_stran_suvenirji_bs.find('div', {'class': 'ProfileSouvenirsList'}).find_all(
            'div')
        for suvenir in seznam_suvenirjev:
            uporabnik["suvenirji"].append({
                "ime": suvenir.find('a').get('title'),
                "povezava": BASE_URL + suvenir.find('a').get('href'),
                "guid": suvenir.find('a').get('href').split("=")[-1],
                "datumPridobitve": suvenir.text.strip().split(" ")[-1]
            })

        # Pridobi podatke o seznamih
        uporabnikova_stran_seznami_bs = self.get_request(
            BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=lists")

        uporabnik["favoriti"] = []
        seznam_favoritov = uporabnikova_stran_seznami_bs.find('table').find('tbody').find_all('tr')
        for favorite in seznam_favoritov:
            table_data = favorite.find_all('td')
            uporabnik["favoriti"].append({
                "koda": table_data[0].find('a').text,
                "povezava": BASE_URL + '/geocache/' + table_data[0].find('a').text,
                "ime": table_data[1].find('span').text.strip(),
                "lokacija": table_data[2].text.strip()
            })

        # Pridobi podatke o statistiki
        uporabnikova_stran_statistika_bs = self.get_request(
            BASE_URL + "/p/default.aspx?guid=" + uporabnik["guid"] + "&tab=stats")
        uporabnik["statistika"] = statistika = {}

        statistika_skrita = uporabnikova_stran_statistika_bs \
            .find('div', {'id': 'ctl00_ContentBody_ProfilePanel1_uxStatisticsWarningPanel'})

        if not statistika_skrita and uporabnik["steviloNajdenihZakladov"] > 0:

            # Osnovna statistika
            basic_finds = uporabnikova_stran_statistika_bs.find('div', {'id': 'BasicFinds'})
            if basic_finds:
                basic_finds_odstavka = basic_finds.find_all('p')

                statistika["datumPrveNajdbe"] = basic_finds_odstavka[0].find_all('strong')[1].text
                statistika["najpogostejsiMesec"] = str(basic_finds_odstavka[1].find_all('strong')[0].text)
                statistika["najpogostejsiDan"] = basic_finds_odstavka[1].find_all('strong')[1].text

            # Kronoloska statistika
            kronoloska_statistika = uporabnikova_stran_statistika_bs \
                .find('div', {'id': 'ctl00_ContentBody_ProfilePanel1_StatsChronologyControl1_FindStatistics'})
            if kronoloska_statistika:
                kronoloski_podatki = kronoloska_statistika.find('dl').find_all('dd')

                statistika["pogostostNajdbDnevno"] = float(kronoloski_podatki[0].find('strong').text)

                najdaljsi_niz_strong_podatki = kronoloski_podatki[1].find_all('strong')
                statistika["najdaljsiNiz"] = {}
                if len(najdaljsi_niz_strong_podatki) >= 3:
                    statistika["najdaljsiNiz"] = {
                        "steviloDni": int(najdaljsi_niz_strong_podatki[0].text),
                        "zacetniDatum": najdaljsi_niz_strong_podatki[1].text,
                        "koncniDatum": najdaljsi_niz_strong_podatki[2].text
                    }
                else:
                    statistika["najdaljsiNiz"]["steviloDni"] = int(najdaljsi_niz_strong_podatki[0].text)

                najdaljsi_premor_strong_podatki = kronoloski_podatki[2].find_all('strong')
                statistika["najdaljsiPremor"] = {}
                if len(najdaljsi_premor_strong_podatki) >= 3:
                    statistika["najdaljsiPremor"] = {
                        "steviloDni": int(najdaljsi_premor_strong_podatki[0].text),
                        "zacetniDatum": najdaljsi_premor_strong_podatki[1].text,
                        "koncniDatum": najdaljsi_premor_strong_podatki[2].text
                    }
                else:
                    statistika["najdaljsiPremor"]["steviloDni"] = int(najdaljsi_premor_strong_podatki[0].text)

                statistika["sedanjiNizSteviloDni"] = int(kronoloski_podatki[3].find('strong').text)
                statistika["sedanjiPremorSteviloDni"] = int(kronoloski_podatki[4].find('strong').text)

                najboljsi_dan_strong_podatki = kronoloski_podatki[5].find_all('strong')
                statistika["najboljsiDan"] = {
                    "steviloZakladov": int(najboljsi_dan_strong_podatki[0].text),
                    "datum": najboljsi_dan_strong_podatki[1].text
                }

                najboljsi_mesec_strong_podatki = kronoloski_podatki[6].find_all('strong')
                statistika["najboljsiMesec"] = {
                    "steviloZakladov": int(najboljsi_mesec_strong_podatki[0].text),
                    "mesec": najboljsi_mesec_strong_podatki[1].text
                }

                najboljse_leto_strong_podatki = kronoloski_podatki[7].find_all('strong')
                statistika["najboljseLeto"] = {
                    "steviloZakladov": int(najboljse_leto_strong_podatki[0].text),
                    "leto": int(najboljse_leto_strong_podatki[1].text)
                }

            # Statistika po letih
            statistika_po_letih = uporabnikova_stran_statistika_bs \
                .find('div', {'id': 'ctl00_ContentBody_ProfilePanel1_StatsChronologyControl1_YearlyBreakdown'})

            if statistika_po_letih:
                statistika_po_letih_vrstice = statistika_po_letih.find('table').find_all('tr')[1:]

                statistika["statistikaPoLetih"] = []

                for vrstica_leto in statistika_po_letih_vrstice:
                    vrstica_leto_podatki = vrstica_leto.find_all('td')
                    statistika["statistikaPoLetih"].append({
                        "leto": int(vrstica_leto_podatki[0].text.strip()),
                        "steviloNajdb": int(vrstica_leto_podatki[1].text.strip()),
                        "pogostostNajdb": float(vrstica_leto_podatki[2].find('strong').text.strip())
                    })

            # Statistika po drzavah
            zemljevid = uporabnikova_stran_statistika_bs.find('div', {'id': 'stats_tabs-maps'})
            if not zemljevid.find('p', {'class', 'Warning'}):
                statistika["steviloNajdenihPoDrzavah"] = []
                vrstice_po_drzavah = zemljevid.find('table').find_all('tr')
                for drzava in vrstice_po_drzavah:
                    podatki = drzava.find_all('td')
                    statistika["steviloNajdenihPoDrzavah"].append({
                        "drzava": podatki[0].text,
                        "stevilo": int(podatki[1].text)
                    })

            # Statistika po velikosti zakladov
            tabela_zakladi_po_velikosti = uporabnikova_stran_statistika_bs \
                .find('table', {'class', 'ContainerTypesTable'})

            if tabela_zakladi_po_velikosti:
                statistika["strukturaZakladovPoVelikosti"] = []
                podatki = tabela_zakladi_po_velikosti.find_all('td')
                seznam_velikosti = podatki[0].find_all('li')
                seznam_frekvenc = podatki[2].find_all('li')

                for velikost, frekvenca in zip(seznam_velikosti, seznam_frekvenc):
                    statistika["strukturaZakladovPoVelikosti"].append({
                        "velikost": velikost.text.strip(),
                        "frekvenca": int(frekvenca.text.strip().split(" ")[0])
                    })

            # Statistika po oddaljenosti
            statistika_oddaljenosti = uporabnikova_stran_statistika_bs \
                .find('div', {'id': 'ctl00_ContentBody_ProfilePanel1_StatsLocationControl1_HomeLocation'})

            if statistika_oddaljenosti:
                statistika["statistikaOddaljenosti"] = oddaljenost = {}
                podatki = statistika_oddaljenosti.find_all('dd')

                oddaljenost["najdbaNajblizjeDomu"] = {
                    "razdalja": float(re.search(".*?([\\d\\.]+?) (\\w+).*", podatki[0].text.strip()).group(1)),
                    "enota": re.search(".*?([\\d\\.]+?) (\\w+).*", podatki[0].text.strip()).group(2)
                }

                oddaljenost["najdbaNajdljeOdDoma"] = {
                    "razdalja": float(re.search(".*?([\\d\\.]+?) (\\w+).*", podatki[1].text.strip()).group(1)),
                    "enota": re.search(".*?([\\d\\.]+?) (\\w+).*", podatki[1].text.strip()).group(2)
                }

                oddaljenost["najsevernejsaNajdba"] = skrajna_najdba(podatki[2])
                oddaljenost["najjuznejsaNajdba"] = skrajna_najdba(podatki[3])
                oddaljenost["najvzhodnejsaNajdba"] = skrajna_najdba(podatki[4])
                oddaljenost["najzahodnejsaNajdba"] = skrajna_najdba(podatki[5])

                tabela_oddaljenosti = uporabnikova_stran_statistika_bs.find('table', {'class': 'LocationTable'})
                if tabela_oddaljenosti:
                    statistika["strukturaZakladovPoOddaljenosti"] = []
                    podatki = tabela_oddaljenosti.find_all('td')
                    seznam_oddaljenosti = podatki[0].find_all('li')
                    seznam_frekvenc = podatki[2].find_all('li')

                    for index, (oddaljenost, frekvenca) in enumerate(zip(seznam_oddaljenosti, seznam_frekvenc)):
                        spodnja_meja = zgornja_meja = 0
                        enota = oddaljenost.text.strip().split()[-1]
                        if index == 0:
                            [zgornja_meja] = [int(s) for s in oddaljenost.text.strip().split() if s.isdigit()]
                        elif index == len(seznam_oddaljenosti) - 1:
                            [spodnja_meja] = [int(s) for s in oddaljenost.text.strip().split() if s.isdigit()]
                        else:
                            zgornja_meja, spodnja_meja = [int(s) for s in
                                                          oddaljenost.text.strip().split() if s.isdigit()]

                        statistika["strukturaZakladovPoOddaljenosti"].append({
                            "spodnjaMeja": spodnja_meja,
                            "zgornjaMeja": zgornja_meja,
                            "enota": enota,
                            "frekvenca": int(frekvenca.text.strip().split(" ")[0])
                        })

        uporabnik_seznam_najdenih_url = BASE_URL + "/seek/nearest.aspx?ul=" + uporabnik['uporabniskoIme']\
                                        + "&sortdir=asc&sort=lastFound"
        uporabnik_seznam_najdenih_bs = self.get_request(uporabnik_seznam_najdenih_url)
        seznam_zakladov_na_strani_tabela = uporabnik_seznam_najdenih_bs.find('table', {'class': 'SearchResultsTable'})
        if seznam_zakladov_na_strani_tabela:
            vrstica = seznam_zakladov_na_strani_tabela.find('tr', {'class': 'Data'})
            ime, podatki = vrstica.find_all('td')[5].findAll('span')
            podatki = podatki.text.split("|")
            uporabnik["prvoOdkritiZaklad"] = {
                "ime": ime.text.strip(),
                "avtor": podatki[0].strip().replace("by ", ""),
                "koda": podatki[1].strip(),
                "lokacija": podatki[2].strip()
            }

        # Obiski uporabnika se trenutno ne pridobivajo, saj ta funkcija močno poveča
        # čas pridobivanja podatkov
        # self.pridobi_obiske_uporabnika(uporabnik)

        uporabnik["zadnjaOsvezitevPodrobnosti"] = datetime.now().strftime(TIMEFORMAT)

        if not uporabnik_obstojeci_podatki:
            uporabnik["zadnjaSpremembaPodrobnosti"] = uporabnik["zadnjaOsvezitevPodrobnosti"]
        else:
            for key in ["strukturaNajdenihZakladov", 'strukturaSkritihZakladov',
                        'strukturaOdkritihSledljivckov', 'strukturaSledljivckovVLasti', 'statistika',
                        'favoriti', 'suvenirji']:
                if uporabnik_obstojeci_podatki[key] != uporabnik[key]:
                    uporabnik["zadnjaSpremembaPodrobnosti"] = uporabnik["zadnjaOsvezitevPodrobnosti"]
                    break
            else:
                # Vse podrobnosti so enake obstojecim, zato se cas zadnje spremembe podrobnosti prepise iz obstojecih
                # podatkov
                uporabnik["zadnjaSpremembaPodrobnosti"] = uporabnik_obstojeci_podatki[
                    "zadnjaSpremembaPodrobnosti"]

        with open(uporabnik_pot, 'w') as fp:
            json.dump(uporabnik, fp)

    def pridobi_obiske_uporabnika(self, uporabnik):

        username = uporabnik['uporabniskoIme']
        uporabnik['seznamObiskanih'] = []
        # Odpremo prvo stran seznama uporabnikovih obiskov
        uporabnikovi_zakladi_url = BASE_URL + "/seek/nearest.aspx?ul=" + username
        uporabnikovi_zakladi = self.get_request(uporabnikovi_zakladi_url)

        # Pridobimo stevilo strani seznama vseh uporabnikovih obiskov
        stevilo_strani_zakladov = int(
            uporabnikovi_zakladi.find('td', {'class': 'PageBuilderWidget'}).findAll('b')[2].text)

        # V iteracijah pregledamo vse strani seznama
        for _i in range(stevilo_strani_zakladov):
            seznam_zakladov_na_strani = uporabnikovi_zakladi.find('table', {'class': 'SearchResultsTable'}).findAll(
                'tr', {'class': 'Data'})
            for zaklad in seznam_zakladov_na_strani:
                podatki_o_zakladu = zaklad.findAll('td')
                id_zaklada = podatki_o_zakladu[5].text.split('|')[1].strip()
                lokacija = podatki_o_zakladu[5].text.split('|')[2].strip()
                tip_zaklada = podatki_o_zakladu[4].find('img').get('alt')
                datum_obiska = podatki_o_zakladu[9].text.strip()
                if datum_obiska[-1] == "*":
                    if datum_obiska[:-1] == "Today":
                        datum_obiska = datetime.today().strftime("%m/%d/%Y")
                    elif datum_obiska[:-1] == "Yesterday":
                        datum_obiska = (datetime.today() - timedelta(days=1)).strftime("%m/%d/%Y")
                    else:
                        difference = int(datum_obiska[0])
                        datum_obiska = (datetime.today() - timedelta(days=difference)).strftime("%m/%d/%Y")

                uporabnik['seznamObiskanih'].append({
                    "idZaklada": id_zaklada,
                    "tipZaklada": tip_zaklada,
                    "datumObiska": datum_obiska,
                    "lokacija": lokacija
                })

            hidden_inputs = uporabnikovi_zakladi.findAll('div', {'class': 'aspNetHidden'})
            inputs = hidden_inputs[0].findAll('input') + hidden_inputs[1].findAll('input')
            form_data = {}
            for inp in inputs:
                form_data[inp.get('id')] = inp.get('value')
            form_data['__EVENTTARGET'] = 'ctl00$ContentBody$pgrTop$ctl08'

            uporabnikovi_zakladi_response = self.session.post(uporabnikovi_zakladi_url, form_data)
            uporabnikovi_zakladi = parse(uporabnikovi_zakladi_response)

    def get_request(self, url):
        response = self.session.get(url)
        return parse(response)


if __name__ == '__main__':
    ustvari_direktorije()
    cache_getter = CachesGetter()
    cache_getter.pridobi_podatke()
