import os
import glob
import zipfile
from qgis.processing import alg

@alg(
    name="unzipsentinel2data",
    label=alg.tr("Unzip Sentinel-2 data"),
    group="sentineltools",
    group_label=alg.tr("Sentinel Tools"),
)
@alg.input(
    type=alg.FILE,
    name="inFile",
    label="zipped file",
    behavior=0,
    optional=False,
    fileFilter="zip",
)
@alg.input(type=alg.FILE_DEST, name="processingDir", label="Directory to unzip data to")
def unzipsentinel2data(instance, parameters, context, feedback, inputs):
    """ unzipsentinel2data """
    inFile = instance.parameterAsString(parameters, 'inFile', context)
    processingDir = instance.parameterAsString(parameters, 'processingDir', context)
    
    def unzip(src_file, dst_dir):
        with zipfile.ZipFile(src_file) as zf:
            zf.extractall(u'\\\\?\\' + dst_dir)

    feedback.pushConsoleInfo('Starting unzip')
    unzip(inFile, processingDir)
    feedback.pushConsoleInfo('Unzip finished...')
