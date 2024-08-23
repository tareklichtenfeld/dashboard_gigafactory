import streamlit as st
import pandas as pd
import numpy as np
import plost
from PIL import Image
from statistics import mean
from datetime import datetime
from meteostat import Hourly, Stations
from streamlit_modal import Modal
from sankeyflow import Sankey
import matplotlib.pyplot as plt
import io

# Page setting
st.set_page_config(page_title="Gigafactory-Skaleriungstool",
                   layout="wide",
                   page_icon=":battery:")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#sidebar
st.sidebar.header('Gigafactory `Builder`')
st.sidebar.subheader('selectable planning parameters')
location = st.sidebar.selectbox('location', ('Germany', 'Norway', 'Texas, USA', 'Mexico', 'Chile', 'Brasil', 'Qatar', 'Greenville, South Carolina' ))
production_capacity= st.sidebar.slider('production capacity [GWh/a]', 2, 150, 40)
cell_format = st.sidebar.selectbox('cell format', ('Pouch', 'Rund', 'Prismatisch'))
automation_degree = st.sidebar.selectbox('degree of automation',('Niedrig','Mittel','Hoch'))
production_setup = st.sidebar.selectbox('cell chemistry',('NMC 811','NCA...'))
production_days = st.sidebar.slider('production days per year', 1, 315, 315)
energy_concept = st.sidebar.selectbox('energy concept', ('Erdgas-Kessel', 'Blockheizkraftwerk', 'Wärmepumpe', 'Kombi-Wärmepumpe')) 
st.sidebar.subheader('Developer Options')
year = st.sidebar.slider('year of production', 2003, 2023, 2023)


st.sidebar.markdown('''
---
Created by Tarek Lichtenfeld :)
''')


#-----popup when opening
modal = Modal(
    "Tutorial", 
    key="demo-modal",
    
    # Optional
    padding=20,    # default value
    max_width=744  # default value
)

open_modal = st.button("First Time?")
if open_modal:
    modal.open()

if modal.is_open():
    with modal.container():
        st.write("Hey there 👋🏻")
        st.write("I'm Tarek and I created this interactive dashboard to visualize and compare the power-input and -output of gigafactories for battery cell production. The sidebar on the left side of the screen contains all the parameters that can be changed to your preferences. Do you want to build a 100 GWh gigafactory on the Bahamas but you want low carbon dioxide emissions? Just choose the location and energy concept and you'll immediately notice the drastic impact your decisions have on the power consumption. Feel free to play around and test out the countless combinations of input parameters.")
        st.write("Enjoy :)")
        
        close_modal = st.button("Let's do this")
        if close_modal:
            modal.close()





#---------------------------WEATHER DATA-----------------------------------------------
#-----assort coordinates to locations

def get_coordinates(location):
    coordinates_dict = {
        'Germany': (51.962099672722246, 7.6260690597081355),
        'Norway': (69.65083068941327, 18.95616203587009),
        'Texas, USA': (35.19429133374373, -101.85247871892864),
        'Mexico': (25.690794191837405, -100.31597776954884),
        'Chile': (-22.46061693078931, -68.92687992157762),
        'Brasil': (2.8168900489923048, -60.68063433499766),
        'Qatar': (25.253853158779187, 51.34762132032399),
        'Russia': (53.7057509164329, 91.39067030182092),
        'Greenville, South Carolina': (34.849191725553155, -82.39028917600623)
    }
    return coordinates_dict.get(location, None)


#-----get coordinates from chosen location-------------------
latitude, longitude = get_coordinates(location)

#----Choose date from sidebar----------------------------------------

#----start_date----------------------
def get_start_dates(date):
    dates_dict = {}
    for year in range(date, 1989, -1):  # Rückwärts iterieren von 'date' bis 1990
        dates_dict[str(year)] = (year, 1, 1)
    return dates_dict.get(str(date), (2023,1,1))

#-----end date------------------------
def get_end_dates(date):
    dates_dict = {}
    for year in range(date, 1989, -1):  # Rückwärts iterieren von 'date' bis 1990
        dates_dict[str(year)] = (year, 12, 31)
    return dates_dict.get(str(date), (2023,12,31))

#-----get dates from chosen year---------------------------------
y1, m1, d1 = get_start_dates(year)
y2, m2, d2 = get_end_dates(year)




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
  start_date = datetime(y1, m1, d1)  # Change year, month, day as needed
  end_date = datetime(y2, m2, d2)  # Change year, month, day as needed
  data = Hourly(f"{station_id}", start_date, end_date)
  data = data.fetch()

  station_rhum_data = data[weather_param].tolist()
  ypoints.append(station_rhum_data)

#-----weather param temperature---------------------------------
weather_param = 'temp'

ypoints = []
for station_name, station_id in stat:
  # Download hourly data for a specific date range (adjust dates as needed)
  start_date = datetime(y1, m1, d1)  # Change year, month, day as needed
  end_date = datetime(y2, m2, d2)  # Change year, month, day as needed
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
  start_date = datetime(y1, m1, d1)  # Change year, month, day as needed
  end_date = datetime(y2, m2, d2)  # Change year, month, day as needed
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
strom_wp_k_end = []
strom_wp_w_end = []
brennstoff_w_end = []
strom_electr_end = []

# make list with hours--------------------------------------
station_time_data = list(range(len(t)))


#---------------------------FORMULAS----------------------------------------------------------------------------
production_day_factor = production_days/365

#-----Anschlussleistung (Demo für Finn)-------------------------
def Anschlussleistung(x):
    return x*6.25

#-----RLT/HVAC Energieverbrauch-------------------------------------------------
#-----RLT Kältelast---------------------------------------------
def RLT_Kaeltelast(x):
    return 1.920*x
    
#-----RLT Wärmelast---------------------------------------------
def RLT_Waermelast(x):
    return 0.6867*x

#-----RLT Stromlast---------------------------------------------
def RLT_Stromlast(x):
    return 1.529*x


#-----MITARBEITENDE-----------------------------------------------------------
#MA pro GWh!!!!!!!!!!!!!!!!!!!!!
def MA_pro_GWh(x):
    return x

# a3.metric("Mitarbeitende im Trockenraum", f"{round(MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format)),0)} MA")
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
#-----Elektrische Last--------------------------------------------
def Prozess_Stromnutzlast(x):
    day_factor=315/315
    if cell_format == 'Pouch':
        return 25.86493*x*day_factor
    if cell_format == 'Rund':
        return 26.59484*x*day_factor
    if cell_format == 'Prismatisch':
        return 29.58601*x*day_factor
    
#-----Kälte-Nutzlast--------------------------------------------
def Prozess_Kaeltenutzlast(x):
    day_factor=315/315
    if cell_format == 'Pouch':
        return 8.14149*x*day_factor
    if cell_format == 'Rund':
        return 9.60784*x*day_factor
    if cell_format == 'Prismatisch':
        return 13.00309*x*day_factor
    

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
def bhkw_w_wirkungsgrad(x):
    n = 0.9
    return x/n

def bhkw_s_wirkungsgrad(x):
    n = 0.05
    return x*n

#-----Konzept 3 - Wärmepumpe--------------------------------------------
def strom_cop(n_c, waerme):
    end_waermeleistung = waerme/n_c
    return(end_waermeleistung)

#-----Konzept 4 - Kombi-WP----------------------------------------------
def kombi_wp_w_end(x):
    cop_kwp=5.7396
    return x/cop_kwp

def kombi_wp_k_end(x):
    cop_kkm=6.1
    return x/cop_kkm


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
    strom_wp_k_end.append(strom_eert(eert_val, cool_val))
    
    #Wärmepumpe
    #End-Wärmeleistung berechnen
    strom_wp_w_end.append(strom_cop(cop_val, heat_val))
    
    #Brennwertkessel
    brennstoff_w_end.append(brennwertkessel_wirkungsgrad(heat_val))
    
    #Strom
    strom_electr_end.append(electr_full_dp60_2rotor())



#-----Durchschnittswerte der Effizienz--------------------------------------------------------------------------------
cop_avg = mean(cop_data)
eer_avg = mean(eert_data)
cop_kkm = 6.1

#---------------------BERECHNUNG DER ENDLAST ZUM GESAMTENERGIEBEDARF----------------------------------------------------------------
#-----REIN_ UND TROCKENRAUM--------------------------------------------------------------------------------------------
#-----Kälte RuT gesamt ausgeben-------------------------------------------------------------------------
RuT_GWh_k_nutz = sum(cool_data)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor

if energy_concept == 'Kombi-Wärmepumpe':
    RuT_GWh_k_end = kombi_wp_k_end(RuT_GWh_k_nutz)
else:
    RuT_GWh_k_end = sum(strom_wp_k_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor

#-----Wärme RuT gesamt ausgeben--------------------------------------------------------------------------
RuT_GWh_w_nutz = sum(heat_data)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor

if energy_concept == 'Erdgas-Kessel':
    RuT_GWh_w_end = sum(brennstoff_w_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor
if energy_concept == 'Blockheizkraftwerk':
    RuT_GWh_w_end = bhkw_w_wirkungsgrad(RuT_GWh_w_nutz)
if energy_concept == 'Wärmepumpe':
    RuT_GWh_w_end = sum(strom_wp_w_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor
if energy_concept == 'Kombi-Wärmepumpe':
    RuT_GWh_w_end = kombi_wp_w_end(RuT_GWh_w_nutz)


#-----Strom RuT gesamt ausgeben--------------------------------------------------------------------------
RuT_GWh_s_nutz = sum(strom_electr_end)/10**6 * (MA_nach_Automatisierungsgrad(MA_in_RuT(production_capacity, cell_format))/2)*production_day_factor

if energy_concept == 'Blockheizkraftwerk':
    RuT_GWh_s_end = RuT_GWh_s_nutz - bhkw_s_wirkungsgrad(RuT_GWh_s_nutz)
else:
    RuT_GWh_s_end = RuT_GWh_s_nutz

#------Gesamtenergiemenge RuT ausgeben-------------------------------------------------------------------
RuT_GWh_kum_ges = (RuT_GWh_k_end + RuT_GWh_w_end + RuT_GWh_s_end)






#------GEBÄUDETECHNIK------------------------------------------------------------------------------------------------
#-----Nutzlast-------------------------------------------------------------------------------------------
#-----       (INFO: RLT unabhängig von production days)       -------------------
RLT_GWh_k_nutz = RLT_Kaeltelast(production_capacity)
RLT_GWh_w_nutz = RLT_Waermelast(production_capacity)
RLT_GWh_s_nutz = RLT_Stromlast(production_capacity)

#-----Endwärme---------------------------------------------------------------------
if energy_concept == 'Kombi-Wärmepumpe':
    RLT_GWh_k_end = kombi_wp_k_end(RLT_GWh_k_nutz)
else:
    RLT_GWh_k_end = strom_eert(eer_avg, RLT_GWh_k_nutz)

#-----Endkälte---------------------------------------------------------------------
if energy_concept == 'Erdgas-Kessel':
    RLT_GWh_w_end = brennwertkessel_wirkungsgrad(RLT_GWh_w_nutz)
if energy_concept == 'Blockheizkraftwerk':
    RLT_GWh_w_end = bhkw_w_wirkungsgrad(RLT_GWh_w_nutz)
if energy_concept == 'Wärmepumpe':
    RLT_GWh_w_end = RLT_GWh_w_nutz/cop_avg
if energy_concept == 'Kombi-Wärmepumpe':
    RLT_GWh_w_end = kombi_wp_w_end(RLT_GWh_w_nutz)

#-----Endstrom-------------------------------------------------------------------
if energy_concept == 'Blockheizkraftwerk':
    RLT_GWh_s_end = RLT_GWh_s_nutz - bhkw_s_wirkungsgrad(RLT_GWh_s_nutz)
else:
    RLT_GWh_s_end = RLT_GWh_s_nutz




#-----PROZESSE-------------------------------------------------------------------------------------------
#-----Nutzlast---------------------------------------------------------------------
PRO_GWh_k_nutz = Prozess_Kaeltenutzlast(production_capacity)*production_day_factor
PRO_GWh_s_nutz = Prozess_Stromnutzlast(production_capacity)*production_day_factor

#-----Endkälte--------------------------------------------------------------------
if energy_concept == 'Kombi-Wärmepumpe':
    PRO_GWh_k_end = kombi_wp_k_end(PRO_GWh_k_nutz)
else:
    PRO_GWh_k_end = strom_eert(eer_avg, PRO_GWh_k_nutz)


#-----Endstrom-------------------------------------------------------------------
if energy_concept == 'Blockheizkraftwerk':
    PRO_GWh_s_end = PRO_GWh_s_nutz - bhkw_s_wirkungsgrad(RLT_GWh_s_nutz)
else:
    PRO_GWh_s_end = PRO_GWh_s_nutz





#-----------GESAMTFACTORY ENERGIEVERBRÄUCHE---------------------------------------------------------------------------
#-----Nutzlast Gesamtfabrik---------------------------------------------------
gesamtfabrik_k_nutz = (RuT_GWh_k_nutz+PRO_GWh_k_nutz+RLT_GWh_k_nutz)
gesamtfabrik_w_nutz = (RuT_GWh_w_nutz+RLT_GWh_w_nutz)
gesamtfabrik_s_nutz = (RuT_GWh_s_nutz+PRO_GWh_s_nutz+RLT_GWh_s_nutz)

gesamtfabrik_ges_nutz = gesamtfabrik_k_nutz + gesamtfabrik_w_nutz + gesamtfabrik_s_nutz

#-----Endlast Gesamtfabrik----------------------------------------------------
gesamtfabrik_k_end = (RuT_GWh_k_end+PRO_GWh_k_end+RLT_GWh_k_end)
gesamtfabrik_w_end = (RuT_GWh_w_end+RLT_GWh_w_end)
gesamtfabrik_s_end = (RuT_GWh_s_end+PRO_GWh_s_end+RLT_GWh_s_end)

gesamtfabrik_ges_end = gesamtfabrik_k_end + gesamtfabrik_w_end + gesamtfabrik_s_end

#-----Gesamtfabrik Daten & Werte----------------------------------------------
energiefaktor = gesamtfabrik_ges_nutz/production_capacity


#-----Emissionen--------------------------------------------------------------------------------
def co2_natual_gas(x):
    kg_co2_GWh = 0.24 * 10**6
    return(kg_co2_GWh * x)

def co2_electric(x):
    kg_co2_GWh=5
    return(x*kg_co2_GWh)

if energy_concept=="Erdgas-Kessel":
    natural_gas_usage=gesamtfabrik_w_end
if energy_concept=="Blockheizkraftwerk":
    natural_gas_usage=gesamtfabrik_w_end+bhkw_s_wirkungsgrad(RLT_GWh_s_nutz)
else:
    natural_gas_usage=0

#-----TOTAl------
natural_gas_emissions_tons=co2_natual_gas(natural_gas_usage)/10**3


#--------------------DATA VISUALIZER-----------------------------------------------------------------------------------
#-----Row A-----------------------------------------------------------------
a1, a2, a3 = st.columns(3)
a1.image(Image.open('streamlit-logo-secondary-colormark-darktext.png'))
a2.metric("energy factor", f"{round(energiefaktor,2)} kWh/kWhcell")
a3.metric("Total energy output", f"{round(gesamtfabrik_ges_nutz,2)} GWh/a")

#-----Row B-----------------------------------------------------------------
b1, b2, b3, b4 = st.columns(4)
b1.metric("Heat energy output",f"{round(gesamtfabrik_w_nutz,2)} GWh/a")
b2.metric("cooling energy output",f"{round(gesamtfabrik_k_nutz,2)} GWh/a")
b3.metric("electrical energy output",f"{round(gesamtfabrik_s_nutz,2)} GWh/a")
b4.metric("Total energy input",f"{round(gesamtfabrik_ges_end,2)} GWh/a")


#-----row b2---------------------------------------------------------------
b5, b6, b7 = st.columns(3)
b5.metric("CO2-emissions",f"{round(natural_gas_emissions_tons,1)} tons")
b6.metric("useful cooling load",f"{round(gesamtfabrik_k_nutz,2)} GWh/a")
b7.metric("electrical energy usage",f"{round(gesamtfabrik_s_nutz,2)} GWh/a")


#-----Row C-----------------------------------------------------------------
Nutzlastdiagramm = pd.DataFrame({
    "name": ["cooling usage","heat usage", "eletric energy usage"],
    "useful energy": [ gesamtfabrik_k_nutz, gesamtfabrik_w_nutz, gesamtfabrik_s_nutz],
    "color": ["#779ecb","#89e894", "#ff6961"]
})



c1, c2= st.columns(2)
with c1:
    st.markdown("**shares of energy usage**")
    st.bar_chart(
        data=Nutzlastdiagramm,
        x="name",
        y="useful energy",
        color="color"
    )

#---------Row D - SANKEY DIAGRAM-----------------------------------------------------
#-----define sankey states-------------------------------------------------------
    if energy_concept == "Erdgas-Kessel":
        df = pd.DataFrame(
            {
                "source": ["Electricity", "Manufacturing", "Manufacturing","Electricity", "Natural Gas", "Building", "Building", "Building","Electricity", "Natural Gas", "Dry Room","Dry Room", "Dry Room"],
                "target": ["Manufacturing", "Electric Energy usage", "Cooling usage", "Building", "Building", "Cooling usage", "Electric Energy usage", "Heat usage", "Dry Room", "Dry Room", "Cooling usage", "Electric Energy usage", "Heat usage"],
                "value": [(PRO_GWh_s_end+PRO_GWh_k_end), PRO_GWh_s_nutz, PRO_GWh_k_nutz, (RLT_GWh_k_end+RLT_GWh_s_end), RLT_GWh_w_end, RLT_GWh_k_nutz, RLT_GWh_s_nutz, RLT_GWh_w_nutz, (RuT_GWh_k_end+RuT_GWh_s_end), RuT_GWh_w_end, RuT_GWh_k_nutz, RuT_GWh_s_nutz, RuT_GWh_w_nutz],
            }
        )
    if energy_concept == "Blockheizkraftwerk":
        df = pd.DataFrame(
            {
                "source": ["Electricity", "Manufacturing", "Manufacturing","Electricity", "Natural Gas", "Building", "Building", "Building","Electricity", "Natural Gas", "Dry Room","Dry Room", "Dry Room"],
                "target": ["Manufacturing", "Electric Energy usage", "Cooling usage", "Building", "Building", "Cooling usage", "Electric Energy usage", "Heat usage", "Dry Room", "Dry Room", "Cooling usage", "Electric Energy usage", "Heat usage"],
                "value": [(PRO_GWh_s_end+PRO_GWh_k_end), PRO_GWh_s_nutz, PRO_GWh_k_nutz, (RLT_GWh_k_end+RLT_GWh_s_end), RLT_GWh_w_end, RLT_GWh_k_nutz, RLT_GWh_s_nutz, RLT_GWh_w_nutz, (RuT_GWh_k_end+RuT_GWh_s_end), RuT_GWh_w_end, RuT_GWh_k_nutz, RuT_GWh_s_nutz, RuT_GWh_w_nutz],
            }
        )
    if energy_concept == "Wärmepumpe":
        df = pd.DataFrame(
            {
                "source": ["Electricity", "Manufacturing", "Manufacturing","Electricity", "Building", "Building", "Building","Electricity", "Dry Room","Dry Room", "Dry Room"],
                "target": ["Manufacturing", "Electric Energy usage", "Cooling usage", "Building", "Cooling usage", "Electric Energy usage", "Heat usage", "Dry Room", "Cooling usage", "Electric Energy usage", "Heat usage"],
                "value": [(PRO_GWh_s_end+PRO_GWh_k_end), PRO_GWh_s_nutz, PRO_GWh_k_nutz, (RLT_GWh_k_end+RLT_GWh_s_end+RLT_GWh_w_end), RLT_GWh_k_nutz, RLT_GWh_s_nutz, RLT_GWh_w_nutz, (RuT_GWh_k_end+RuT_GWh_s_end+RuT_GWh_w_end), RuT_GWh_k_nutz, RuT_GWh_s_nutz, RuT_GWh_w_nutz],
            }
        )
        
    if energy_concept == "Kombi-Wärmepumpe":
        df = pd.DataFrame(
            {
                "source": ["Electricity", "Manufacturing", "Manufacturing","Electricity", "Building", "Building", "Building","Electricity", "Dry Room","Dry Room", "Dry Room"],
                "target": ["Manufacturing", "Electric Energy usage", "Cooling usage", "Building", "Cooling usage", "Electric Energy usage", "Heat usage", "Dry Room", "Cooling usage", "Electric Energy usage", "Heat usage"],
                "value": [(PRO_GWh_s_end+PRO_GWh_k_end), PRO_GWh_s_nutz, PRO_GWh_k_nutz, (RLT_GWh_k_end+RLT_GWh_s_end+RLT_GWh_w_end), RLT_GWh_k_nutz, RLT_GWh_s_nutz, RLT_GWh_w_nutz, (RuT_GWh_k_end+RuT_GWh_s_end+RuT_GWh_w_end), RuT_GWh_k_nutz, RuT_GWh_s_nutz, RuT_GWh_w_nutz],
            }
        )


def draw_sankey(df):
    flows = list(df[["source", "target", "value"]].itertuples(index=False, name=None))
    # remove empty and nan values
    flows_clean = [x for x in flows if x[0] and x[1] and x[2] > 0]

    diagram = Sankey(
        flows=flows_clean,
        cmap=plt.get_cmap("Pastel1"),
        flow_color_mode="source",
        node_opts={"label_opts": {"fontsize": 7, "fontname": "monospace"}},  # Set font to monospace
        flow_opts={"curvature": 8/10},
    )
    _, col2, _ = st.columns([1, 7, 1])
    with col2:
        diagram.draw()
        st.pyplot(plt)
        img = io.BytesIO()
        plt.savefig(img, format="png")
        st.session_state.image = img
 
 
def empty_df():
    df = pd.DataFrame({"source": [""], "target": [""], "value": [None]})
    st.session_state.df = df.astype({"value": float})
 
 
def timestamp():
    return pd.Timestamp.now().strftime("%Y%m%d%H%M%S")
 
sankey_placeholder = st.empty()
#-----draw sankey plot ---------------------------------------------------
st.markdown("**Sankey-plot**")
draw_sankey(df)
#--------------------------by tarek lichtenfeld, august 2024------------------------------------