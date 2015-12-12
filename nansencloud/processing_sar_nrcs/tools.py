#-------------------------------------------------------------------------------
# Name:		utils.py
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	27.08.2013
# Last modified:30.04.2015 10:51
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
from django.utils import timezone

import os, scipy
import numpy as np
from nansat import Figure
from nansat.nansat import Nansat

#import geographiclib.geodesic
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap


eResampleAlg = 1 # bilinear 
#eResampleAlg = 0  # nearest neighbour

def resize(n, resize_factor = 0.1):
    # resize to correct ratio range:azimuth
    try:
        wh_ratio = ( float(n.get_metadata()['LINE_SPACING']) /
            float(n.get_metadata()['PIXEL_SPACING']) )
    except Exception as e:
        print e
        wh_ratio = ( float(n.get_metadata()['SPH_AZIMUTH_SPACING']) /
            float(n.get_metadata()['SPH_RANGE_SPACING']) )

    w0 = wh_ratio*n.shape()[1]
    h0 = n.shape()[0]
    n.resize( width = w0*resize_factor, height = h0*resize_factor,
            eResampleAlg=eResampleAlg)

def flipdim(n, nparr):
    ''' Flip dimensions for descending pass images

    Note that this presently only works for Radarsat-2. Other SAR instruments
    may have different metadata keys for the orbit direction
    '''
    #if n.get_metadata()['ORBIT_DIRECTION']=='Descending':
    #    nparr=np.fliplr(nparr)
    #if n.get_metadata()['ORBIT_DIRECTION']=='Ascending':
    nparr=np.flipud(nparr)
    return nparr

def get_label(b):
    if 'sigma0_HH'==b:
        #return '$\sigma_0^{hh}$'
        return 'HH'
    if 'sigma0_VV'==b:
        #return '$\sigma_0^{vv}$'
        return 'VV'
    if 'PD'==b:
        #return '$\Delta\sigma_0$'
        return 'PD'
    if 'PR'==b:
        #return '$P_R$'
        return 'PR'
    if 'CP'==b:
        #return '$\sigma_0^{cp}$'
        return 'CP'
    if 'NP'==b:
        #return '$\sigma_{wb}$'
        return 'NP'
    return ''

def _show_transect(n,t,pixlinCoord,title='',label_prefix='', dir='.', **kwargs):
    nparr = n[kwargs['bandList'][0]]
    bandnames = kwargs.pop('bandList')
    kwargs.pop('smoothRadius')
    if kwargs.has_key('ylim'):
        ylim = kwargs.pop('ylim')
    if kwargs.has_key('semilogy'):
        semilogy = kwargs.pop('semilogy')

    copy = np.zeros(np.shape(nparr))
    copy[pixlinCoord[1].astype(int), pixlinCoord[0].astype(int)] = 1
    aa, rr = np.where(copy)

    b = bandnames[0]
    if '_reduced' in b:
        b=b.strip('_reduced')
    fn = 'transect_marked_'+b+'_'+title.replace(' ','_').lower()+'.png'
    fig = plt.figure(num=2,figsize=( int(np.round(n.shape()[1]/100.)),
        int(np.round(n.shape()[0]/100.)) ), dpi=300)
    plt.clf()
    plt.imshow(nparr, **kwargs)
    plt.axis('tight')
    plt.axis('off')
    plt.hold(True)
    plt.plot(rr, aa, 'r',
            lw=int(np.round(n.shape()[0]/1000.)), linewidth=4 )
    plt.axis('tight')
    plt.axis('off')
    fig.savefig(os.path.join(dir,fn), pad_inches=-0.5, bbox_inches='tight')
    fig.clear()
    plt.close()

    #b = bandnames[0]
    #if '_reduced' in b:
    #    b=b.strip('_reduced')
    #fn = 'transect_'+label_prefix.lower()+'_'+b+'_'+title.replace(' ','_').lower()+'.png'
    ##fig = plt.figure(num=3,figsize=(3,3), dpi=300)
    #fig = plt.figure(num=3,dpi=300,figsize=(2.5,2.5))
    #plt.clf()
    #if 'semilogy' in locals() and semilogy:
    #    plt.semilogy(t[0], label = get_label(b))
    #else:
    #    plt.plot(t[0], label = get_label(b))
    #plt.hold(True)
    #count=1
    #for transect in t[1:]:
    #    b = bandnames[count]
    #    if '_reduced' in b:
    #        b=b.strip('_reduced')
    #    if 'semilogy' in locals() and semilogy:
    #        plt.semilogy(transect, label = get_label(b))
    #    else:
    #        plt.plot(transect, label = get_label(b))
    #    count += 1
    ##if title:
    ##    plt.title(title, fontsize=10)
    #plt.axis('tight')
    #if 'ylim' in locals():
    #    plt.ylim(ylim[0],ylim[1])
    #plt.legend(fontsize=6)
    #plt.grid(axis='both',which='both')
    #if title=='Plant oil':
    #    plt.ylabel('Contrast', fontsize=10)
    #else:
    #    plt.ylabel('', fontsize=10)
    #plt.xlabel('Pixel no. along transect', fontsize=10)
    #plt.yticks(fontsize=8)
    #plt.xticks(fontsize=8)
    #fig.savefig(os.path.join(dir,fn), dpi=300, pad_inches=0.1, bbox_inches='tight')
    #fig.clear()
    #plt.close()

def contrast_transect(n, method='contrast', dir='.', title='', **kwargs):
    if kwargs.has_key('ylim'):
        ylim = kwargs.pop('ylim')
    if kwargs.has_key('semilogy'):
        semilogy = kwargs.pop('semilogy')
    if kwargs.has_key('points'):
        pp0 = kwargs.pop('points')
    else:
        print 'Mark 4 points. First and last sections are background. Middle is slick.'
        t,[lon,lat],pp0=n.get_transect(transect=False,**kwargs)
    t1,[lon1,lat1],p1 = n.get_transect(latlon=False, points=((pp0[0][0],
        pp0[1][0]),(pp0[0][1], pp0[1][1])), smoothRadius=kwargs['smoothRadius'],
        bandList=kwargs['bandList'])
    t2,[lon2,lat2],p2 = n.get_transect(latlon=False, points=((pp0[0][1],
        pp0[1][1]),(pp0[0][2], pp0[1][2])), smoothRadius=kwargs['smoothRadius'],
        bandList=kwargs['bandList'])
    t3,[lon3,lat3],p3 = n.get_transect(latlon=False, points=((pp0[0][2],
        pp0[1][2]),(pp0[0][3], pp0[1][3])), smoothRadius=kwargs['smoothRadius'],
        bandList=kwargs['bandList'])

    orig = Nansat(os.path.abspath(n.fileName).split('.')[0]+'.zip')
    inci1 = orig['incidence_angle'][p1[1],p1[0]]
    inci2 = orig['incidence_angle'][p2[1],p2[0]]
    inci3 = orig['incidence_angle'][p3[1],p3[0]]

    inci=np.array([])
    inci=np.append(inci,inci1)
    inci=np.append(inci,inci2)
    inci=np.append(inci,inci3)

    ii=np.array([])
    ii=np.append(ii,inci1)
    ii=np.append(ii,inci3)
    for i in range(len(t1)):
        bg=np.array([])
        bg=np.append(bg,t1[i])
        bg=np.append(bg,t3[i])

        A = np.array([ii,np.ones(len(ii))])
        w = np.linalg.lstsq(A.T, bg)[0] # least squares fit 
        line = w[0]*inci+w[1] # regression line

        tr=np.array([])
        tr=np.append(tr,t1[i])
        tr=np.append(tr,t2[i])
        tr=np.append(tr,t3[i])

        fig = plt.figure(num=1)
        plt.plot(inci,tr,label=n.get_metadata('name',kwargs['bandList'][i]))
        plt.hold(True)
        plt.plot(inci,line,label='Background')
        plt.legend()
        if title:
            plt.title(title)
        fig.savefig(os.path.join(dir,
            'transect_'+n.get_metadata('name', kwargs['bandList'][i])+'_'+title.replace(' ','_').lower()+'.png'),
            pad_inches=1, bbox_inches='tight')
        fig.clear()
        plt.close()

        if i==0:
            if method=='contrast':
                transects = np.array([np.divide(np.subtract(tr, line), line)])
            if method=='ratio':
                transects = np.array([np.divide(line,tr)])
        else:
            if method=='ratio':
                # sjekk for negative verdier og band vs index...
                transects = np.append(transects, 
                        [np.divide(line, tr)], axis=0)
            if method=='contrast':
                transects = np.append(transects, 
                        [np.divide(np.subtract(tr, line), line)], axis=0)

    pp = np.array([[],[]])
    pp = np.append(pp,[p1[0],p1[1]],axis=1)
    pp = np.append(pp,[p2[0],p2[1]],axis=1)
    pp = np.append(pp,[p3[0],p3[1]],axis=1)

    if 'ylim' in locals():
        kwargs['ylim']=ylim
    if 'semilogy' in locals():
        kwargs['semilogy']=semilogy

    _show_transect(n, transects, pp, dir=dir, label_prefix=method,
            title=title, **kwargs)

    lon=np.array([])
    lon=np.append(lon,lon1)
    lon=np.append(lon,lon2)
    lon=np.append(lon,lon3)
    lat=np.array([])
    lat=np.append(lat,lat1)
    lat=np.append(lat,lat2)
    lat=np.append(lat,lat3)
    
    return transects,[lon,lat],pp0

#def transect(n, dir='.', **kwargs):
#    t,[lon,lat],pixlinCoord=n.get_transect(**kwargs)
#    _show_transect(n, t, pixlinCoord, dir=dir, **kwargs)
#    return t,[lon,lat],pixlinCoord

def make_PR_image(fqp_obj, fn='sigma0_PR.png', dir='.', min=np.nan, max=np.nan,
        **kwargs):
    # reduce file size
    resize(fqp_obj)
    try:
        pr = fqp_obj['PR']
    except:
        fqp_obj.undo()
        raise
    #if fqp_obj.fileName[-2:]=='nc':
    #    pr = flipdim(fqp_obj,pr)
    if np.isnan(max):
        max=1
    if np.isnan(min):
        min=np.nanmedian(pr,axis=None)-2.0*np.nanstd(pr,axis=None)
        if min<0:
            min=0
    # Using nansat.figure module:
    caption = 'Linear units'
    nansatFigure(pr, min, max, dir, fn)
    fqp_obj.undo()
    return fn

def make_PD_image(fqp_obj,fn='sigma0_PD.png',dir='.', max=np.nan, min=np.nan,
        **kwargs):
    resize(fqp_obj)
    try:
        pd = fqp_obj['PD']
    except:
        fqp_obj.undo()
        raise
    #if fqp_obj.fileName[-2:]=='nc':
    #    pd = flipdim(fqp_obj,pd)
    #pd[np.where(pd<0)] = np.nan # over the sea sbrvv>sbrhh, thus pd>0
    if np.isnan(max):
        max = np.nanmedian(pd,axis=None)+2.0*np.nanstd(pd,axis=None)
    if np.isnan(min):
        min = np.nanmedian(pd,axis=None)-2.0*np.nanstd(pd,axis=None)
        if min<0:
            min = 0 # over the sea sbrvv>sbrhh, thus pd>0
    caption = 'Linear units'
    nansatFigure(pd, min, max, dir, fn)
    fqp_obj.undo()
    return fn

def make_NP_image(fqp_obj,fn='sigma0_NP.png',dir='.', max=np.nan, min=np.nan,
        **kwargs):
    resize(fqp_obj)
    try:
        nonpol = fqp_obj['NP']
    except:
        fqp_obj.undo()
        raise
    #if fqp_obj.fileName[-2:]=='nc':
    #    nonpol = flipdim( fqp_obj, nonpol)
    caption = 'Linear units'
    if np.isnan(max):
        max=np.nanmedian(nonpol,axis=None)+2.0*np.nanstd(nonpol,axis=None)
    if np.isnan(min):
        min=np.nanmedian(nonpol,axis=None)-2.0*np.nanstd(nonpol,axis=None)
    if min<0:
        min = 0 # cannot have negative backscatter..
    nansatFigure(nonpol, min, max, dir, fn)
    fqp_obj.undo()
    return fn

def make_NRCS_image( nobj, bandname, fn='', dir='.', max=np.nan, min=np.nan,
        **kwargs):
    if not fn:
        if 'reduced' in bandname:
            fn = bandname[:9]+'.png'
        else:
            fn = bandname+'.png'
    resize(nobj)
    try:
        s0 = 10.0*np.log10(nobj[bandname])
    except:
        n_obj.undo()
        raise
    s0[np.where(np.isinf(s0))]=np.nan
    #if nobj.fileName[-2:]=='nc':
    #    s0 = flipdim(nobj,s0)

    caption='dB'
    if np.isnan(min):
        min = np.nanmedian(s0,axis=None)-2.0*np.nanstd(s0,axis=None)
    if np.isnan(max):
        max = np.nanmedian(s0,axis=None)+2.0*np.nanstd(s0,axis=None)
    nansatFigure(s0, min, max, dir, fn)
    nobj.undo()
    return fn

def nansatFigure(nparr, mask, min, max, dir, fn):

    f = Figure(nparr)
    f.process(
        cmin = min,
        cmax = max,
        cmapName = 'gray',
        mask_array=mask,
        mask_lut={0:[255,0,0]}
    )
    f.save(os.path.join(dir,fn), transparency=[255,0,0])

#def make_wind_field_image( w, dir='.', fn='windfield.png', max=np.nan,
#        min=np.nan, res='l'):
#
#    uu = w['U']
#    vv = w['V']
#    #look_direction = float(w.get_metadata('SAR_center_look_direction'))
#    speed = w['windspeed']
#    dirGeo = w['winddirection']
#    #dirLookRelative = np.mod(np.subtract( dirGeo, look_direction ), 360)
#    #dirRange = -np.sin(dirLookRelative*np.pi/180.)
#    #dirAzim = np.cos(dirLookRelative*np.pi/180.)
#    #x=np.arange(np.shape(dirRange)[0])
#    #y=np.arange(np.shape(dirRange)[1])
#    #X, Y = np.meshgrid(y, x)
#    if np.isnan(min):
#        min = np.nanmedian(speed, axis=None) - 2*np.nanstd(speed,axis=None)
#        if min<0:
#            min = 0
#    if np.isnan(max):
#        max = np.nanmedian(speed, axis=None) + 2*np.nanstd(speed,axis=None)
#
#    lonMax = np.max(w.get_corners()[0])
#    lonMean = np.mean(w.get_corners()[0])
#    lonMin = np.min(w.get_corners()[0])
#    latMax = np.max(w.get_corners()[1])
#    latMean = np.mean(w.get_corners()[1])
#    latMin = np.min(w.get_corners()[1])
#    width = geographiclib.geodesic.Geodesic.WGS84.Inverse(latMean,
#            lonMin, latMean, lonMax)
#    height = geographiclib.geodesic.Geodesic.WGS84.Inverse(latMin,
#            lonMean, latMax, lonMean)
#
#    dpi = 300.
#    ysize = 6
#    xsize = 6
#    titleSize = 1.5*xsize #w.shape()[1]/500
#    legendSize = xsize #*2.5/3
#    tickSize = xsize*2/3 #w.shape()[1]/1000
#    fig = plt.figure(num=1, figsize=(xsize,ysize), dpi=dpi)
#    plt.clf()
#    map = Basemap(projection='laea', 
#                    width=width['s12'],
#                    height=height['s12'],
#                    lat_ts = np.mean(w.get_corners()[1]),
#                    lon_0 = np.mean(w.get_corners()[0]),
#                    lat_0 = np.mean(w.get_corners()[1]),
#                    resolution=res)
#
#    lon,lat=w.get_geolocation_grids()
#    x,y = map(lon,lat)
#    mappable = map.pcolormesh(x,y,speed,vmin=min,vmax=max,shading='flat',cmap=plt.cm.jet)
#
#    dd = int(np.round(np.shape(speed)[1]/10))
#    # Meteorological barbs
#    Q = map.barbs(x[dd::dd-1,::dd], y[dd::dd-1,::dd], uu[dd::dd-1,::dd],
#            vv[dd::dd-1,::dd])
#
#    map.fillcontinents(color='#cc9966',lake_color='#99ffff')
#
#    nLines = 3.
#    map.drawparallels(np.arange(lat.min()+(lat.max()-lat.min())/(nLines*2),lat.max(),
#        (lat.max()-lat.min())/nLines), 
#        linewidth=0.2,
#        labels=[True,False,False,False], fontsize=tickSize, fmt='%.1f')
#    map.drawmeridians(np.arange(lon.min()+(lon.max()-lon.min())/(nLines*2),lon.max(),
#        (lon.max()-lon.min())/nLines),
#        linewidth=0.2,
#        labels=[False,False,False,True], fontsize=tickSize, fmt='%.1f')
#
#    cb = fig.colorbar(mappable,orientation='horizontal', pad=0.05)
#    cb.set_label('m/s',fontsize=legendSize)
#
#    ax = plt.gca()
#    plt.axes(cb.ax)
#    plt.xticks(fontsize=tickSize)
#    plt.axes(ax)
#
#    fig.savefig( os.path.join(dir,fn), facecolor='w', edgecolor='w', dpi=300,
#            bbox_inches="tight", pad_inches=0.1)

def write_map(outputFileName, list_of_nobjs, lonBorder=[4.,4.],
        latBorder=[4.,4.],
        figureSize=(4,4), dpi=50, projection='cyl', resolution='h',
        continetsColor='coral', meridians=10, parallels=10, pColor='r',
        pLine='k', pAlpha=0.5, padding=0.):
    ''' Write map with location of several nansat objects

    '''
    meanLon = []
    meanLat = []
    lons = []
    lats = []
    minLon = 181
    maxLon = -181
    minLat = 91
    maxLat = -91
    for n in list_of_nobjs:
        lonVec, latVec = n.get_border()
        lonVec = np.array(lonVec)
        latVec = np.array(latVec)
        lons.append(lonVec)
        lats.append(latVec)
        # estimate mean/min/max values of lat/lon of the shown area
        # (real lat min max +/- latBorder) and (real lon min max +/- lonBorder)
        if max(-180, lonVec.min() - lonBorder[0]) < minLon:
            minLon = max(-180, lonVec.min() - lonBorder[0])
        if min(180, lonVec.max() + lonBorder[1]) > maxLon:
            maxLon = min(180, lonVec.max() + lonBorder[1])
        if max(-90, latVec.min() - latBorder[0]) < minLat:
            minLat = max(-90, latVec.min() - latBorder[0])
        if min(90, latVec.max() + latBorder[1])> maxLat:
            maxLat = min(90, latVec.max() + latBorder[1])

        meanLon.append(lonVec.mean())
        meanLat.append(latVec.mean())

    meanLon = np.array(meanLon).mean()
    meanLat = np.array(meanLat).mean()
        
    # generate template map (can be also tmerc)
    f = plt.figure(num=1, figsize=figureSize, dpi=dpi)
    bmap = Basemap(projection=projection,
                    lat_0=meanLat, lon_0=meanLon,
                    llcrnrlon=minLon, llcrnrlat=minLat,
                    urcrnrlon=maxLon, urcrnrlat=maxLat,
                    resolution=resolution)

    # add content: coastline, continents, meridians, parallels
    bmap.drawcoastlines()
    bmap.fillcontinents(color=continetsColor)
    bmap.drawmeridians(np.linspace(minLon, maxLon, meridians))
    bmap.drawparallels(np.linspace(minLat, maxLat, parallels))

    for lonVec, latVec in zip(lons,lats):
        # convert input lat/lon vectors to arrays of vectors with one row
        # if only one vector was given
        if len(lonVec.shape) == 1:
            lonVec = lonVec.reshape(1, lonVec.shape[0])
            latVec = latVec.reshape(1, latVec.shape[0])

        for lonSubVec, latSubVec in zip(lonVec, latVec):
            # convert lat/lons to map units
            mapX, mapY = bmap(list(lonSubVec.flat), list(latSubVec.flat))

            # from x/y vectors create a Patch to be added to map
            boundary = Polygon(zip(mapX, mapY),
                                alpha=pAlpha, ec=pLine, fc=pColor)

            # add patch to the map
            plt.gca().add_patch(boundary)
            plt.gca().set_aspect('auto')
            plt.draw()

    # save figure and close
    plt.savefig(outputFileName, bbox_inches='tight',
                dpi=dpi, pad_inches=padding)
    plt.close('all')

