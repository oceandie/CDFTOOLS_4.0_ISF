# Notes on using Shapiro for smoothing GEBCO/EMODNET for AMM15


We have sample Files to work with:

   * **EMODNET_2020_amm15.bathydepth.co7.cs3x.cs20.nc**
      * EMODNET December 2020 with CS3x+CS20 LAT correction on AMM15 grif with original LSM imposed
   * **EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc**
      * GEBCO 2020 Deep to 200 m, Linear Interp to EMODNET 100 m EMODNET to 10 m Linear Interpolation to GEBCO by 5 m GEBCO to 5_GEBCO_TO_COAST_amm15
      * This is done on the expanded AMM15 domain so taht the smoother wont effect the AMM15 bdy

## Reformat the data

### OLD way was to use a template file, This is no longer donwe see next section

The smoother has particular format in mind so we use the reference file:
   * bathymetry_u-ai424.ncS35TT
To set up a format before processing.

The python *xarray_format.py* processes the input file to conform.


Read in the sample file and the actual data file to be processed:
```python
dsa = xr.open_mfdataset('bathymetry_u-ai424.ncS35TT')
dsb = xr.open_mfdataset('EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc')
```
We work on a copy of the input data:
```python
dsc = dsb.copy()
dsc.Bathymetry.values[:] = np.zeros(np.shape(dsc.Bathymetry.values[:]))
```
And in fact use a numpy array based on that data so really no need to copy
```python
A = +np.ones(np.shape(dsc.Bathymetry.values[:]))* dsc.Bathymetry.values[:]
```
Due to negative bathy, we could have 0 as a real valid bathy value. I set it up arbitarily as some large negative number here 1000 m

```python
A[np.where(np.isnan(A[:]))] = -1000.
```
Then we create a brand new dataset **ds** that also has a time dimension by using numpy newaxis to add on to A. We also use the lat and lon data straight from **dsb** (input data). We set the global attributes to be exactly as in the reference data set **dsa**

```python
ds = xr.Dataset(
    data_vars=dict(
        Bathymetry=(["time_counter","y", "x"], A[np.newaxis,:,:] )),
    coords=dict(
        nav_lon=(["y", "x"], dsb.lon.data),
        nav_lat=(["y", "x"], dsb.lat.data),
        time_counter=dsa.time_counter.data
    ),
    attrs=dsa.attrs
)
```
Likewise we set the attributes of lat and lon as in the reference dataset
```python
ds.nav_lat.attrs = dsa.nav_lat.attrs
ds.nav_lon.attrs = dsa.nav_lon.attrs
```
Finally we set the FillValue for the Bathymetry as -100_EMODNET_TO_10
```python
ds.Bathymetry.attrs = dict(_FillValue=-1000.)
```

Then just write out the data to disk ready for processing by the smoother.
```python
with ProgressBar():
  ds.to_netcdf("TESTT.nc")
```

### New way is to just set the attributes directly in python/xarray, no need of template

```bash
xarray_format_notemplate.py
```

First get the input dataset

```python
dsb = xr.open_mfdataset('EXPANDED_MERGE_GEBCO_DEEP_TO_200-100_EMODNET_TO_10-5_GEBCO_TO_COAST_amm15.bathydepth.co7.cs3x.cs20.nc')
```

work on a copy of the date
```python
dsc=dsb.copy()
dsc.Bathymetry.values[:] = np.zeros(np.shape(dsc.Bathymetry.values[:]))

A=+np.ones(np.shape(dsc.Bathymetry.values[:]))* dsc.Bathymetry.values[:]
```

Due to negative bathy, we could have 0 as a real valid bathy value. I set it up arbitarily as some large negative number here 1000 m
```python
A[np.where(np.isnan(A[:]))] = -1000.
```

Set up new data set ds, based on Bathymetry and dsb lat lon and add in time counter

```python
ds = xr.Dataset(
    data_vars=dict(
        Bathymetry = (["time_counter","y", "x"], A[np.newaxis,:,:] )),
    coords=dict(
        nav_lon = (["y", "x"], dsb.lon.data),
        nav_lat = (["y", "x"], dsb.lat.data),
        time_counter = (["time_counter"], np.ones(1)),
    ),
)
```

Now set up the attributes for each case

```python
ds.nav_lat.attrs['standard_name'] = "latitude"
ds.nav_lat.attrs['longname'] = "Latitude"
ds.nav_lat.attrs['units'] = "degrees_north"
ds.nav_lon.attrs['standard_name'] = "longitude"
ds.nav_lon.attrs['longname'] = "Longitude"
ds.nav_lon.attrs['units'] = "degrees_east"
ds.Bathymetry.attrs = dict(_FillValue=-1000.)
```

The write it out



## Do the Smoothing.

The actual Smoother can be run by commands  such as:
```bash
./bin/cdfsmooth -f TESTT.nc -c 2 -t S -npass 8 -lap T -lsm TT -nc4
```
   * Here the order of the smoother used is the number after the flag **-c**
   * The number of passes performed is given after the **-npass** flag

It is important to note that a namelist can be used to set the parameters of the smoother. This has actually been hard coded to be in the Notes folder:
   * Notes/namelist_shapiro.txt
In our case we have:

```namelist
&nam_shapiro
l_pass_shallow_updates = .TRUE.
l_pass_fixed_pt_updates = .FALSE.
/
```

Also several variables are set in the code directly to defaults that could be set in the namelist that the user ought to be aware of.
```fortran

    NAMELIST / nam_shapiro / ll_npol_fold, ll_cycl, l_single_point_response, l_pass_shallow_updates, l_pass_fixed_pt_updates, &
   &                         ji_single_pt, jj_single_pt, jst_prt, jend_prt

```
The Defaults are set as:
```fortran
ll_npol_fold = .FALSE.
ll_cycl = .FALSE.
l_single_point_response = .FALSE.

```

There are also a number of variables that are hardcoded into the source that are important, perhaps they should be user defined in in the namelist_shapiro
```
zmin_val        =  -5    ! minimum depth (e.g. 10.0 metres)
ztol_shallow    = 1.0    ! tolerance in metres of minimum shallow values (zmin_val - ztol_shallow)
ztol_fixed      = 1.0    ! tolerance in metres for fit to bathymetry at point specified to be fixed  
zfactor_shallow = 1.0    ! zfactor_shallow needs to be slightly greater than 1.0   ! 1.1 to 1.5 are reasonable values
```

I have changed the minimum value here to -5. Note the ztol_shallow tolerance and zfactor_shallow are important here also.

Some of the more relevant changes/comments are:
```diff
WHERE ( v2d == rspval ) iw =0
+             !CEOD OLD FIX NOT NEEDED found problem in io routine where mask set
+             !to 0 WHERE ( v2d == 0 ) iw =0
IF ( ncut /= 0 ) CALL filter( nfilter, v2d, iw, w2d)
IF ( ncut == 0 ) w2d = v2d
-              w2d  = w2d *iw  ! mask filtered data
+!CEOD DONT NEED THE BELOW?
+!CEOD              w2d  = w2d *iw  ! mask filtered data
ierr = putvar(ncout, id_varout(jvar), w2d, jk, npiglo, npjglo, ktime=jt)
!
END DO
-    ll_npol_fold = .TRUE.
-    ll_cycl = .TRUE.
+!CEOD Hardwired here
+    ll_npol_fold = .FALSE.
+    ll_cycl = .FALSE.
l_single_point_response = .FALSE.
l_pass_shallow_updates = .TRUE.
l_pass_fixed_pt_updates = .TRUE.

-    zmin_val        = 10.0   ! minimum depth (e.g. 10.0 metres)
+    !CEODzmin_val        = 10.0   ! minimum depth (e.g. 10.0 metres)
+    zmin_val        =  -5  ! minimum depth (e.g. 10.0 metres)
+    !CEODztol_shallow    = 1.0    ! tolerance in metres of minimum shallow values (zmin_val - ztol_shallow)
ztol_shallow    = 1.0    ! tolerance in metres of minimum shallow values (zmin_val - ztol_shallow)
ztol_fixed      = 1.0    ! tolerance in metres for fit to bathymetry at point specified to be fixed
-    zfactor_shallow = 1.5    ! zfactor_shallow needs to be slightly greater than 1.0   ! 1.1 to 1.5 are reasonable values
+    !CEODzfactor_shallow = 1.5    ! zfactor_shallow needs to be slightly greater than 1.0   ! 1.1 to 1.5 are reasonable values
+    zfactor_shallow = 1.0    ! zfactor_shallow needs to be slightly greater than 1.0   ! 1.1 to 1.5 are reasonable values

ji_single_pt = 622 ; jj_single_pt = 779
jst_prt = 400 ;      jend_prt = 405

-    OPEN(UNIT=20, file = '@Notes/namelist_shapiro.txt', form='formatted', status='old' )
+    OPEN(UNIT=20, file = 'Notes/namelist_shapiro.txt', form='formatted', status='old' )
READ(NML=nam_shapiro, UNIT = 20)
WRITE(NML=nam_shapiro, UNIT=6)
CLOSE(20)
@@ -638,8 +664,11 @@
END IF

! read the indices of points to remain fixed
IF ( l_pass_fixed_pt_updates ) THEN
-       OPEN (unit=20, file = '@Notes/list_fixed_points.txt', form='formatted', status='old' )
+       OPEN (unit=20, file = 'Notes/list_fixed_points.txt', form='formatted', status='old' )
READ (20, *) jn_fix_pts
```

I found that the code tries to set the mask to 0, this is actually done in cdf90.cdf90
```fortran
WHERE (getvar == spval )  getvar=0.0
```
so I removed it from this W&D case

## LSM issues and the expanded domain
  *  It looks like we have some Sea values creeping into the LSM in the expanded domain
      * Is this happening before we even filter, is a cut out of the expanded domain having these sea values?
      * If we take a cut ouf the TESTT.nc file as yet to be smoothed
      ```bash
      ncks -d x,100,-100 -d y,100,-100 TESTT.nc X.nc
      ```
      we can see sea points in Norway along the boundary:
      ![](Norway_Sea_Points_AMM15_N_BDY.png)

      This must be occuring  in the expanded domain processing perhaps we are a grid point reference out by one?
         * Actually I believe the cut out is not quite straight
         * It should be
         ```bash
         ncks -d x,100,-101 -d y,100,-101 TESTT.ncS28TT CUT.nc
         ```
         That gives the correct limits and dimensions:
         ```
         dimensions:
      	 time_counter = UNLIMITED ; // (1 currently)
      	 y = 1345 ;
	       x = 1458 ;
         ```
      *  Note in the original case we actualy copied out the perimiter points so we may want to replicate this after the smoothing is done and we have a final cut out
       ```python
       # ==== OPTIONAL: apply 5pt smoothing around bry (bdy5) ====
       # e.g. set bathy[:4,:] = bathy[4,:]  
       for i in range(4):
         emodnet_bath[i,:] = emodnet_bath[4,:]
         emodnet_bath[:,i] = emodnet_bath[:,4]
         emodnet_bath[-1-i,:] = emodnet_bath[-5,:]
         emodnet_bath[:,-1-i] = emodnet_bath[:,-5]
       ```  
       so actually the 4 outer points are copies
       * Can add a simple python script to both cut out the inner dommain and make the copy on the perimeter

### Script to cut out and copy out bdy perimeter
Create a simple python script to read in an expanded bathy file,
cut out the inner part of the domain and apply the same copy of the inner perimeter 4 points in out to the edge as in the CO7 configuration

   * Cut_and_copy_bdy_perimeter.py
   * Typical Usage:
      * ```bash
      ipython Cut_and_copy_bdy_perimeter.py TESTT.ncS28TT
      ```
It will output a new file with BDY_COPY_CUTAMM15 in front of the orginal  
