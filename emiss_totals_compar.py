# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import matplotlib as mpl    #I probably don't need half of these packages, so I can optimise later
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
import cartopy.io.shapereader as shpreader
from cartopy.io.shapereader import Reader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.feature import (OCEAN, LAKES, BORDERS, COASTLINE, RIVERS, COLORS,
                             LAND)
from wrf import (to_np, getvar, smooth2d, get_cartopy, cartopy_xlim,
                 cartopy_ylim, latlon_coords)
from wrf import (getvar, to_np, vertcross, smooth2d, CoordPair, GeoBounds,
                 get_cartopy, latlon_coords, cartopy_xlim, cartopy_ylim)
from wrf import getvar, interplevel, to_np, get_basemap, latlon_coords
import pandas as pd
import xesmf as xe

cmip6_EU = xr.open_dataset(r'/nobackup/eecjc/cmip6_processed/cmip6_PM2_5_processed2014.nc')
EDGAR_EU = xr.open_dataset(r'/nobackup/WRFChem/emissions/EDGAR-HTAP2_MEIC2015/MOZART/EDGARHTAP2_MEIC2015_PM2.5_2010.0.1x0.1.nc')


EDGAR_EU = EDGAR_EU.assign_coords(lon=(((EDGAR_EU.lon + 180) % 360)- 180)).sortby('lon')


statesetc = shpreader.natural_earth(resolution='10m',# downloads country borders from Natural Earth
                                      category='cultural',
                                      name='admin_0_countries') #
shape_feature_another = ShapelyFeature(Reader(statesetc).geometries(),
                                ccrs.PlateCarree(), edgecolor='black', facecolor = 'none') #setting the facecolor as none is important, otherwise you can't see what is being plotted 

cmip_weights = np.cos(np.deg2rad(cmip6_EU.lat))
EDGAR_weights = np.cos(np.deg2rad(EDGAR_EU.lat))
#define latitude and longitude boundariess
#lat_bnds, lon_bnds = [32, 88], [-30.25, 48]
#lat_bnds, lon_bnds = [-90, 90], [-179, 179]

cmip6_EU= cmip6_EU.where(cmip6_EU<0,0)#get rid f negative, will probably need to add to datset generation
#get rid of superfluous varibales that make analysis tricky
cmip6_EU = cmip6_EU.drop_vars('date')
cmip6_EU = cmip6_EU.drop_vars('datesec')

EDGAR_EU['time'] = cmip6_EU['time'] #both have 12 times, but different years. This is just for consistency
#%%

#regrid the cmip6 data to EDGAR grid


regridder = xe.Regridder(cmip6_EU, EDGAR_EU, "bilinear")
CMIP_out = regridder(cmip6_EU)
print("BOZO",CMIP_out)
#%%

#subset if desired and weight data


#cmip6_EU = cmip6_EU.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
#print(cmip6_EU)
CMIP_out = CMIP_out.weighted(cmip_weights)
                             
#EDGAR_EU = EDGAR_EU.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
EDGAR_EU = EDGAR_EU.weighted(EDGAR_weights)
#EDGAR_EU_sum = EDGAR_EU.sum(dim=('lat','lon'))
                             
#print(EDGAR_EU)                     
#print(cmip6_EU) 
#%%
#get the latitude weighted totals and convert to tons for both datasets
cmip6_EU_tot = CMIP_out.sum_of_weights(dim='time') #get total number of kg per second
#print(cmip6_EU_tot)
cmip6_EU_tot = cmip6_EU_tot*31536000 #multiply by seconds in a year
#print(cmip6_EU_tot)
cmip6_EU_tot = cmip6_EU_tot*30000 #multiply by number of m2 in each grid cell
#print(cmip6_EU_tot)
cmip6_EU_tot = cmip6_EU_tot/1000 #convert to tons
#to_plot = EDGAR_EU_sum['emis_tot']
the_CMIP = cmip6_EU_tot['emis_tot']


EDGAR_EU_tot = EDGAR_EU.sum_of_weights(dim='time') #get total number of kg per second
#print(EDGAR_EU_tot)
EDGAR_EU_tot = EDGAR_EU_tot*31536000 #multiply by seconds in a year
#print(EDGAR_EU_tot)
EDGAR_EU_tot = EDGAR_EU_tot*30000 #multiply by number of m2 in each grid cell
#print(EDGAR_EU_tot)
EDGAR_EU_tot = EDGAR_EU_tot/1000 #convert to tons
print(EDGAR_EU_tot)
#to_plot = np.log10(EDGAR_EU_tot['emis_tot'])
the_EDGAR = EDGAR_EU_tot['emis_tot']



#%%

#get totals
C_lat_sum = the_CMIP.sum(dim=('lat'))
C_lon_sum = C_lat_sum.sum(dim='lon')
print("total CMIP6 PM2.5 emissions in tons is", C_lon_sum)

E_lat_sum = the_EDGAR.sum(dim=('lat'))
E_lon_sum =E_lat_sum.sum(dim='lon')
print("total EDGAR PM2.5 emissions in tons is", E_lon_sum)



#plotting a percentage difference map
to_plot = (the_CMIP-the_EDGAR/the_EDGAR)*100


levs = np.arange(-100,100, 20)

fig = plt.figure (figsize = (18, 12))
ax =plt.axes(projection = ccrs.LambertConformal(central_longitude =8)) 
ax.coastlines()
colourscheme = mpl.cm.get_cmap("seismic", 10)
#ax.set_extent([-10.25,27.9,32,69]) #Doesn't seem to show the UK with much definition

ax.add_feature(shape_feature_another) 
to_plot.plot.pcolormesh(levels=levs,cmap=colourscheme,transform=ccrs.PlateCarree())
plt.title(r'Percentage change in total PM2.5 emissions (tons) CMIP6 to EDGAR-HTAP')
plt.show()
plt.savefig('percentage_diff_emis.png')
#cb = plt.colorbar(fig)
