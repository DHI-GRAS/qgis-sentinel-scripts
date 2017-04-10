from __future__ import division
import os
import glob
import fnmatch

import osr
import numpy as np
import scipy.ndimage

from qgis_utils import DummyProgress
import gdal_utils

from atmospheric_correction.read_satellite_metadata import readMetadataS2L1C


def find_tiles(input_dir, granules=[]):
    """Find tile paths given list of granule names"""
    tiledir = os.path.join(input_dir, 'GRANULE')
    if granules:
        tiles = []
        for tilefile in os.listdir(tiledir):
            for granule in granules:
                pattern = 'S2*_T{}_*'.format(granule)
                if fnmatch.fnmatch(tilefile, pattern):
                    tiles.append(os.path.join(tiledir, tilefile))
    else:
        pattern = os.path.join(tiledir, '*')
        tiles = glob.glob(pattern)
        if not tiles:
            raise ValueError('No tiles found for pattern \'{}\'.'.format(pattern))
    return tiles


def s2_to_gtiff(inDir, granules, out_res, bandList, outDir,
        maxCldCov=100, minDataCov=0, progress=None):
    """Export Sentinel 2 data to GeoTiff

    Parameters
    ----------
    inDir : str
        input directory (unzipped SAFE archive)
    granules : list of str
        granules to extract
    out_res : str
        output resolution
    bandList : list of str
        bands to retrieve
    outDir : str
        ouput directory
    maxCldCov : float
        maximum cloud cover to extract
        in percent (e.g. 100 for 100%)
    minDataCov : float
        minimum data cover to extract
        in percent (e.g. 100 for 100%)
    progress : QGIS progress, optional
        QGIS progress logging
    """
    # make sure input arguments have the right format
    if out_res.lower().endswith('m'):
        out_res = out_res[:-1]
    if progress is None:
        progress = DummyProgress()

    # conversion table from band name to resolution
    bandDictRes = {'B01':60, 'B02':10, 'B03':10, 'B04':10, 'B05':20, 'B06':20,
                   'B07':20, 'B08':10, 'B8A':20, 'B09':60, 'B10':60, 'B11':20,
                   'B12':20}

    # Get parameters from main metadata file
    pattern = os.path.join(inDir, 'S2?_*.xml')
    xmlMain = glob.glob(pattern)[0]
    metaDict = readMetadataS2L1C(xmlMain)

    # Get the granules
    tiles = find_tiles(inDir, granules)

    if not tiles:
        progress.setConsoleInfo('No tiles were found for query {}. Exiting.'.format(granules))
        return []

    # Process granules
    files_exported = []
    for tile in tiles:
        granuleName = tile.split('_')[-2]
        progress.setConsoleInfo('\nProcessing granule: ' + granuleName)

        # Prepare array for data
        ULX = float(metaDict[granuleName]['ULX_'+out_res])
        ULY = float(metaDict[granuleName]['ULY_'+out_res])
        xsize = int(metaDict[granuleName]['cols_'+out_res])
        ysize = int(metaDict[granuleName]['rows_'+out_res])
        geotransform = (ULX, float(out_res), 0.0, ULY, 0.0, float(out_res)*-1)
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(int(metaDict[granuleName]['projection'][5:]))
        projection = sr.ExportToWkt()

        # check if cloud cover is less than limit otherwise skip granule
        cloudCoverPercent = float(metaDict[granuleName].get('cloudCoverPercent', 0))
        dataCheck = 0
        progress.setConsoleInfo('Cloud cover %: {:.0f}'.format(cloudCoverPercent))
        if cloudCoverPercent > maxCldCov:
            dataCheck = dataCheck + 1

        # Open band 1
        band1file = glob.glob(tile + '\\IMG_DATA\\S2*_B01.jp2')[0]
        with gdal_utils.gdal_open(band1file) as ds:
            band1xsize = ds.RasterXSize
            band1ysize = ds.RasterYSize
            band1Arr = ds.GetRasterBand(1).ReadAsArray().astype(np.uint16)

        # calculate % of valid data (0 assumed to be nodata)
        dataPercent = ((band1Arr > 0).sum()/float((band1xsize*band1ysize)))*100.
        # check if data coverage is higher than limit otherwise skip granule
        progress.setConsoleInfo('Data %: {:.0f}'.format(dataPercent))
        if dataPercent < float(minDataCov):
            dataCheck = dataCheck + 2

        # Inform user
        if dataCheck == 1:
            progress.setConsoleInfo('Skipping granule - cloud cover % is too high')
            continue
        elif dataCheck == 2:
            progress.setConsoleInfo('Skipping granule - data % is too low')
            continue
        elif dataCheck == 3:
            progress.setConsoleInfo('Skipping granule - cloud cover % is too high and data % is too low')
            continue

        # store band data
        data = np.zeros((len(bandList), ysize, xsize), dtype=np.uint16)
        bands_stored = []
        bandfile = None
        for b, bandname in enumerate(bandList):
            # find band data file
            fnpattern = 'S2*_{}.jp2'.format(bandname)
            pattern = os.path.join(tile, 'IMG_DATA', fnpattern)
            try:
                bandfile = glob.glob(pattern)[0]
            except IndexError:
                progress.setConsoleInfo('No data found for band {} with search pattern {}. '
                        'Continuing.'.format(bandname, pattern))
                continue
            # export data
            progress.setConsoleInfo('Exporting data for band {} from {} ...'.format(bandname, bandfile))
            banddata = gdal_utils.retrieve_array_masked(bandfile, tgt_dtype='uint16').filled()
            zoom = bandDictRes[bandname] / float(out_res)
            if zoom != 1:
                banddata = scipy.ndimage.interpolation.zoom(banddata, zoom, order=0)
            data[b,:,:] = banddata
            bands_stored.append(b)

        if not bands_stored:
            raise RuntimeError('No band data was retrieved.')

        # save data to Geotiff
        progress.setConsoleInfo('\nSaving GeoTiff')
        outFilename = os.path.join(outDir, os.path.basename(bandfile)[:-8] + '.tif')
        gdal_utils.array_to_gtiff(data, outFilename, projection, geotransform, create_options=[])

        # gather list of exported files
        files_exported.append(outFilename)

    progress.setConsoleInfo('Export Sentinel-2 finished with {} exported files.'.format(len(files_exported)))
    return files_exported


def flags_to_bandlist(B1=False, B2=False, B3=False, B4=False, B5=False, B6=False,
        B7=False, B8=False, B8A=False, B9=False, B10=False, B11=False, B12=False,
        allVISNIR=False):
    """Convenience function to generate list of bands from flags"""
    if allVISNIR:
        bandList = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                    'B07', 'B08', 'B8A']
    else:
        bandList = []
        if B1:
            bandList.append('B01')
        if B2:
            bandList.append('B02')
        if B3:
            bandList.append('B03')
        if B4:
            bandList.append('B04')
        if B5:
            bandList.append('B05')
        if B6:
            bandList.append('B06')
        if B7:
            bandList.append('B07')
        if B8:
            bandList.append('B08')
        if B8A:
            bandList.append('B8A')
        if B9:
            bandList.append('B09')
        if B10:
            bandList.append('B10')
        if B11:
            bandList.append('B11')
        if B12:
            bandList.append('B12')
    return bandList
