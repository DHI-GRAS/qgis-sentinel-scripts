# function for calculating a selction of Sentinel 2 Spectral indices
# Kenneth Grogan 3/11/2016 Sun 21/12/2016

import os
import gdal
import numpy as np

def standard_index(band1, band2):
    """Function for standard index calculation"""
    idx = (band1 - band2)/(band1 + band2)
    return idx

def extract_band(stack, bnd_num):
    """Function to extract single bands from stack; stack = input stack, bnd_num = the band number to extract"""
    b = stack.GetRasterBand(bnd_num)
    band = b.ReadAsArray().astype(np.float32)
    return band


def calc_index(stack, bnd_num1, bnd_num2):
    """ Function to calculate an index; stack = input stack, bnd_numx = the band number in the stack"""
    band1 = extract_band(stack, bnd_num1)
    band2 = extract_band(stack, bnd_num2)
    any_index = standard_index(band1, band2)
    return any_index


def sen2indices(inRst, outDir):
    """
    Main function for calculating a selction of Sentinel 2 Spectral indices
    """
    stk = gdal.Open(inRst)

    # get raster specs
    xsize = stk.RasterXSize
    ysize = stk.RasterYSize
    proj = stk.GetProjection()
    geotransform = stk.GetGeoTransform()

    # calculate indices: these indices were chosen based on variable importance ranking from Random Forest classification
    # calc ndvi
    ndvi_b8_b4 = calc_index(stk, 7, 3)

    # calc red edge ndi b8a_b5
    re_ndi_b8a_b5 = calc_index(stk, 8, 4)

    # calc red edge ndi b7_b5
    re_ndi_b7_b5 = calc_index(stk, 6, 4)

    # calc mNDWI
    ndwi_b3_b11 = calc_index(stk, 2, 9)

    # calc NDWI
    ndwi_b3_b8 = calc_index(stk, 2, 7)

    # calc DVW
    dvw = ndvi_b8_b4 - ndwi_b3_b8

    # Stack and write to disk
    # get base filename and combine with outpath
    sName = os.path.splitext(os.path.basename(inRst))[-2]
    stkPath = os.path.join(outDir, sName + '_indices.tif')
    drv = gdal.GetDriverByName('GTiff')
    outTif = drv.Create(stkPath, xsize, ysize, 5, gdal.GDT_Float32)
    outTif.SetProjection(proj)
    outTif.SetGeoTransform(geotransform)
    outTif.GetRasterBand(1).WriteArray(ndvi_b8_b4)
    outTif.GetRasterBand(2).WriteArray(re_ndi_b8a_b5)
    outTif.GetRasterBand(3).WriteArray(re_ndi_b7_b5)
    outTif.GetRasterBand(4).WriteArray(ndwi_b3_b11)
    outTif.GetRasterBand(5).WriteArray(dvw)
    outTif = None
    return stkPath
