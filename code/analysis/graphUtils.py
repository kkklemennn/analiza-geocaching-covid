from helperUtils import read_obcine, read_regije
import plotly.graph_objects as go
import plotly.express as px

from urllib.request import urlopen
import numpy as np
import pandas as pd
import ast

#import pandas as pd
#pd.options.plotting.backend = "plotly"

barve = ["#F94144", "#F8961E", "#F9C74F", "#90BE6D", "#43AA8B", "#577590", "#F3722C"]

def newstyle(fig):
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#A8A8A8', showline=True, linewidth=2, linecolor='black')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#A8A8A8', showline=True, linewidth=2, linecolor='black')

def izrisi_leta_povp(leta, naslov):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["povp"].values(), dtype=int),
        name='Povprečje 2017-2019',
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2020"].values(), dtype=int),
        name='2020',
        marker_color=barve[1]
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2021"].values(), dtype=int),
        name='2021',
        marker_color=barve[3]
    ))
    newstyle(fig)
    #fig.write_image("temp.png")
    fig.show()

def izrisi_tujci_domaci(leta, naslov):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["povp"]["domaci"].values(), dtype=int),
        name='Povprečje 2017-2019 domači',
        marker_color="#FDC437"
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["povp"]["tujci"].values(), dtype=int),
        name='Povprečje 2017-2019 tujci',
        marker_color="#CF9300"
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2020"]["domaci"].values(), dtype=int),
        name='2020 domači',
        marker_color="#E64374"
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2020"]["tujci"].values(), dtype=int),
        name='2020 tujci',
        marker_color="#B90038"
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2021"]["domaci"].values(), dtype=int),
        name='2021 domači',
        marker_color="#ACEC33"
    ))
    fig.add_trace(go.Line(
        x=months,
        y=np.fromiter(leta["2021"]["tujci"].values(), dtype=int),
        name='2021 tujci',
        marker_color="#70AB00"
    ))
    newstyle(fig)
    #fig.write_image("temp.png")
    fig.show()

def izrisi_leta(leta, od, naslov):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fig = go.Figure()
    for i in range(2022-int(od)):
        trenutno = int(od) + i
        fig.add_trace(go.Line(
            x=months,
            y=np.fromiter(leta[str(trenutno)].values(), dtype=int),
            name=str(trenutno),
            marker_color=barve[i]
        ))
    fig.update_layout(title_text=naslov+" od leta " + str(od))
    fig.show()

def izrisi_apple_mobility(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.index,
        y=df['driving'],
        name="navodila za vožnjo (Apple zemljevidi)",
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['walking'],
        name="navodila za hojo (Apple zemljevidi)",
        marker_color=barve[1]
    ))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    newstyle(fig)
    #fig.write_image("temp.png")
    fig.show()
    
def izrisi_najdbe_po_tipih(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.index,
        y=df['Traditional'],
        name="Traditional",
        marker_color="#02874d"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['Mystery'],
        name="Mystery",
        marker_color="#12508c"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['Multi-Cache'],
        name="Multi-Cache",
        marker_color="#e98300"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['Virtual'],
        name="Virtual",
        marker_color="#009bbb"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['Earthcache'],
        name="Earthcache",
        marker_color="#fdbb12"
    ))
    newstyle(fig)
    #fig.update_layout(title_text="Najdbe po vseh tipih zakladov, razen tradicionalnih")
    #fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    #fig.write_image("temp.png")
    fig.show()

def izrisi_evente(df17, df18, df19, df20, df21):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df17[0],
        y=df17[1],
        name="2017",
        marker_color="#fedcda"
    ))
    fig.add_trace(go.Line(
        x=df18[0],
        y=df18[1],
        name="2018",
        marker_color="#ffada9"
    ))
    fig.add_trace(go.Line(
        x=df19[0],
        y=df19[1],
        name="2019",
        marker_color="#ff7f78"
    ))
    fig.add_trace(go.Line(
        x=df20[0],
        y=df20[1],
        name="2020",
        marker_color="#b30900"
    ))
    fig.add_trace(go.Line(
        x=df21[0],
        y=df21[1],
        name="2021",
        marker_color="#510400"
    ))
    newstyle(fig)
    #fig.write_image("temp.png")
    fig.show()


def map_prehajanja_regije(df):
    regije = read_regije()
    fig = px.choropleth_mapbox(df, geojson=regije, locations='name', featureidkey="properties.name", color='število prehajanj',
                        color_continuous_scale=[(0,"green"), (0.2,"yellow"), (1,"red")],
                        mapbox_style="carto-positron",
                        zoom=7, center = {"lat": 46.1193, "lon": 14.9233},
                        opacity=0.5,
                        title='Prehajanje igralcev med regijami'
                        )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    #fig.write_image("temp.png")
    fig.show()

def map_skupine_regije(df):
    regije = read_regije()
    fig = px.choropleth_mapbox(df, geojson=regije, locations='name', featureidkey="properties.name", color='število skupin',
                        color_continuous_scale=[(0,"green"), (0.2,"yellow"), (1,"red")],
                        mapbox_style="carto-positron",
                        zoom=7, center = {"lat": 46.1193, "lon": 14.9233},
                        opacity=0.5
                        )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    #fig.write_image("temp.png")
    fig.show()

def map_prehajanja_obcine(df):
    obcine = read_obcine()
    fig = px.choropleth_mapbox(df, geojson=obcine, locations='name', featureidkey="properties.name", color='število prehajanj',
                        color_continuous_scale=[(0,"green"), (0.09,"yellow"), (0.5,"red")],
                        mapbox_style="carto-positron",
                        zoom=7, center = {"lat": 46.1193, "lon": 14.9233},
                        opacity=0.5,
                        )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    #fig.write_image("temp.png")
    fig.show()

def map_prehajanja_regije_normal(df):
    regije = read_regije()
    fig = px.choropleth_mapbox(df, geojson=regije, locations='name', featureidkey="properties.name", color='prehajanja',
                        color_continuous_scale=[(0,"green"), (0.5,"yellow"), (1,"red")],
                        mapbox_style="carto-positron",
                        zoom=7, center = {"lat": 46.1193, "lon": 14.9233},
                        opacity=0.5
                        )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(coloraxis_colorbar=dict(
        ticksuffix="%"
    ))
    #fig.write_image("temp.png")
    fig.show()

def map_prehajanja_obcine_normal(df):
    obcine = read_obcine()
    fig = px.choropleth_mapbox(df, geojson=obcine, locations='name', featureidkey="properties.name", color='prehajanja',
                        color_continuous_scale=[(0,"green"), (0.09,"yellow"), (1,"red")],
                        mapbox_style="carto-positron",
                        zoom=7, center = {"lat": 46.1193, "lon": 14.9233},
                        opacity=0.5
                        )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(coloraxis_colorbar=dict(
        ticksuffix="%"
    ))
    #fig.write_image("temp.png")
    fig.show()

def izrisi_apple_mobility_smooth(df, smooth):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.index,
        y=df['driving'],
        name="driving",
        showlegend=False,
        opacity=0.25,
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['walking'],
        name="walking",
        showlegend=False,
        opacity=0.25,
        marker_color=barve[1]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['aktivni'],
        name="aktivni",
        showlegend=False,
        opacity=0.25,
        marker_color=barve[3]
    ))
    fig.add_trace(go.Line(
        x=smooth.index,
        y=smooth['driving'],
        name="navodila za vožnjo (Apple zemljevidi)",
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=smooth.index,
        y=smooth['walking'],
        name="navodila za hojo (Apple zemljevidi)",
        marker_color=barve[1]
    ))
    fig.add_trace(go.Line(
        x=smooth.index,
        y=smooth['aktivni'],
        name="aktivni uporabniki (Geocaching)",
        marker_color=barve[3]
    ))
    newstyle(fig)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    #fig.write_image("temp.png")
    fig.show()

def izrisi_covid_sledilnik_najdbe(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.date,
        y=df['cases.confirmed'],
        name="število potrjenih primerov (COVID-19 sledilnik)",
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.date,
        y=df['stNajdb'],
        name="število najdb zakladov (Geocaching)",
        marker_color=barve[3]
    ))
    fig.add_trace(go.Line(
        x=df.date,
        y=df['cepljeni'],
        name="število cepljenih x 1000 (COVID-19 sledilnik)",
        marker_color=barve[5]
    ))
    newstyle(fig)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    #fig.write_image("temp.png")
    fig.show()

def izrisi_covid_sledilnik_aktivni(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.date,
        y=df['cases.confirmed'],
        name="potrjeni primeri",
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.date,
        y=df['aktivni'],
        name="aktivni igralci",
        marker_color=barve[3]
    ))
    fig.update_layout(title_text="COVID-19 Sledilnik")
    fig.show()

def izrisi_google_mobility(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.index,
        y=df['retail_and_recreation_percent_change_from_baseline'],
        name="retail and recreation (Google Mobility Trends)",
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['grocery_and_pharmacy_percent_change_from_baseline'],
        name="grocery and pharmacy (Google Mobility Trends)",
        marker_color=barve[1]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['parks_percent_change_from_baseline'],
        name="parks (Google Mobility Trends)",
        marker_color=barve[2]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['transit_stations_percent_change_from_baseline'],
        name="transit stations (Google Mobility Trends)",
        marker_color=barve[6]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['workplaces_percent_change_from_baseline'],
        name="workplaces (Google Mobility Trends)",
        marker_color="#c7a881"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['residential_percent_change_from_baseline'],
        name="residential (Google Mobility Trends)",
        marker_color="#CF9300"
    ))
    newstyle(fig)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    #fig.write_image("temp.png")
    fig.show()

def izrisi_google_mobility_aktivni(df):
    fig = go.Figure()
    fig.add_trace(go.Line(
        x=df.index,
        y=df['retail_and_recreation_percent_change_from_baseline'],
        name="retail and recreation (Google Mobility Trends)",
        opacity=0.7,
        marker_color=barve[0]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['grocery_and_pharmacy_percent_change_from_baseline'],
        name="grocery and pharmacy (Google Mobility Trends)",
        opacity=0.7,
        marker_color=barve[1]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['parks_percent_change_from_baseline'],
        name="parks (Google Mobility Trends)",
        opacity=0.7,
        marker_color=barve[2]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['transit_stations_percent_change_from_baseline'],
        name="transit stations (Google Mobility Trends)",
        opacity=0.7,
        marker_color=barve[6]
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['workplaces_percent_change_from_baseline'],
        name="workplaces (Google Mobility Trends)",
        opacity=0.7,
        marker_color="#c7a881"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['residential_percent_change_from_baseline'],
        name="residential (Google Mobility Trends)",
        opacity=0.7,
        marker_color="#CF9300"
    ))
    fig.add_trace(go.Line(
        x=df.index,
        y=df['aktivni'],
        name="aktivni uporabniki (Geocaching)" ,
        marker_color=barve[3]
    ))
    newstyle(fig)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    #fig.write_image("temp.png")
    fig.show()

def trendSkupin(df):
    fig = go.Figure()
    interval = ['Pred COVID-19','Čas ukrepov']
    i = 1
    for index, row in df.iterrows():
        if (i==10): break
        skupina = row['skupina']
        skupina = set(ast.literal_eval(skupina))
        if (len(skupina) == 2):
            label = str(len(skupina)) + ' igralca'
        elif (len(skupina) == 3 or len(skupina) == 4):
            label = str(len(skupina)) + ' igralci'
        elif (len(skupina) == 5):
            label = str(len(skupina)) + ' igralcev'
        fig.add_trace(go.Line(
            x=interval,
            y=np.fromiter([row['pred'], row['covid']], dtype=int),
            name=label,
            marker_color=barve[len(skupina)]
        ))
        i += 1
    newstyle(fig)
    fig.update_yaxes(title_text='Število najdb')
    #fig.write_image("temp.png")
    fig.show()