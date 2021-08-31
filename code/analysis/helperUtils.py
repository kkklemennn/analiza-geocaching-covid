import json
import gzip
import datetime
import pandas as pd

def read_uporabniki():
    f = open("../../data/downloaded/vsi-uporabniki-Slovenia.json")
    data = json.load(f)
    return data

def read_zakladi():
    f = open("../../data/downloaded/vsi-zakladi-Slovenia.json")
    data = json.load(f)
    return data

def read_json(path):
    f = open(path,"r",encoding='utf-8')
    data = json.load(f)
    return data

def save_to_json(data, filename):
    with open("../../data/processed/" + filename + ".json" , 'w+', encoding='utf-8') as fp:
        json.dump(data, fp, indent=4, ensure_ascii=False)

def read_regije():
    f = open("../../data/raw/OSM/OSM-slovenske-statisticne-regije.geojson","r",encoding='utf-8')
    data = json.load(f)
    return data

def read_obcine():
    f = open("../../data/raw/OSM/OSM-slovenske-obcine.geojson","r",encoding='utf-8')
    data = json.load(f)
    return data

def read_mesta():
    f = open("../../data/raw/OSM/OSM-slo3-place-city-town.geojson","r",encoding='utf-8')
    data = json.load(f)
    return data

def get_obcine_list():
    f = open("../../data/processed/obcine-v-regijah.json","r",encoding='utf-8')
    data = json.load(f)
    return data

def read_ftfs():
    f = open("../../data/processed/ftfs.json","r",encoding='utf-8')
    data = json.load(f)
    return data

def parse_date(datum):
    datumParse = datum.split(".")
    return datetime.date(int(datumParse[2]), int(datumParse[1]), int(datumParse[0]))

def read_apple_mobility():
    df = pd.read_csv('../../data/raw/Mobility_Trends/applemobilitytrends-2021-08-02.csv')
    apple_mobility = df.loc[df['region'] == 'Slovenia']
    return apple_mobility

def read_uporabniki_lokacije():
    f = open("../../data/processed/uporabniki_lokacije.json","r",encoding='utf-8')
    data = json.load(f)
    return data

def read_zakladi_lokacije():
    f = open("../../data/processed/zakladi_lokacije.json","r",encoding='utf-8')
    data = json.load(f)
    return data

def read_google_mobility():
    ohrani = [
    'date',
    'retail_and_recreation_percent_change_from_baseline',
    'grocery_and_pharmacy_percent_change_from_baseline',
    'parks_percent_change_from_baseline',
    'transit_stations_percent_change_from_baseline',
    'workplaces_percent_change_from_baseline',
    'residential_percent_change_from_baseline'
    ]
    df1 = pd.read_csv('../../data/raw/Mobility_Trends/2020_SI_Region_Mobility_Report.csv')
    df2 = pd.read_csv('../../data/raw/Mobility_Trends/2021_SI_Region_Mobility_Report.csv')
    dff1 = df1.loc[df1.place_id == 'ChIJYYOWXuckZUcRZdTiJR5FQOc',]
    dff2 = df2.loc[df2.place_id == 'ChIJYYOWXuckZUcRZdTiJR5FQOc',]
    dff = dff1.append(dff2)
    dff = dff.set_index(dff.date)
    dff = dff.filter(ohrani)
    return dff