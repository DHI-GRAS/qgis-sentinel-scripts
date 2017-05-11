# function for calculating a selction of Sentinel 2 Spectral indices
# Kenneth Grogan 3/11/2016

import os
import gdal
import numpy as np

def standard_index(band1, band2):
    """Function for standard index calculation"""
    idx = ((band1 - band2)/(band1 + band2))*10000
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

    # calc ndvi using 8a
    ndvi_b8a_b4 = calc_index(stk, 8, 3)

    # calc red edge ndi b8a_b5
    re_ndi_b8a_b5 = calc_index(stk, 8, 4)

    # calc red edge ndi b8a_b6
    re_ndi_b8a_b6 = calc_index(stk, 8, 5)

    # calc red edge ndi b6_b5
    re_ndi_b6_b5 = calc_index(stk, 5, 4)

    # calc red edge ndi b7_b5
    re_ndi_b7_b5 = calc_index(stk, 6, 4)

    # calc NDII
    ndii_b8a_b11 = calc_index(stk, 8, 9)

    # calc NDMI
    ndwi_b8a_b12 = calc_index(stk, 8, 10)

    # Stack and write to disk
    # get base filename and combine with outpath
    sName = os.path.splitext(os.path.basename(inRst))[-2]
    stkPath = os.path.join(outDir, sName + '_indices.tif')
    drv = gdal.GetDriverByName('GTiff')
    outTif = drv.Create(stkPath, xsize, ysize, 8, gdal.GDT_Int16)
    outTif.SetProjection(proj)
    outTif.SetGeoTransform(geotransform)
    outTif.GetRasterBand(1).WriteArray(ndvi_b8_b4)
    outTif.GetRasterBand(2).WriteArray(ndvi_b8a_b4)
    outTif.GetRasterBand(3).WriteArray(re_ndi_b8a_b5)
    outTif.GetRasterBand(4).WriteArray(re_ndi_b8a_b6)
    outTif.GetRasterBand(5).WriteArray(re_ndi_b6_b5)
    outTif.GetRasterBand(6).WriteArray(re_ndi_b7_b5)
    outTif.GetRasterBand(7).WriteArray(ndii_b8a_b11)
    outTif.GetRasterBand(8).WriteArray(ndwi_b8a_b12)
    outTif = None
    return stkPath
