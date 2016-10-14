# -*- coding: utf-8 -*-

"""
Script to prepare a (Bruker) tomographic dataset for use with the
[STEPanizer](http://stepanizer.com/)
It looks how many reconstructed files we have and letzs the user decide
on disector width, etc.
"""

# Import modules
from optparse import OptionParser
import sys
import os
import glob
import logging
import time
import datetime
import scipy.misc


def get_pixelsize(logfile):
    """Get the pixel size from the scan log file"""
    with open(logfile, 'r') as f:
        for line in f:
            if 'Image Pixel' in line and 'Scaled' not in line:
                pixelsize = float(line.split('=')[1])
    return(pixelsize)

# Setup the options to run the script and to ask from the user
parser = OptionParser()
usage = 'usage: %prog [options] arg'
parser.add_option('-f', '--folder', dest='RecFolder', type='str',
                  default='/home/habi/uCT-Archive-Online/Brain-Grenoble/M41_bb_D24T14/rec/',
                  metavar='SampleA/rec', help='Location of the reconstructions')
parser.add_option('-n', '--FileNumber', dest='NumFiles', type=int, default=10,
                  metavar='18',
                  help='Number of reconstructions to convert for STEPanizer. The script will select them equally spaced throughout the whole set of images')
parser.add_option('-v', '--voxelsize', dest='voxelsize', type='float',
                  metavar=11, help='Voxel size of the scan. Read from the log file, but can be overriden manually')
parser.add_option('-d', '--DrawScaleBar', dest='ScaleBar', type=int,
                  default=100, metavar='256',
                  help='Draw a scale bar with the given length (in micrometer) in the bottom right of the image')
(options, args) = parser.parse_args()

# Show the help if necessary parameters are missing
if not options.RecFolder:
    parser.print_help()
    print
    sys.exit('You need to give me an rec folder as input...')

if not os.path.isdir(options.RecFolder):
    print('Please give me a correct folder (and only the folder) as input')

SampleFolder = os.path.split(os.path.abspath(options.RecFolder))[0]
try:
    OutFolder = os.path.join(SampleFolder, 'STEPanizer')
    os.makedirs(OutFolder)
except OSError:
    print('STEPanizer directory already exists')    

# Set up logging
logging.basicConfig(filename=os.path.join(OutFolder, 'STEPanizerizer.log'),
                    level=logging.INFO, format='%(message)s')
logging.info('Started conversion at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
logging.info(80 * '-')
    
if not options.voxelsize:
    options.voxelsize = get_pixelsize(glob.glob(os.path.join(options.RecFolder, '*.log'))[0])
print('The scan was done with a voxel size of %0.2f um' % options.voxelsize)

print('Looking for *.png files in %s' % options.RecFolder)
ReconstructionNames = glob.glob(os.path.join(options.RecFolder, '*rec*.png'))
print('We found %s reconstructions' % len(ReconstructionNames))
print('We will select %s images from these and rewrite them to %s' % (options.NumFiles, OutFolder))

logging.info('%s images are written fom %s to %s' % (options.NumFiles, os.path.abspath(options.RecFolder), os.path.abspath(OutFolder)))

# Get the common prefix of all the reconstuctions. Strip trailing zeros and
# 'rec'. This will be the prefix of the STEPanizer files.
CommonPrefix = os.path.split(os.path.abspath(os.path.commonprefix(ReconstructionNames)))[1].rstrip('0').strip('_rec')

# Calculate which files we need to read, based on the total file number and the requested file number
StepWidth = int(round(len(ReconstructionNames) / (options.NumFiles - 1)))

# Actually read the files now. They go from *.png to (resized) *.jpg
for c, i in enumerate(ReconstructionNames[::StepWidth]):
    rec = scipy.misc.imread(i, flatten=True)
    OutputName = os.path.join(OutFolder, '%s_%s.jpg' % (CommonPrefix, c + 1))
    Output = '%s/%s: %s --> %s' % (c + 1, len(ReconstructionNames[::StepWidth]),
                                   os.path.split(i)[1], os.path.split(OutputName)[1])
    print(Output)
    #~ if options.ScaleBar:
        #~ CurrentSlice(size(DICOMFile,1)-10-(round(ScaleBarLength/10)):size(DICOMFile,1)-10,10:10+ScaleBarLength) = 255; % draw Scalebar of length(ScaleBarLength) in the bottom left corner, with 10 times the length of the height.
    if options.resize:
        rec = scipy.misc.imresize(rec, (1024, 1024), interp='bilinear', mode=None)[source]¶
    scipy.misc.imsave(OutputName, rec)
    logging.info(Output)

# TODO: Add scale bar
# TODO: Not only load N slices throughout dataset, but load slices M um apart
# TODO: Disector

logging.info(80 * '-')
logging.info('Conversion finished at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
