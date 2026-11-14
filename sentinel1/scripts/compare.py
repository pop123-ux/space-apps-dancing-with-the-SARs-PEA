"""Summarize matched-pixel Sentinel-1 displacements for the common date window."""
import json
from pathlib import Path
import sys
import numpy as np
from pyproj import Transformer

root = Path(sys.argv[1])
a,d = [np.load(root/(tr+'.npz')) for tr in ('029A','007D')]
project = Transformer.from_crs(4326,32635,always_xy=True)
zones = [(45.0892,24.2872,300),(45.0882,24.2892,250),
         (45.0930,24.2565,300),(45.0826,24.2628,250)]
xmin,ymin,xmax,ymax = a['bounds_utm']
X,Y = np.meshgrid(np.arange(xmin+20,xmax,40),np.arange(ymax-20,ymin,-40))
epoch = np.datetime64('2026-07-07')
days = np.arange(90)
def reconstruct(stack):
    dates = stack['dates']
    t = np.array([s[:4]+'-'+s[4:6]+'-'+s[6:] for s in dates],dtype='datetime64[D]')
    t = (t-epoch).astype(int)
    y = stack['displacement_mm']
    good = np.isfinite(y).all(axis=0)
    slope = np.full(good.shape,np.nan)
    ix = np.searchsorted(t,days,side='right').clip(1,len(t)-1)
    frac = (days-t[ix-1])/(t[ix]-t[ix-1])
    interpolated = y[ix-1][:,good]*(1-frac[:,None])+y[ix][:,good]*frac[:,None]
    centered = days-days.mean()
    slope[good] = (centered @ interpolated)/(centered @ centered)*365.25
    return slope
av,dv = map(reconstruct,(a,d))
ea,ua,ed,ud = (z[k] for z,k in ((a,'e'),(a,'u'),(d,'e'),(d,'u')))
det = ea*ud-ed*ua
with np.errstate(invalid='ignore',divide='ignore'):
    up = (ea*dv-ed*av)/det
    east = (ud*av-ua*dv)/det
valid = np.isfinite(up)&np.isfinite(east)&(np.abs(det)>.2)
dist = [np.hypot(X-x,Y-y)-r for lat,lon,r in zones for x,y in [project.transform(lon,lat)]]
offset = np.minimum.reduce(dist)
regions = {f'zone_{i}': m<=0 for i,m in enumerate(dist,1)}
regions['outer_control'] = (offset>=6500)&(offset<=8000)
summary={}
for name,m in regions.items():
    k=m&valid
    summary[name]={'matched_pixels':int(k.sum())}
    if k.any():
        summary[name].update({key:float(np.median(val[k])) for key,val in
                              [('asc_mm_yr',av),('desc_mm_yr',dv),('up_mm_yr',up),('east_mm_yr',east)]})
print(json.dumps(summary,indent=2))
(root/'matched_geometry_exploratory.json').write_text(json.dumps(summary,indent=2)+'\n')
