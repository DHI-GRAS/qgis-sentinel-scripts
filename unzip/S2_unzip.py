#Definition of inputs and outputs
#==================================
##Sentinel Tools=group
##Unzip Sentinel-2 data=name
##ParameterFile|inFile|zipped file|False|False|zip
##OutputDirectory|processingDir|Directory to unzip data to

import os
import glob
import zipfile

def unzip(src_file, dst_dir):
    with zipfile.ZipFile(src_file) as zf:
        zf.extractall(u'\\\\?\\' + dst_dir)

feedback.pushConsoleInfo('Starting unzip')
unzip(inFile, processingDir)
feedback.pushConsoleInfo('Unzip finished...')
