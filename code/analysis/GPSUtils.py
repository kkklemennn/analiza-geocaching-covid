import math
from shapely.geometry import shape, Point, Polygon
import helperUtils

# Pretvori koordinate v regijo
def get_regija(lon,lat):
    point = Point(lon,lat)
    regije = helperUtils.read_regije()
    for feature in regije['features']:
        name = feature['properties']['name']
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return name
    return None

# Pretvori koordinate v obcino
def get_obcina(lon,lat):
    point = Point(lon,lat)
    obcine = helperUtils.read_obcine()
    for feature in obcine['features']:
        if ('name' not in feature['properties']):
            break
        name = feature['properties']['name']
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return name
    return None

# Najde najblizje mesto danim koordinatam
def najblizje_mesto(lat,lon):
    koordinateCache = {
        "lat": lat,
        "lon": lon
    }
    minRazdalja = 999999999
    minMesto = None   
    mesta = helperUtils.read_mesta()
    for feature in mesta['features']:
        name = feature['properties']['name']
        koodrinateMesto = {
            "lat": feature['geometry']['coordinates'][1],
            "lon": feature['geometry']['coordinates'][0]
        }
        razdalja = razdalja_med_koordinati(koordinateCache, koodrinateMesto)
        if (razdalja < minRazdalja):
            minRazdalja = razdalja
            minMesto = name
    return minMesto

# Vrne razdaljo med koordinatama
def razdalja_med_koordinati(lokacija1, lokacija2):
    # Source: https://en.wikipedia.org/wiki/Haversine_formula
    lat1 = math.radians(lokacija1["lat"])
    lon1 = math.radians(lokacija1["lon"])
    lat2 = math.radians(lokacija2["lat"])
    lon2 = math.radians(lokacija2["lon"])
    a = math.sin((lat2-lat1) / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1) / 2)**2
    r_zemlje = 6371 # km
    return (2 * r_zemlje * math.asin(math.sqrt(a)))

# Vrne koordinate dolocenega kraja
def kraj_v_koord(kraj):
    mesta = helperUtils.read_mesta()
    for feature in mesta['features']:
        name = feature['properties']['name']
        if (kraj.lower() == name.lower()):
            koodrinateMesto = {
            "lat": feature['geometry']['coordinates'][1],
            "lon": feature['geometry']['coordinates'][0]
            }
            return koodrinateMesto

# Vrne razdaljo med dvema krajama
def razdalja_med_krajema(kraj1, kraj2):
    if (kraj1 != None and kraj2 != None):
        koord1 = kraj_v_koord(kraj1)
        koord2 = kraj_v_koord(kraj2)
        if (koord1 != None and koord2 != None):
            razdalja = razdalja_med_koordinati(koord1, koord2)
            return razdalja
        else: return 0
    else: return 0

# Pretvori koordinate iz formata: N XX° XX.XXX E XXX° XX.XXX v decimalni zapis
def pretvori_v_decimalni_zapis(koordinate):
    split = koordinate.replace("°", "").split(" ")
    if len(split[0]) == 1 and not split[0][0].isdigit():
        lat = float(split[1]) + float(split[2]) / 60
        lon = float(split[4]) + float(split[5]) / 60
        return {"lat": lat, "lon": lon}
    return {"lat": 0.0, "lon": 0.0}