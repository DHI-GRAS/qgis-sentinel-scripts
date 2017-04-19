#Definition of inputs and outputs
#==================================
##Sentinel Tools=group
##Export Sentinel-2 data=name
##ParameterFile|inDir|Sentinel-2 product folder (.SAFE)|True|False|
##ParameterBoolean|B1|Band 1 (Aerosol 60m)|False
##ParameterBoolean|B2|Band 2 (Blue 10m)|False
##ParameterBoolean|B3|Band 3 (Green 10m)|False
##ParameterBoolean|B4|Band 4 (Red 10m)|False
##ParameterBoolean|B5|Band 5 (Red edge 20m)|False
##ParameterBoolean|B6|Band 6 (Red edge 20m)|False
##ParameterBoolean|B7|Band 7 (Red edge 20m)|False
##ParameterBoolean|B8|Band 8 (NIR 10m)|False
##ParameterBoolean|B8A|Band 8A (Red edge 20m)|False
##ParameterBoolean|B9|Band 9 (Water vapour 60m|False
##ParameterBoolean|B10|Band 10 (Cirrus 60m)|False
##ParameterBoolean|B11|Band 11 (Snow/Ice/Cloud 20m)|False
##ParameterBoolean|B12|Band 12 (Snow/Ice/Cloud 20m)|False
##ParameterBoolean|allVISNIR|All VIS + NIR bands (1-8A, needed for atmospheric correction)|True
##ParameterSelection|out_res|Output resolution|10 meter;20 meter;60 meter
##ParameterString|granules|Only process given granules separated with comma eg. 32UNG,33UUB (To find relevant granules - check ESA kml file).|
##*ParameterNumber|maxCldCov|Maximum cloud cover %|0|100|100
##*ParameterNumber|minDataCov|Minimum data cover %|0|100|0
##OutputDirectory|outDir|Directory to save the exported data in
import os
import sys
here = os.path.dirname(scriptDescriptionFile)
if here not in sys.path:
    sys.path.append(here)
import s2_export

# Parse inputs

bandList = s2_export.flags_to_bandlist(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12, allVISNIR)

# output resolution ('10m', '20m', '60m')
out_res_names = ["10", "20", "60"]
out_res = out_res_names[out_res]

# Get the granules
if not granules.strip():
    granules = []
else:
    # parse string list
    granules = granules.split(',')

s2_export.s2_to_gtiff(
        inDir, granules, out_res, bandList, outDir,
        maxCldCov=maxCldCov, minDataCov=minDataCov, progress=progress)
