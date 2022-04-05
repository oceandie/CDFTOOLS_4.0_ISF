import xarray as xr
import numpy as np
import time

import sys
from dask.diagnostics import ProgressBar
infile = sys.argv[1]

print("\n %s will be cut down to AMM15 dimensions\n"%(infile))
dsa = xr.open_mfdataset(infile,combine='by_coords').squeeze()



inflate_lat=100
inflate_lon=100


# Get core part of the domain 

print(dsa)
dscut = dsa.Bathymetry[      inflate_lat : -inflate_lat , inflate_lon : -inflate_lon ]


#dsa.keys()

LIST=list(dsa.keys())
print(LIST[0])
if(LIST[0]=='lat'):
   dlatcut = dsa.lat [      inflate_lat : -inflate_lat , inflate_lon : -inflate_lon ]
   dloncut = dsa.lon [      inflate_lat : -inflate_lat , inflate_lon : -inflate_lon ]
else:
   dlatcut = dsa.nav_lat [      inflate_lat : -inflate_lat , inflate_lon : -inflate_lon ]
   dloncut = dsa.nav_lon [      inflate_lat : -inflate_lat , inflate_lon : -inflate_lon ]




print('Storing Pure Cut Domain')

with ProgressBar():
  dscut.to_netcdf("CUTAMM15_%s"%(infile))

print(' Copying perimeter values from 4 in out to edge')

dscut.load()
for i in range(4):
    dscut[   i  ,   :  ] = dscut[   4  , :  ]
    dscut[   i  ,   :  ] = dscut[   4  , :  ]
    dscut[   :  ,   i  ] = dscut[   :  , 4  ]
    dscut[ -1-i ,   :  ] = dscut[   -5 , :  ]
    dscut[   :  , -1-i ] = dscut[   :  , -5 ]

print('Storing Cut Domain with copied outer perimieter' )

with ProgressBar():
  OUTPUT=xr.merge([dscut, dlatcut, dloncut])
  OUTPUT.attrs['description'] = 'Used Cut_and_copy_bdy_perimeter.py to cut out inner domain and apply bdy perimeter to %s'%(infile)
  OUTPUT.attrs['history'] = "Created at the Met Office, " + time.ctime(time.time())
  OUTPUT.attrs['Usage'] = "See README_AMM15_USAGE.md"
  OUTPUT.to_netcdf("BDY_COPY_CUTAMM15_%s"%(infile))

print(' All Done')
