#Definition of inputs and outputs
#==================================
##Sentinel Tools=group
##Sentinel-2 atmospheric correction=name
##ParameterRaster|input_file|Input file (band stacked)|False|False
##ParameterFile|meta_file|Sentinel-2 metadata file|False|False|
##ParameterSelection|method|Output type|Dark Object Subtraction (DOS);Top-of-atmosphere reflectance;Top-of-atmosphere radiance|0
##OutputRaster|output_file|Output file

import sys
import os

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.outputs import OutputRaster
from processing.core.parameters import ParameterSelection
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterFile

here = os.path.dirname(scriptDescriptionFile)
if here not in sys.path:
    sys.path.append(here)
from s2_dos_correction import atmProcessingMain

methodList = ["DOS", "TOA", "RAD"]

options = {}
# input/output parameters
options["input_file"] = input_file
options["metadata_file"] = meta_file
options["output_file"] = output_file
# Atmospheric correction parameters
options["atmCorrMethod"] = methodList[method]

reflectanceImg = atmProcessingMain(options)
