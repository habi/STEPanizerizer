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
import datetime
import scipy.misc
import matplotlib.pyplot as plt

# Display all images in b&w and with nearest neighbour interpolation
plt.rc('image', cmap='gray', interpolation='nearest') 

def get_pixelsize(logfile):
    """Get the pixel size from the scan log file"""
    with open(logfile, 'r') as f:
        for line in f:
            if 'Image Pixel' in line and 'Scaled' not in line:
                pixelsize = float(line.split('=')[1])
    return(pixelsize)

def get_git_hash():
    """
    Get the current git hash from the repository.
    Good for saving this information into the log files of process.
    Based on http://stackoverflow.com/a/14989911/323100
    """
    import subprocess
    return(subprocess.check_output(["git", "describe", "--always"]).strip().decode('utf-8'))

# Setup the options to run the script and to ask from the user
parser = OptionParser()
usage = 'usage: %prog [options] arg'
parser.add_option('-f', '--folder', dest='RecFolder', type='str',
                  default='/home/habi/uCT-Archive-Online/Brain-Grenoble/M41_bb_D24T14/rec/',
                  metavar='SampleA/rec', help='Location of the reconstructions')
parser.add_option('-n', '--FileNumber', dest='NumFiles', type=int, default=10,
                  metavar='18',
                  help='Number of reconstructions to convert for STEPanizer. The script will select them equally spaced throughout the whole set of images. (Default=%default)')
parser.add_option('-p', '--pixelsize', dest='pixelsize', type='float',
                  metavar=11, help='Pixel/Voxel size of the scan. Read from the log file, but can be overriden manually')
parser.add_option('-b', '--ScaleBar', dest='scalebar', type=int,
                  default=1000, metavar='256',
                  help='Draw a scale bar with the given length (in micrometer) in the bottom right of the image. (Default scalebar length=%default um)')
parser.add_option('-r', '--Resize', dest='resize', type=int, metavar='1600',
                  help='Resize the input image to this side length.')                  
parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                  help='Be really chatty, (Default=Be quiet)',
metavar=1)                  
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
logging.info('STEPanizerizer (version %s) has been run with this command line\n--\n%s\n--' % (get_git_hash(), ' '.join(sys.argv)))
logging.info('Conversion started at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
logging.info(80 * '-')
    
if not options.pixelsize:
    options.pixelsize = get_pixelsize(glob.glob(os.path.join(options.RecFolder, '*.log'))[0])
print('The scan was done with a voxel size of %0.2f um.' % options.pixelsize)
# Calculate the pixel length of the scale bar
ScaleBarPixels = int(round(options.scalebar / options.pixelsize))
print('A scale bar of %s um will thus be about %s px long.' % (options.scalebar, ScaleBarPixels))

print('Looking for *.png files in %s' % options.RecFolder)
ReconstructionNames = glob.glob(os.path.join(options.RecFolder, '*rec*.png'))
print('We found %s reconstructions' % len(ReconstructionNames))
print('We will select %s images from these and rewrite them to %s' % (options.NumFiles, OutFolder))

logging.info('%s images are written fom %s to %s' % (options.NumFiles, os.path.abspath(options.RecFolder), os.path.abspath(OutFolder)))
logging.info('The scale bar at the bottom right of the images is %s um long' % options.scalebar)
logging.info(80 * '-')

# Get the common prefix of all the reconstuctions. Strip trailing zeros and
# 'rec'. And also strip the InstaRecon suffix if we have that. The resulting
# string is the prefix of the STEPanizer files.
CommonPrefix = os.path.split(os.path.abspath(os.path.commonprefix(ReconstructionNames)))[1].rstrip('0').strip('_rec').strip('_IR')

# Calculate which files we need to read, based on the total file number and the requested file number
StepWidth = int(round(len(ReconstructionNames) / (options.NumFiles - 1)))

# Actually read the files now. They go from *.png to (scale-barred and resized) *.jpg
for c, i in enumerate(ReconstructionNames[::StepWidth]):
    rec = scipy.misc.imread(i, flatten=True)
    OutputName = os.path.join(OutFolder, '%s_%s.jpg' % (CommonPrefix, c + 1))
    Output = '%s/%s: %s --> %s' % (c + 1, len(ReconstructionNames[::StepWidth]),
                                   os.path.split(i)[1], os.path.split(OutputName)[1])
    print(Output)
    if options.scalebar:
        # Add white scalebar with the given length (and 1/10 of it as height) at the bottom right of the image
        fromborder = 200
        rec[-fromborder-ScaleBarPixels/10.:-fromborder,
            -fromborder-ScaleBarPixels:-fromborder]=255
    if options.resize:
        print('Resizing output image to %sx%s px' % (options.resize, options.resize))
        rec = scipy.misc.imresize(rec, (options.resize, options.resize))
    if options.verbose:
        #~ plt.ion()
        plt.imshow(rec)
        plt.title(Output)
        plt.show()
    scipy.misc.imsave(OutputName, rec)
    logging.info(Output)

# TODO: Not only load N slices throughout dataset, but load slices M um apart
# TODO: Implement Disector

logging.info(80 * '-')
logging.info('Conversion finished at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
