import xarray as xr
import numpy as np

import sys


from dask.diagnostics import ProgressBar

#dsb = xr.open_mfdataset('EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc')
dsb = xr.open_mfdataset('CORRECTED_EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc')


dsc=dsb.copy()

dsc.Bathymetry.values[:] = np.zeros(np.shape(dsc.Bathymetry.values[:]))

A=+np.ones(np.shape(dsc.Bathymetry.values[:]))* dsc.Bathymetry.values[:]
A[np.where(np.isnan(A[:]))] = -1000.
A[np.where(A[:]>1.e20)] = -1000.

ds = xr.Dataset(
    data_vars=dict(
        Bathymetry = (["time_counter","y", "x"], A[np.newaxis,:,:] )),
    coords=dict(
        nav_lon = (["y", "x"], dsb.lon.data),
        nav_lat = (["y", "x"], dsb.lat.data),
        time_counter = (["time_counter"], np.ones(1)),
    ),
)

ds.nav_lat.attrs['standard_name'] = "latitude"
ds.nav_lat.attrs['longname'] = "Latitude"
ds.nav_lat.attrs['units'] = "degrees_north"
ds.nav_lon.attrs['standard_name'] = "longitude"
ds.nav_lon.attrs['longname'] = "Longitude"
ds.nav_lon.attrs['units'] = "degrees_east"
ds.Bathymetry.attrs = dict(_FillValue=-1000.)
print(ds.nav_lat.attrs)



print (ds)
print ("---------")
print (dsb)

with ProgressBar():
  ds.to_netcdf("TESTT.nc")


print('All Done')




