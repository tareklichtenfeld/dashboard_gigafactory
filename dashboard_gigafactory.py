import streamlit as st
import pandas as pd
import numpy as np
import plost
from PIL import Image
from statistics import mean
from datetime import datetime
from meteostat import Hourly, Stations

# Page setting
st.set_page_config(page_title="Gigafactory-Skaleriungstool",
                   layout="wide",
                   page_icon=":battery:")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#sidebar
st.sidebar.header('Dashboard `Skalierbare Gigafactory`')

st.sidebar.subheader('Wählbare Planungsparameter')
location = st.sidebar.selectbox('Standort', ('Deutschland', 'Norwegen', 'Texas, USA', 'Mexiko', 'Chile', 'Brasilien', 'Katar' ))
production_capacity= st.sidebar.slider('Produktionskapazität in GWh/a', 2, 200, 40)
energy_concept = st.sidebar.selectbox('Energiekonzept', ('Erdgas-Kessel', 'Blockheizkraftwerk', 'Wärmepumpe', 'Kombi-Wärmepumpe')) 
cell_format = st.sidebar.selectbox('Zellformat', ('Pouch', 'Rund', 'Prismatisch'))
production_setup = st.sidebar.selectbox('Art der Fertigung',('State of the Art','Next Gen'))
automation_degree = st.sidebar.selectbox('Automatisierungsgrad',('Niedrig','Mittel','Hoch'))


st.sidebar.markdown('''
---
Created by Tarek Lichtenfeld :)
''')






#---------------------------WEATHER DATA-----------------------------------------------
#-----assort coordinates to locations

def get_coordinates(location):
    coordinates_dict = {
        'Deutschland': (51.962099672722246, 7.6260690597081355),
        'Norwegen': (69.65083068941327, 18.95616203587009),
        'Texas, USA': (35.19429133374373, -101.85247871892864),
        'Mexiko': (25.690794191837405, -100.31597776954884),
        'Chile': (-22.46061693078931, -68.92687992157762),
        'Brasilien': (2.8168900489923048, -60.68063433499766),
        'Katar': (25.253853158779187, 51.34762132032399),
        'Russland': (53.7057509164329, 91.39067030182092)
    }
    return coordinates_dict.get(location, None)

#-----get coordinates from chosen location-------------------
latitude, longitude = get_coordinates(location)

#-----GET WEATHER DATA---------------------------------------
stations = Stations()
stations = stations.nearby(latitude, longitude)
station = stations.fetch(1)
station['id']=station.index
stat=[]
for sta in range(1):
    stat.append([station['name'][sta],station['id'][sta]])

#-----weather param humidity---------------------------------
weather_param = 'rhum'

ypoints = []
for station_name, station_id in stat:
  # Download hourly data for a specific date range (adjust dates as needed)
  start_date = datetime(2023, 1, 1)  # Change year, month, day as needed
  end_date = datetime(2024, 12, 31)  # Change year, month, day as needed
  data = Hourly(f"{station_id}", start_date, end_date)
  data = data.fetch()

  station_rhum_data = data[weather_param].tolist()
  ypoints.append(station_rhum_data)

#-----weather param temperature---------------------------------
weather_param = 'temp'

ypoints = []
for station_name, station_id in stat:
  # Download hourly data for a specific date range (adjust dates as needed)
  start_date = datetime(2023, 1, 1)  # Change year, month, day as needed
  end_date = datetime(2024, 1, 1)  # Change year, month, day as needed
  data = Hourly(f"{station_id}", start_date, end_date)
  data = data.fetch()

  station_temp_data = data[weather_param].tolist()
  modified_data = []  # Create a new list to store modified temperature values
  for temp in station_temp_data:
    kelvin_temp = temp + 273.15
    modified_data.append(kelvin_temp)

#-----weather param pressure------------------------------------
weather_param = 'pres'

ypoints = []
for station_name, station_id in stat:
  # Download hourly data for a specific date range (adjust dates as needed)
  start_date = datetime(2023, 1, 1)  # Change year, month, day as needed
  end_date = datetime(2024, 1, 1)  # Change year, month, day as needed
  data = Hourly(f"{station_id}", start_date, end_date)
  data = data.fetch()

  station_pres_data = data[weather_param].tolist()
  ypoints.append(station_pres_data)






#---------------------------DEFINING LISTS---------------------------------------------
t = [float(value) for value in station_temp_data]
rhum = [float(value) for value in station_rhum_data]
pres = [float(value) for value in station_pres_data]
t_kelvin = [float(value) for value in modified_data]
f_abs = []
cool_data = []
heat_data = []
cop_data = []
eert_data = []
strom_k_end = []
strom_w_end = []
brennstoff_w_end = []
strom_electr_end = []







#---------------------------FORMULAS----------------------------------------------------------------------------

#-----Anschlussleistung (Test für Finn)-------------------------
def Anschlussleistung(x):
    return x*6.25

#-----MITARBEITENDE---------------------------------------------------------
#MA pro GWh
def MA_pro_GWh(x):
    return x

#MA in RuT nach Produktionskapazität (längere Formel)--------
#def MA_in_RuT(x):
    if cell_format == 'Pouch':
        return x*27*0.83
    if cell_format == 'Rund':
        return x*27
    if cell_format == 'Prismatisch':
        return x*27*1.225
    else:
        return x*27

#MA in RuT nach Produktionskapazität-------------------------
def MA_in_RuT(x, cell_format):
    factors = {
        "Pouch": 0.83,
        "Rund": 1.0,
        "Prismatisch": 1.225
    }
    return x * 27 * factors.get(cell_format, 1.0)

#MA Umrechnung nach Automatisierungsgrad--------------------
def MA_nach_Automatisierungsgrad(x2):
    if automation_degree == 'Niedrig':
        return x2*1.2
    if automation_degree == 'Mittel':
        return x2
    if automation_degree == 'Hoch':
        return x2*0.8
    else:
        return x2


#-----PROZESSENERGIE--------------------------------------------------------


#-----REIN-UND TROCKENRAUM--------------------------------------------------
#-----absolute Feuchte----------------------------------------
def hum_abs(temp_val, rhum_val, pres_val):
    K1 = 6.112
    K2 = 17.62
    K3 = 243.12
    
    p_s = K1*np.exp(K2*temp_val/(K3+temp_val))*(rhum_val/100)
    x = 1000*(p_s/(pres_val-p_s)*0.622)
    if x>7.6:
        return(7.6)
    else:
        return(float(x))

#-----FULL DP 60 2 ROTOR--------------------------------------
def cool_full_dp60_2rotor(x, y):
    
    p00=131.8
    p10=-1.526
    p01=1.12
    p20=0.03284
    p11=-0.1051
    p02=-0.1936
    p30=0.000924
    p21=-0.001409
    p12=0.0371
    p03=-0.03555
    p40=-0.00002705
    p31=0.0001107
    p22=-0.0009098
    p13=0.0005325
    p04=0.00131
    
    return(p00+p10*x+p01*y+p20*x**2+p11*x*y+p02*y**2+p30*x**3+p21*x**2*y+p12*x*y**2+p03*y**3+p40*x**4+p31*x**3*y+p22*x**2*y**2+p13*x*y**3+p04*y**4)

def heat_full_dp60_2rotor(x,y):
    
    p00 =       101.7
    p10 =     0.08791
    p01 =       3.367
    p20 =     0.03407 
    p11 =     -0.1347 
    p02 =      0.6819 
    p30 =   0.0009921  
    p21 =   -0.002345  
    p12 =     0.04728 
    p03 =     -0.1927 
    p40 =  -2.852e-05
    p31 =   0.0001195 
    p22 =   -0.000903 
    p13 =  -6.901e-05
    p04 =     0.01073 

    return(p00 + p10*x + p01*y + p20*x**2 + p11*x*y + p02*y**2 + p30*x**3 + p21*x**2*y + p12*x*y**2 + p03*y**3 + p40*x**4 + p31*x**3*y + p22*x**2*y**2 + p13*x*y**3 + p04*y**4)

def electr_full_dp60_2rotor():
    return(73)



#------------------------ENERGIEKONZEPTE--------------------------------------------------------
#-----WIRKUNGSGRADE--------------------------------------------------------------
#-----Carnot-Formel 85 Grad Vorlauf----------------------------------
def cop(K):
    t_h=358.15
    real_faktor=0.625
    if K>(t_h+0.2):
        return 1e3
    else:
        n_c=t_h/(t_h-K)
        n_c_real=n_c*real_faktor
        return(n_c_real)
    
#-----EERT Tischrückkühler trocken-----------------------------------
def eert(K):
    if K>312.15:
        return 14
    else:
        e=-24.067*K + 7526.4
        return(e)



#-----BERECHNUNG ENDLAST-------------------------------------------------------
#-----Kälteerzeugung KKM
def strom_eert(e, kaelte):
    cop_kkm = 6.1
    end_kaelteleistung = kaelte/cop_kkm + kaelte/e
    return(end_kaelteleistung)

#-----Konzept 1 - Brennwertkessel---------------------------------------
def brennwertkessel_wirkungsgrad(heat):
    n = 0.95
    end_waermelast = heat/n
    return(end_waermelast)

#-----Konzept 2 - BHKW--------------------------------------------------
#-----Konzept 3 - Wärmepumpe--------------------------------------------
def strom_cop(n_c, waerme):
    end_waermeleistung = waerme/n_c
    return(end_waermeleistung)

#-----Konzept 4 - Kombi-WP----------------------------------------------








#---------------------DURCHLAUFEN DER FORMELN ZUR BESTIMMUNG DES LASTVERLAUFS------------------------------------------------------

for i in range(len(t)):
    
    # Extract a pair of values for each iteration
    temp_val = t[i]
    rhum_val = rhum[i]
    pres_val = pres[i]
    t_k = t_kelvin[i]
    
    #Absolute Feuchte berechnen
    hum_abs_val = hum_abs(temp_val, rhum_val, pres_val)
    f_abs.append(hum_abs_val)
    
    #EERT-Wert berechnen
    eert_val = eert(t_k)
    eert_data.append(eert_val)
    
    #COP-Wert berechnen
    cop_val = cop(t_k)
    cop_data.append(cop_val)
    
    #Kälteleistung berechnen
    cool_val = cool_full_dp60_2rotor(temp_val, hum_abs_val)
    cool_data.append(cool_val)
    
    #Wärmeleistung berechnen
    heat_val = heat_full_dp60_2rotor(temp_val, hum_abs_val)
    heat_data.append(heat_val)
    
    #End-Kühlleistung berechnen
    strom_k_end.append(strom_eert(eert_val, cool_val))
    
    #Wärmepumpe
    #End-Wärmeleistung berechnen
    strom_w_end.append(strom_cop(cop_val, heat_val))
    
    #Brennwertkessel
    brennstoff_w_end.append(brennwertkessel_wirkungsgrad(heat_val))
    
    #Strom
    strom_electr_end.append(electr_full_dp60_2rotor())





#---------------------BERECHNUNG DER ENDLAST ZUM GESAMTENERGIEBEDARF----------------------------------------------------------------

kWh_k_nutz = sum(cool_data)
GWh_k_nutz = sum(cool_data)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)
kWh_k_end = sum(strom_k_end)
GWh_k_end = sum(strom_k_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)

#Wärme gesamt ausgeben
kWh_w_nutz = sum(heat_data)
GWh_w_nutz = sum(heat_data)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)
kWh_w_end = sum(strom_w_end)
GWh_w_end = sum(strom_w_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)
kWH_w_end_kessel = sum(brennstoff_w_end)
GWH_w_end_kessel = sum(brennstoff_w_end)/10**6

#Strom gesamt ausgeben
kWh_s_ges = sum(strom_electr_end)
GWh_s_ges = sum(strom_electr_end)/10**6

#Gesamtenergiemenge ausgeben
GWh_kum_ges = ((kWh_k_end + kWh_w_end + kWh_s_ges)/10**6)

#Durchschnittswerte der Effizienz
cop_avg = mean(cop_data)
eer_avg = mean(eert_data)




# Data-----------------------------------------------------------------------------------
seattle_weather = pd.read_csv('https://raw.githubusercontent.com/tvst/plost/master/data/seattle-weather.csv', parse_dates=['date'])
stocks = pd.read_csv('https://raw.githubusercontent.com/dataprofessor/data/master/stocks_toy.csv')

# Row A
a1, a2, a3 = st.columns(3)
a1.image(Image.open('streamlit-logo-secondary-colormark-darktext.png'))
a2.metric("Anschlussleistung", f"{round(Anschlussleistung(production_capacity),3)} MW")
a3.metric("Mitarbeitende im Trockenraum", f"{round(MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format)),0)} MA")

# Row B
b1, b2, b3, b4 = st.columns(4)
b1.metric("Name der Wetterstation", f"{station_name}")
b2.metric("Nutz-Wärmebedarf des RuT",f"{round(GWh_w_nutz,3)} GWh/a")
b3.metric("End-Wärmebedarf des RuT",f"{round(GWh_w_end,3)} GWh/a")
b4.metric("Humidity", "86%", "4%")

# Row C
c1, c2 = st.columns((7,3))
with c1:
    st.markdown('### Heatmap')
    plost.time_hist(
    data=seattle_weather,
    date='date',
    x_unit='week',
    y_unit='day',
    color='temp_max',
    aggregate='median',
    legend=None)
with c2:
    st.markdown('### Bar chart')
    plost.donut_chart(
        data=stocks,
        theta='q2',
        color='company')