# -*- coding: utf-8 -*-
"""
Created on Tue Sep 09 12:54:33 2014

@author: rmgu
"""
import numpy as np
import os
import glob
from xml.etree import ElementTree as ET
from math import cos, radians, pi
from osgeo import gdal

driverOptionsGTiff = ['COMPRESS=DEFLATE', 'PREDICTOR=1', 'BIGTIFF=IF_SAFER']


def atmProcessingMain(options):

    # Commonly used filenames
    input_file = options["input_file"]
    metadata_file = options["metadata_file"]
    output_file = options["output_file"]

    # Correction options
    atmCorrMethod = options["atmCorrMethod"]

    # Read metadata in to dictionary
    metadata_file = readMetadataS2L1C(metadata_file)

    # Get reflectance or radiance
    inImg = gdal.Open(input_file)
    if atmCorrMethod in ["DOS", "TOA"]:
        if atmCorrMethod == "DOS":
            doDOS = True
        else:
            doDOS = False
        output_image = toaReflectanceS2(inImg, metadata_file, output_file, doDOS=doDOS)
    elif atmCorrMethod == "RAD":
        output_image = toaRadianceS2(inImg, metadata_file, output_file)

    inImg = None
    output_image = None


# Method taken from the bottom of http://s2tbx.telespazio-vega.de/sen2three/html/r2rusage.html
# Assumes a L1C product which contains TOA reflectance: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/product-types
def toaRadianceS2(inImg, metadataFile, output_file):
    e0 = []
    for e in metadataFile['irradiance_values']:
        e0.append(float(e))
    z = float(metadataFile['sun_zenit'])

    visNirBands = range(1, 10)
    # Convert to radiance
    radiometricData = np.zeros((inImg.RasterYSize, inImg.RasterXSize, len(visNirBands)))
    for i in range(len(visNirBands)):
        rToa = inImg.GetRasterBand(i+1).ReadAsArray()
        radiometricData[:, :, i] = (rToa * e0[i] * cos(radians(z))) / pi
    res = saveImg(radiometricData, inImg.GetGeoTransform(), inImg.GetProjection(), output_file)
    return res


# Assumes a L1C product which contains TOA reflectance: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/product-types
def toaReflectanceS2(inImg, metadataFile, output_file, doDOS=False):

    # perform dark object substraction
    if doDOS:
        dosDN = darkObjectSubstraction(inImg)
    else:
        dosDN = list(np.zeros((inImg.RasterYSize, inImg.RasterXSize)))

    # Convert to TOA reflectance
    rToa = np.zeros((inImg.RasterYSize, inImg.RasterXSize, inImg.RasterCount))
    for i in range(inImg.RasterCount):
        rawData = inImg.GetRasterBand(i+1).ReadAsArray()
        rToa[:, :, i] = np.where((rawData-dosDN[i]) > 0, rawData-dosDN[i], 0)

    res = saveImg(rToa, inImg.GetGeoTransform(), inImg.GetProjection(), output_file)
    return res


def darkObjectSubstraction(inImg):
    dosDN = []
    tempData = inImg.GetRasterBand(1).ReadAsArray()
    numElements = np.size(tempData[tempData != 0])
    tempData = None
    for band in range(1, inImg.RasterCount+1):
        hist, edges = np.histogram(inImg.GetRasterBand(band).ReadAsArray(), bins=2048,
                                   range=(1, 2048), density=False)
        for i in range(1, len(hist)):
            if hist[i] - hist[i-1] > (numElements-numElements*0.999999):
                dosDN.append(i-1)
                break
    return dosDN


def readMetadataS2L1C(metadataFile):
    # Get parameters from main metadata file
    ProductName = os.path.split(os.path.dirname(metadataFile))[1]
    tree = ET.parse(metadataFile)
    root = tree.getroot()
    namespace = root.tag.split('}')[0]+'}'

    baseNodePath = "./"+namespace+"General_Info/Product_Info/"
    dateTimeStr = root.find(baseNodePath+"PRODUCT_START_TIME").text
    procesLevel = root.find(baseNodePath+"PROCESSING_LEVEL").text
    spaceCraft = root.find(baseNodePath+"Datatake/SPACECRAFT_NAME").text
    orbitDirection = root.find(baseNodePath+"Datatake/SENSING_ORBIT_DIRECTION").text

    baseNodePath = "./"+namespace+"General_Info/Product_Image_Characteristics/"
    quantificationVal = root.find(baseNodePath+"QUANTIFICATION_VALUE").text
    reflectConversion = root.find(baseNodePath+"Reflectance_Conversion/U").text
    irradianceNodes = root.findall(baseNodePath+"Reflectance_Conversion/Solar_Irradiance_List/SOLAR_IRRADIANCE")
    e0 = []
    for node in irradianceNodes:
        e0.append(node.text)

    # save to dictionary
    metaDict = {}
    metaDict.update({'product_name': ProductName,
                     'product_start': dateTimeStr,
                     'processing_level': procesLevel,
                     'spacecraft': spaceCraft,
                     'orbit_direction': orbitDirection,
                     'quantification_value': quantificationVal,
                     'reflection_conversion': reflectConversion,
                     'irradiance_values': e0})
    # granule
    XML_mask = 'MTD_TL.xml'
    globlist = os.path.join(os.path.dirname(metadataFile), "GRANULE", "L1C_*", XML_mask)
    metadataTile = glob.glob(globlist)[0]
    # read metadata of tile
    tree = ET.parse(metadataTile)
    root = tree.getroot()
    namespace = root.tag.split('}')[0]+'}'
    # Get sun geometry - use the mean
    baseNodePath = "./"+namespace+"Geometric_Info/Tile_Angles/"
    sunGeometryNodeName = baseNodePath+"Mean_Sun_Angle/"
    sunZen = root.find(sunGeometryNodeName+"ZENITH_ANGLE").text
    sunAz = root.find(sunGeometryNodeName+"AZIMUTH_ANGLE").text
    # Get sensor geometry - assume that all bands have the same angles
    # (they differ slightly)
    sensorGeometryNodeName = baseNodePath+"Mean_Viewing_Incidence_Angle_List/Mean_Viewing_Incidence_Angle/"
    sensorZen = root.find(sensorGeometryNodeName+"ZENITH_ANGLE").text
    sensorAz = root.find(sensorGeometryNodeName+"AZIMUTH_ANGLE").text
    EPSG = tree.find("./"+namespace+"Geometric_Info/Tile_Geocoding/HORIZONTAL_CS_CODE").text
    cldCoverPercent = tree.find("./"+namespace+"Quality_Indicators_Info/Image_Content_QI/CLOUDY_PIXEL_PERCENTAGE").text
    for elem in tree.iter(tag='Size'):
        if elem.attrib['resolution'] == '10':
            rows_10 = int(elem[0].text)
            cols_10 = int(elem[1].text)
        if elem.attrib['resolution'] == '20':
            rows_20 = int(elem[0].text)
            cols_20 = int(elem[1].text)
        if elem.attrib['resolution'] == '60':
            rows_60 = int(elem[0].text)
            cols_60 = int(elem[1].text)
    for elem in tree.iter(tag='Geoposition'):
        if elem.attrib['resolution'] == '10':
            ULX_10 = int(elem[0].text)
            ULY_10 = int(elem[1].text)
        if elem.attrib['resolution'] == '20':
            ULX_20 = int(elem[0].text)
            ULY_20 = int(elem[1].text)
        if elem.attrib['resolution'] == '60':
            ULX_60 = int(elem[0].text)
            ULY_60 = int(elem[1].text)

    # save to dictionary
    metaDict.update({'sun_zenit': sunZen,
                     'sun_azimuth': sunAz,
                     'sensor_zenit': sensorZen,
                     'sensor_azimuth': sensorAz,
                     'projection': EPSG,
                     'cloudCoverPercent': cldCoverPercent,
                     'rows_10': rows_10,
                     'cols_10': cols_10,
                     'rows_20': rows_20,
                     'cols_20': cols_20,
                     'rows_60': rows_60,
                     'cols_60': cols_60,
                     'ULX_10': ULX_10,
                     'ULY_10': ULY_10,
                     'ULX_20': ULX_20,
                     'ULY_20': ULY_20,
                     'ULX_60': ULX_60,
                     'ULY_60': ULY_60})
    return metaDict


# save the data to geotiff or memory
def saveImg(data, geotransform, proj, outPath, noDataValue=0):

    # Start the gdal driver for GeoTIFF
    if outPath == "MEM":
        driver = gdal.GetDriverByName("MEM")
        driverOpt = []
    else:
        driver = gdal.GetDriverByName("GTiff")
        driverOpt = driverOptionsGTiff

    shape = data.shape
    if len(shape) > 2:
        ds = driver.Create(outPath, shape[1], shape[0], shape[2], gdal.GDT_Int16, driverOpt)
        ds.SetProjection(proj)
        ds.SetGeoTransform(geotransform)
        for i in range(shape[2]):
            ds.GetRasterBand(i+1).WriteArray(data[:, :, i].astype(int))
            ds.GetRasterBand(i+1).SetNoDataValue(noDataValue)
    else:
        ds = driver.Create(outPath, shape[1], shape[0], 1, gdal.GDT_Float32)
        ds.SetProjection(proj)
        ds.SetGeoTransform(geotransform)
        ds.GetRasterBand(1).WriteArray(data.astype(int))
        ds.GetRasterBand(1).SetNoDataValue(noDataValue)

    return ds
