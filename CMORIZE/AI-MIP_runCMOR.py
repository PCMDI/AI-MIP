import cmor
import xcdat as xc
import xarray as xr
import cftime
import numpy as np
import sys, os, glob
from datetime import datetime

# USING CMOR @NERSC PERLMUTTER

# PJG  01142025 First test
# REQUIRES ENV WITH CMOR, XARRAY AND XCDAT
infile = '/pscratch/sd/d/duan0000/ACE/output_ERA5_1/interpolated_init_1_T_.nc'
inputVarName = '__xarray_dataarray_variable__'
inputJson = 'AI-MIP_input.json'
cmorTable = 'Tables/obs4MIPs_Aday.json'
outputVarName = 'ta'
outputUnits = 'K'

start_time = datetime.now()
#fc = xc.open_mfdataset(infile,decode_times=True,use_cftime=True, preprocess=extract_date)
fc = xc.open_dataset(infile,decode_times=True,use_cftime=True)  #, preprocess=extract_date)

f = fc.isel(time=slice(0,10))
d = f[inputVarName]
f['ta'] = f['__xarray_dataarray_variable__']
f = f.drop_vars(['__xarray_dataarray_variable__'])

lat = f.lat.values  
lon = f.lon.values
lev = f.pressure.values
time = f.time.values 
tunits = "days since 1900-01-01"

f = f.bounds.add_bounds("X") 
f = f.bounds.add_bounds("Y")
f = f.bounds.add_bounds("Z")
f = f.bounds.add_bounds("T")

##### CMOR setup
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= 'cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# SET CMIP MODEL SPECIFIC ATTRIBUTES 
#cmor.set_cur_dataset_attribute("source_id","LOCA2--" + mod)
#cmor.set_cur_dataset_attribute("driving_source_id",mod)
#cmor.set_cur_dataset_attribute("driving_variant_label",ri)
#cmor.set_cur_dataset_attribute("driving_experiment_id",exp)

#w = sys.stdin.readline()

# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorLev = cmor.axis("plev4", coord_vals=lev[:]*10., cell_bounds=f.pressure_bnds.values*10., units="Pa")
cmorTime = cmor.axis("time", coord_vals=cftime.date2num(time,tunits), cell_bounds=cftime.date2num(f.time_bnds.values,tunits), units= tunits)
cmoraxes = [cmorLev,cmorTime, cmorLat, cmorLon]  #plev4,time,latitude,longitude'

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
values  = np.array(d[:],np.float32)

cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)

cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,len(time)) ; # Write variable with time axis
cmor.close()
f.close()
fc.close()
end_time = datetime.now()
#print('done cmorizing ',mod,exp, ri, yr[0],'-',yr[1],' process time: {}'.format(end_time-start_time))
                                                          
