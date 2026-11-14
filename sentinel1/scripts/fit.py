"""Fit Sentinel-1 HyP3 Burst InSAR products for Ocnele Mari.

Run with Python, GDAL, NumPy, pyproj and matplotlib installed:
    python fit.py ZIP_DIRECTORY OUTPUT_DIRECTORY
"""
from pathlib import Path
import re
import sys
import json
import zipfile
import numpy as np
from osgeo import gdal
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

gdal.UseExceptions()
root, out = map(Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
project = Transformer.from_crs(4326,32635,always_xy=True)
cx,cy=project.transform(24.290,45.088)
bounds=(cx-8200,cy-8200,cx+8200,cy+8200)
step=40
X,Y=np.meshgrid(bounds[0]+step*(.5+np.arange(410)),bounds[3]-step*(.5+np.arange(410)))
zones=[(45.0892,24.2872,300),(45.0882,24.2892,250),(45.0930,24.2565,300),(45.0826,24.2628,250)]
distance=[np.hypot(X-x,Y-y)-r for lat,lon,r in zones for x,y in [project.transform(lon,lat)]]
masks=[d<=0 for d in distance]
offset=np.min(distance,axis=0)
refs=[(offset>=3000)&(offset<=6500),
      (offset>=3000)&(offset<=6500)&(X<cx),
      (offset>=3000)&(offset<=6500)&(X>=cx)]
control=(offset>=6500)&(offset<=8000)
FACTOR=-1000*0.05546576/(4*np.pi)  # LOS positive toward sensor; HyP3 phase positive away.
suffixes={'phase':'unw_phase','coh':'corr','comp':'conncomp','water':'water_mask','dem':'dem','theta':'lv_theta','phi':'lv_phi'}

def read_product(p):
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
    result={}
    for key,suffix in suffixes.items():
        name=next(n for n in names if n.endswith('_'+suffix+'.tif'))
        src=gdal.Open(f'/vsizip/{p.resolve()}/{name}')
        raster=gdal.Warp('',src,format='MEM',dstSRS='EPSG:32635',outputBounds=bounds,
                         xRes=40,yRes=40,resampleAlg='near',outputType=gdal.GDT_Float32,dstNodata=np.nan)
        result[key]=raster.ReadAsArray()
    return result

def solve(A, edges, data, weights):
    """Solve only pixels whose retained pair graph connects every date."""
    n=A.shape[1]+1
    flat=weights.reshape(len(edges),-1)
    known=np.zeros((n,flat.shape[1]),bool)
    known[0]=True
    for _ in range(n):
        old=known.sum()
        for k,(i,j) in enumerate(edges):
            valid=flat[k]>0
            known[i] |= known[j]&valid
            known[j] |= known[i]&valid
        if known.sum()==old:
            break
    complete=np.flatnonzero(known.all(axis=0))
    estimated=np.full((n,flat.shape[1]),np.nan,np.float32)
    for ids in np.array_split(complete,max(1,(len(complete)+3999)//4000)):
        if not len(ids): continue
        w=flat[:,ids].astype(float)
        y=np.nan_to_num(data.reshape(len(edges),-1)[:,ids])
        normal=np.einsum('pi,pn,pj->nij',A,w,A,optimize=True)
        rhs=np.einsum('pi,pn->ni',A,w*y,optimize=True)
        estimated[0,ids]=0
        estimated[1:,ids]=np.linalg.solve(normal,rhs[...,None])[...,0].T
    return estimated.reshape((n,)+X.shape)

def slopes(t,y):
    return np.tensordot((t-t.mean())/np.sum((t-t.mean())**2),y,axes=1)

def stats(t,y):
    fit=float(slopes(t,y))
    dy=y[None,:]-y[:,None]
    i,j=np.triu_indices(len(t),1)
    sen=float(np.median(dy[i,j]/(t[j]-t[i])))
    leave=[float(slopes(np.delete(t,k),np.delete(y,k))) for k in range(len(t))]
    return {'linear_mm_yr':fit,'theil_sen_mm_yr':sen,'window_fit_mm':fit*float(t[-1]-t[0]),
            'date_fit_omission_range_mm_yr':[min(leave),max(leave)],'displacement_mm':y.tolist()}

def fit_track(track):
    files=sorted(root.glob(f'*-{track}-*.zip'))
    assert len(files)==29 and all(zipfile.is_zipfile(f) for f in files)
    pairs=[re.findall(r'20\d{6}',f.stem) for f in files]
    dates=sorted(set(sum(pairs,[])))
    assert len(dates)==16
    ix={d:i for i,d in enumerate(dates)}
    edges=[(ix[a],ix[b]) for a,b in pairs]
    A=np.zeros((len(edges),len(dates)))
    for k,(i,j) in enumerate(edges): A[k,[i,j]]=[-1,1]
    A=A[:,1:]
    rows=[read_product(f) for f in files]
    dem=rows[0]['dem']
    t=(np.array([f'{d[:4]}-{d[4:6]}-{d[6:]}' for d in dates],dtype='datetime64[D]')-
       np.datetime64(f'{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}')).astype(float)/365.25
    results={}
    for label,min_coh,ref_idx,tropo in [('baseline',.35,0,False),('strict_coherence',.55,0,False),
                                         ('west_reference',.35,1,False),('east_reference',.35,2,False),
                                         ('elevation_correction',.35,0,True)]:
        ds=[]; ws=[]
        for p in rows:
            valid=(p['coh']>=min_coh)&(p['comp']>0)&(p['water']==1)&np.isfinite(p['phase'])
            reference=refs[ref_idx]&valid
            labels,counts=np.unique(p['comp'][reference],return_counts=True)
            assert len(labels), (track,label)
            valid &= p['comp']==labels[np.argmax(counts)]
            reference=refs[ref_idx]&valid
            d=p['phase']*FACTOR
            if tropo:
                ref=reference&np.isfinite(dem)
                b=np.polyfit(dem[ref],d[ref],1)[0]
                d=d-b*(dem-np.median(dem[ref]))
            d=d-np.median(d[reference])
            ds.append(np.where(valid,d,np.nan))
            ws.append(np.where(valid,p['coh']**2,0))
        data=np.stack(ds);weights=np.stack(ws)
        y=solve(A,edges,data,weights)
        good=np.isfinite(y).all(axis=0)
        zone_results={}
        for name, mask in zip(['zone_1','zone_2','zone_3','zone_4','outer_control'],masks+[control]):
            keep=mask&good
            if keep.sum():
                zone_results[name]={'pixels':int(keep.sum()),**stats(t,np.median(y[:,keep],axis=1))}
        results[label]=zone_results
        if label=='baseline':
            fit=slopes(t,y)
            errors=[]
            index={edge:i for i,edge in enumerate(edges)}
            for (i,k), ik in index.items():
                for j in range(i+1,k):
                    if (i,j) in index and (j,k) in index:
                        closure=data[index[i,j]]+data[index[j,k]]-data[ik]
                        errors.append(closure)
            c=np.asarray(errors)
            print(track,'closure',len(c),np.nanmedian(abs(c)),np.nanpercentile(abs(c),95), 'pixels',good.sum(),flush=True)
            theta=rows[0]['theta'];phi=rows[0]['phi']
            np.savez_compressed(out/(track+'.npz'),dates=np.array(dates),displacement_mm=y,rate_mm_yr=fit,
                                e=np.cos(theta)*np.cos(phi),u=np.sin(theta),bounds_utm=np.array(bounds))
            fig,ax=plt.subplots(figsize=(7,5),layout='constrained')
            im=ax.imshow(fit,extent=(bounds[0],bounds[2],bounds[1],bounds[3]),vmin=-35,vmax=35,cmap='RdBu')
            for lat,lon,r in zones:
                ax.add_patch(plt.Circle(project.transform(lon,lat),r,fill=False,color='#ecd638',lw=1.1))
            ax.set(xlim=(cx-4500,cx+3800),ylim=(cy-3500,cy+3500),title=f'Sentinel-1 {track} · LOS rate',xlabel='UTM easting (m)',ylabel='UTM northing (m)')
            fig.colorbar(im,ax=ax,label='mm/yr · positive toward satellite')
            fig.savefig(out/(track+'.png'),dpi=140)
            plt.close(fig)
            results['quality']={'closure_triangles':len(c),'closure_abs_median_mm':float(np.nanmedian(abs(c))),
                                'closure_abs_p95_mm':float(np.nanpercentile(abs(c),95))}
        print(track,label,{k:(v['pixels'],round(v['linear_mm_yr'],2)) for k,v in zone_results.items()},flush=True)
    return {'dates':dates,'pair_count':len(files),'fits':results}

summary={track:fit_track(track) for track in ['029A','007D']}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
