##############################################
#              Ethan Palmisano               #
#                                            #
#          Valparaiso University '28         #
#                                            #
#           Map-Maker Python Project         #
##############################################

# Import Statements

from datetime import datetime, timedelta, time
from io import StringIO
from urllib.request import urlopen

from metpy.io import metar
from metpy.plots import declarative
from metpy.units import units
import pandas as pd

from metpy.io import add_station_lat_lon
from siphon.simplewebservice.iastate import IAStateUpperAir


# Selecting Level of Atmosphere

user_pressure_lvl = input('Which level of the atmosphere would you like to map?' 'Available Options: Surface, 850mb, 700mb, 500mb, 300mb, 250mb''    ''>>>')
if user_pressure_lvl == 'Surface' or user_pressure_lvl == 'sfc' or user_pressure_lvl == 'surface':
    print('Selected: Surface')
    sfc_tf = True
    obslvl = 'sfc'
elif user_pressure_lvl == '850mb' or user_pressure_lvl == '850':
    print('Selected: 850mb')
    sfc_tf = False
    obslvl = 850
elif user_pressure_lvl == '700mb' or user_pressure_lvl == '700':
    print('Selected: 700mb')
    sfc_tf = False
    obslvl = 700
elif user_pressure_lvl == '500mb' or user_pressure_lvl == '500':
    print('Selected: 500mb')
    sfc_tf = False
    obslvl = 500
elif user_pressure_lvl == '300mb' or user_pressure_lvl == '300':
    print('Selected: 300mb')
    sfc_tf = False
    obslvl = 300
elif user_pressure_lvl == '250mb' or user_pressure_lvl == '250':
    print('Selected: 250mb')
    sfc_tf = False
    obslvl = 250
else:
    print('Not a viable option. Please run again.')
    quit()

# Selecting Date and Time

user_time = input('Select a date and time in [YYYYMMDDHHmm] format.''    ''>>>')

if (user_time) == 'test':
    year = 2025
    month = 1
    day = 1
    hour = 12
    minute = 0
    date = datetime(year,month,day,hour,minute)

elif len(user_time) == 12:
    year = int(user_time[0:4])
    month = int(user_time[4:6])
    day = int(user_time[6:8])
    hour = int(user_time[8:10])
    minute = int(user_time[10:12])
    date = datetime(year,month,day,hour,minute)
    if month <= 0 or month >= 13:
        print('Wrong format. Please try again.')
        quit()
    
    print(f'Date entered is {date:%D} at {hour}:{user_time[10:12]} UTC...')
else:
    print('Wrong format. Please try again.')
    quit()

# Remote Access - Archive Data Read with pandas from Iowa State Archive,
# note differences from METAR files

if sfc_tf == True:

    standard_obs_tf = input('Would you like the standard surface observation, or to use a specific parameter? For standard, type S, for a specific parameter, type O    >>>')

    # For Standard Surface Maps
    
    if standard_obs_tf == 'S' or standard_obs_tf =='s':

        dt = timedelta(minutes=30)
        sdate = date - dt
        edate = date + dt
        data_url = ('http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'
                    'data=all&tz=Etc/UTC&format=comma&latlon=yes&'
                    f'year1={sdate.year}&month1={sdate.month}&day1={sdate.day}'
                    f'&hour1={sdate.hour}&minute1={sdate.minute}&'
                    f'year2={edate.year}&month2={edate.month}&day2={edate.day}'
                    f'&hour2={edate.hour}&minute2={edate.minute}')
        data = pd.read_csv(data_url, skiprows=5, na_values=['M'],
                           low_memory=False).replace('T', 0.00001).groupby('station').tail(1)
        df = metar.parse_metar_file(StringIO('\n'.join(val for val in data.metar)),
                                    year=date.year, month=date.month)

        # User selected units
        
        user_temp_units = input('For Celcius or Fahrenheit, type C/F    >>>')

        if user_temp_units == 'C' or user_temp_units == 'c':
            df['tmpf'] = (df.air_temperature.values)
            df['dwpf'] = (df.dew_point_temperature.values)
        elif user_temp_units == 'F' or user_temp_units == 'f':
            df['tmpf'] = (df.air_temperature.values * units.degC).to('degF')
            df['dwpf'] = (df.dew_point_temperature.values * units.degC).to('degF')
        else:
            print('Please retry using the correct format.')
            quit()
        
        user_map_region = input('Input a viable code from https://unidata.github.io/MetPy/latest/api/areas.html to select where to plot your map.    >>>')

        # Correctly Formats Surface Data
        
        mslp_formatter = lambda v: format(v*10, '.0f')[-3:]

        # Plot desired data
        obs = declarative.PlotObs()
        obs.data = df
        obs.time = date
        obs.time_window = timedelta(minutes=15)
        obs.level = None
        obs.fields = ['cloud_coverage', 'tmpf', 'dwpf',
                      'air_pressure_at_sea_level', 'current_wx1_symbol']
        obs.locations = ['C', 'NW', 'SW', 'NE', 'W']
        obs.formats = ['sky_cover', None, None, mslp_formatter, 'current_weather']
        obs.reduce_points = 0.75
        obs.vector_field = ['eastward_wind', 'northward_wind']
        
        # Panel for plot with Map features
        panel = declarative.MapPanel()
        panel.layout = (1, 1, 1)
        panel.projection = 'lcc'
        panel.area = f'{user_map_region}'
        panel.layers = ['states']
        panel.plots = [obs]
        panel.left_title = 'Surface Observations'
        panel.right_title = f'Valid: {date:%Y-%m-%d %H00} UTC'
        
        # Bringing it all together
        pc = declarative.PanelContainer()
        pc.size = (10, 10)
        pc.panels = [panel]

        # Note that this saves the file to your maps directory. 
        #To save images to the same location you are in, remove "maps/" from the string.
        
        pc.show()
        pc.save(f'maps/{obslvl}_{user_map_region}_{date:%Y%m%d}_{date:%H}z.png', dpi=150, bbox_inches='tight')

    #For Non-Standard Surface Maps
    
    elif standard_obs_tf == 'O' or standard_obs_tf == 'o':
    
        dt = timedelta(minutes=30)
        sdate = date - dt
        edate = date + dt
        data_url = ('http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'
                    'data=all&tz=Etc/UTC&format=comma&latlon=yes&'
                    f'year1={sdate.year}&month1={sdate.month}&day1={sdate.day}'
                    f'&hour1={sdate.hour}&minute1={sdate.minute}&'
                    f'year2={edate.year}&month2={edate.month}&day2={edate.day}'
                    f'&hour2={edate.hour}&minute2={edate.minute}')
        data = pd.read_csv(data_url, skiprows=5, na_values=['M'],
                           low_memory=False).replace('T', 0.00001).groupby('station').tail(1)
        df = metar.parse_metar_file(StringIO('\n'.join(val for val in data.metar)),
                                    year=date.year, month=date.month)
        
        # Prints a long list of many different parameters that the user can choose from
        print(df.units)

        # And these need the user to correctly spell and type what they want
        user_map_parameter = input('Select one of the above to plot.    >>>')
    
        user_map_units = input('For the code to work, also type the units used with the parameter here.    >>>')
    
        user_map_region = input('Input a viable code from https://unidata.github.io/MetPy/latest/api/areas.html to select where to plot your map.    >>>')
    
        user_map_title = input("Lastly, input your parameter for your map's title here. (Tip: This will be printed as <your_title> on <date> at <time> UTC)    >>>")

        #### Used only for Valpo students if above websites are down
        
        # Local Access
        # data = f'/data/ldmdata/surface/sao/{date:%Y%m%d%H}_sao.wmo'
        # df = metar.parse_metar_file(data, year=date.year, month=date.month)
        
        obs = declarative.PlotObs()
        obs.data = df
        obs.time = date
        obs.time_window = timedelta(minutes=30)
        obs.fields = [f'{user_map_parameter}']
        obs.plot_units = [f'{user_map_units}']
        
        # Panel for plot with Map features
        panel = declarative.MapPanel()
        panel.layout = (1, 1, 1)
        panel.projection = 'lcc'
        panel.area = f'{user_map_region}'
        panel.layers = ['states']
        panel.title = f'{user_map_title} on {date:%Y%m%d} at {date:%H}UTC'
        panel.plots = [obs]
        
        # Bringing it all together
        pc = declarative.PanelContainer()
        pc.size = (10, 10)
        pc.panels = [panel]
    
        # Saves the map, but make sure the f string is sending them to the right location.
        
        # Note that this saves the file to your maps directory. 
        #To save images to the same location you are in, remove "maps/" from the string.
        
        pc.show()
        pc.save(f'maps/{obslvl}_{user_map_region}_{user_map_parameter}_{date:%Y%m%d}_{date:%H}z.png', dpi=150, bbox_inches='tight')

if sfc_tf == False:

# Set a format specifier for the geoptential height
# This formatter takes a value 9300 -> 930
# Good for 500-hPa and 300-hPa Observations
    if obslvl == 500 or obslvl == 300:
        height_format = lambda v: format(v, '.0f')[:-1]
    elif obslvl == 700 or obslvl == 850:

# Set a format specifier for the geoptential height
# This formatter takes a value 1576 -> 576
# Good for 700-hPa, 850-hPa, and 925-hPa Observations
        height_format = lambda v: format(v, '.0f')[1:]
# Formats 250mb correctly
    elif obslvl == 250:
        height_format = lambda v: format(v, '03.0f')[1:-1]

    # Request data using Siphon request for data from Iowa State Archive
    df = IAStateUpperAir.request_all_data(date)

    # Add lat/long data and drop stations for which we don't have lat/lons
    df = add_station_lat_lon(df, 'station').dropna(subset=['latitude', 'longitude'])

    # Eliminate the station KVER
    df = df[df.station != 'KVER']

    # Calculate Dewpoint Depression
    df['dewpoint_depression'] = df['temperature'] - df['dewpoint']
    
   # Plot desired data
    obs = declarative.PlotObs()
    obs.data = df
    obs.time = date
    obs.level = obslvl * units.hPa
    obs.fields = ['temperature', 'dewpoint_depression', 'height']
    obs.locations = ['NW', 'SW', 'NE']
    obs.formats = [None, None, height_format]
    obs.vector_field = ['u_wind', 'v_wind']
    
    # Panel for plot with Map features
    panel = declarative.MapPanel()
    panel.layout = (1, 1, 1)
    panel.projection = 'lcc'
    panel.area = [-124, -72, 24, 50]
    panel.layers = ['states', 'coastline']
    panel.left_title = f'{obslvl}mb Observations'
    panel.right_title = f'Valid: {date:%Y-%m-%d %H00} UTC'
    panel.plots = [obs]
    
    # Bringing it all together
    pc = declarative.PanelContainer()
    pc.size = (15, 12)
    pc.panels = [panel]

    # Note that this saves the file to your maps directory. 
    #To save images to the same location you are in, remove "maps/" from the string.
    
    pc.save(f'maps/{obslvl}mb_observations_{date:%Y%m%d}_{date:%H}z.png', dpi=150, bbox_inches='tight')
    pc.show()

print('Enjoy your map!')


# For testing
#date = datetime(year,month,day,hour,minute)
#print(date)
