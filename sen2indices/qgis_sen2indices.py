#Definition of inputs and outputs
#==================================
##Sentinel 2 Indices=name
##Sentinel Tools=group
##ParameterRaster|input|Input Reflectance Stack|False
##OutputDirectory|outputDirectory|Folder to save the stack of Indices
#OutputRaster|output|Name for Index Stack

# Call the function for Sentinel 2 index calculation
#==================================
import os
import sys
here = os.path.dirname(scriptDescriptionFile)
if here not in sys.path:
    sys.path.append(here)
import sen2indices

print 'Starting index calculation...'
sen2indices.sen2indices(input, outputDirectory)
print 'Finished writing to disk...'

