#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 13:38:14 2022

@author: eecjc
"""


import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
import cartopy.io.shapereader as shpreader
from cartopy.io.shapereader import Reader
import os
import xesmf as xe
import PIL #only needed for gifs, comment out if not using

#update the following things based on your preferences and what you want to plot
filepath = r'/nobackup/eecjc/ClWRFotron/ClWRFChem4.2_test/output/base/'
filename =r'wrfout_d01_global_0.25deg_'
simdate='2015-10_'
varname = 'GLW'
choose_mode ='time_series' #select gif_maps, mean_map or time_series
data = xr.open_dataset (filepath + filename + simdate +varname +'.nc') 
time_points = np.arange(0,167) #number of different times you have data for in the wrfout file ONLY RELEVANT 4 GIFMAPS
time_period = '01/10/2015-08/10/2015'
log = 'false' #choose true or false
regridding = 'false' #do you want to regrid? true/false
cmap = 'seismic' #will need to change if doing percentage difference. I like seismic for that
central_lon = 8
ax_lims = [-10.25,19,35,60]
is_comparison = 'true' # if yu want a 2nd timeseries line or diff map
compare_percentage = 'false' #use true if you want the percentage difference
comparison_file_path = r'/nobackup/eecjc/insane_GHG_WRFotron/ClWRFChem4.2_test/output/base/'
if is_comparison == 'true':
    data2 = xr.open_dataset(comparison_file_path + filename + simdate +varname +'.nc')
    scenarios_compared = 'ordinary_GHG_vs_999.999_ppm (red)' #add string with brief description of what you are comparing use _ not space

set_colourbar_lim = 'false'#choose what scale you want on the colourbar. Can't really find a better way of doing this
if set_colourbar_lim == 'true':
    limits = np.arange(-2,2, 0.2)
    

#Makes a directory and sets it as default for plt.savefig
output_dir = filepath +varname +'_images/' 
if not os.path.exists(output_dir):
    os. makedirs(output_dir)
plt.rcParams["savefig.directory"] = os.chdir(os.path.dirname(output_dir))

level = 0


#next bit loads stuff for plotting, likely no need to change
var = data[varname]

stuff_with_lev = ['co', 'ch4', 'nh3']
print(var)

if varname in stuff_with_lev:
    var = var.isel(bottom_top=level)
varmean= var.mean(dim='time')
var_line = var.mean(dim = ('lat', 'lon'))




if log == 'true':
    var = np.log10(var)
    varmean = var.mean(dim ='time')
    var_line = var.mean(dim = ('lat', 'lon'))

if is_comparison == 'true': #this assumes you are comparing so you can plot the difference between wrfout files
    var2 = data2[varname]
    var2mean = var2.mean(dim='time')
    var2_line = var2.mean(dim = ('lat', 'lon'))
    if log == 'true':
        var2 = np.log10(var2)
        var2mean = var2.mean(dim='time')
        var2_line = var2.mean(dim = ('lat', 'lon'))
    if compare_percentage == 'true':
        var =(( var - var2)/var) *100 #will need to check if correct
        varmean=((varmean - var2mean)/varmean *100)
    if compare_percentage == 'false':
        var = var- var2
        varmean = varmean-var2mean
if log == 'true':
    var = np.log10(var)


    global_grid = xr.Dataset(
        {'lat': (['lat'], np.arange(-60, 85, 0.25)), 
         'lon': (['lon'], np.arange(-180, 180, 0.25)),}
        )

#collect appropriate units. Add as required

ppm = ['o3', 'co', 'ch4', 'nh3', 'no2', 'n2o', 'no3', 'no']
ug_m3 = ['PM2_5_DRY', 'PM10']
Kelvin = ['T2', 'SST', 'T', 'T00', 'TH2', 'td', 'td_2m', 'tk']
Wm2 = ['GLW', 'GSW', 'LWDNB', 'LWDNBC','LWDNT', 'LWDNTC','LWUPB', 'LWUPBC',
       'LWUPB', 'LWUPBC', 'LWUPT', 'LWUPBC', 'OlR'] #cba adding shortwave ones
ms1 = ['U', 'U10', 'V', 'V10', 'W'] 
if varname in ppm:
    units ='ppm'

if varname in ug_m3:
    units = ' ug/m3' 
    
if varname in Kelvin:
    units = ' K'
    
if varname in Wm2:
    units = ' Wm-2'

if varname in ms1:
    units = ' ms-1'
#thought about adding set scales for plots in this bit, but specifying easier

#define some functions
def regrid(dataset):
    global global_grid
    global_grid = xr.Dataset(
        {'lat': (['lat'], np.arange(-60, 85, 0.25)), 
         'lon': (['lon'], np.arange(-180, 180, 0.25)),}
        )
    regridder = xe.Regridder(
        dataset, 
        global_grid, 
        'bilinear', 
        periodic=True # needed for global grids, otherwise miss the meridian line
        )
    #global dataset
    dataset = regridder(dataset)# for multiple files to the same grid, add: reuse_weights=True

def get_maps():
    global statesetc
    statesetc = shpreader.natural_earth(resolution='10m',# downloads country borders from Natural Earth
                                        category='cultural',
                                        name='admin_0_countries')
    global shape_feature_another
    shape_feature_another = ShapelyFeature(Reader(statesetc).geometries(),
                                ccrs.PlateCarree(), edgecolor='black', 
                                facecolor = 'none')
    
def time_series(dataset):
    global fig
    fig=plt.figure(figsize=(18,18))
    dataset.plot()
    plt.grid(axis='y')
    

def make_map(dataset):
  global fig
  fig = plt.figure (figsize = (18, 12))
  global ax
  ax =plt.axes(projection = ccrs.LambertConformal(central_longitude=central_lon)) 
  ax.coastlines()
  ax.set_extent(ax_lims) #Doesn't seem to show the UK with much definition
  ax.add_feature(shape_feature_another)
  if set_colourbar_lim == 'true':
        fig = dataset.plot.pcolormesh(add_colorbar= False,cmap=cmap,
                                                    levels = limits,transform=ccrs.PlateCarree())
  else:
        fig = dataset.plot.pcolormesh(add_colorbar= False,cmap=cmap,transform=ccrs.PlateCarree())
  plt.title (varname + units + ' mean ' + time_period, size ='x-large', weight='bold')
  global cb
  cb = plt.colorbar(fig)

#different plotting forms

if choose_mode == 'time_series':
    time_series(var_line)
    if is_comparison == 'true':
        var2_line.plot(color='red')
        plt.ylabel('Mean ' + varname + ' '+ units, size='x-large', weight='bold')
        plt.title('Mean ' + varname + ' ' + scenarios_compared, size='x-large', weight='bold')
        plt.savefig(output_dir +varname+ scenarios_compared + choose_mode +'.jpg')
    if is_comparison == 'false':
        plt.title('Mean ' + varname + ' ' + time_period, size='x-large', weight='bold')
        plt.savefig(output_dir +'varname'+ choose_mode + '.jpg')
    plt.show() 
        

if choose_mode == 'mean_map':
    get_maps()
    make_map(varmean)
    cb.set_label(label = varname + ' ' + units, size = 'x-large', weight = 'bold')
    if is_comparison == 'false':
        plt.title('Mean ' + varname + ' ' + time_period, size='x-large', weight='bold')
    if is_comparison == 'true':
        plt.title('Mean ' + varname + ' ' + scenarios_compared, size='x-large', weight='bold')
    plt.savefig(output_dir +varname + '_' + choose_mode + '.jpg')
    plt.show()

if choose_mode == 'gif_maps':
    get_maps()
    if regridding == 'true':
        regrid(var)
    for i in time_points:
        time_for_titles = i+1
        make_map(var[i])
        cb.set_label(label = varname + ' ' + units, size = 'x-large', weight = 'bold')
        plt.title (varname + ' ' + units + ' at time point: ' + str(time_for_titles), size='x-large', weight='bold')#I think this is ppm. The .nc file doesn't say
        make_title = varname + '_' + str(time_for_titles) + '.jpg'
        plt.savefig(make_title) #be aware this will save an image for every time point in the wrfout file
        #plt.show() #only use if need be, makes a LOT of images
        plt.clf()
  
    #now make gif
    image_frames = []
    time_points = time_points +1 #keeps file numbers consistent
    
    for k in time_points:
        new_frame = PIL.Image.open(output_dir + varname + '_' + str(k) + '.jpg')
        image_frames.append(new_frame)
    print(image_frames)
    image_frames[0].save('GLW_ClWRF.gif', format ='GIF', #not specifying path, will be in working dir
                         append_images = image_frames[1:],
                         save_all =True, duration = 300,
                         loop=0)
        

