import xarray as xr
import numpy as np

import sys


from dask.diagnostics import ProgressBar

dsa = xr.open_mfdataset('bathymetry_u-ai424.ncS35TT')
#dsb = xr.open_mfdataset('EMODNET_2020_amm15.bathydepth.co7.cs3x.cs20.nc')
#dsb = xr.open_mfdataset('EMODNET_2020_expand_amm15.bathydepth.co7.cs3x.cs20.nc')
#dsb = xr.open_mfdataset('EMODNET_2020_expand_amm15.bathydepth.co7.cs3x.cs20.nc')
dsb = xr.open_mfdataset('EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc')


dsc=dsb.copy()

#dsc.Bathymetry.values[np.where(dsc.Bathymetry.values>400)] = 0.0
dsc.Bathymetry.values[:] = np.zeros(np.shape(dsc.Bathymetry.values[:]))

A=+np.ones(np.shape(dsc.Bathymetry.values[:]))* dsc.Bathymetry.values[:]
#A=np.ones(np.shape(dsc.Bathymetry.values[:]))* dsc.Bathymetry.values[:]
#A[np.where(A[:]<100)] = 100
A[np.where(np.isnan(A[:]))] = -1000.
print(dsa.time_counter.data)

ds = xr.Dataset(
    data_vars=dict(
        Bathymetry=(["time_counter","y", "x"], A[np.newaxis,:,:] )),
    coords=dict(
        nav_lon=(["y", "x"], dsb.lon.data),
        nav_lat=(["y", "x"], dsb.lat.data),
        time_counter=dsa.time_counter.data
#        reference_time=reference_time,
    ),
    #attrs=dict(description="Bathymetry Data"),
    attrs=dsa.attrs
)

ds.nav_lat.attrs = dsa.nav_lat.attrs
ds.nav_lon.attrs = dsa.nav_lon.attrs
ds.Bathymetry.attrs = dict(_FillValue=-1000.)

#ds.Bathymetry.attrs = dsa.Bathymetry.attrs
#ds.Bathymetry.attrs["iweight"] = 1 




print (dsa)
print ("---------")
print (ds)
print ("---------")
print (dsb)

# = dsb.lat.data
#dsc.nav_lon.data = dsb.lat.data
#print(dsa)
#print(dsb)
#print(dsc)
with ProgressBar():
  dsa.to_netcdf("TESTA.nc")
  dsb.to_netcdf("TESTB.nc")
  ds.to_netcdf("TESTT.nc")


print('All Done')




