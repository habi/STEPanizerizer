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
import numpy
import scipy.misc
import random
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
    Get the current git hash from the repository, which is written to the log file.
    Based on http://stackoverflow.com/a/14989911/323100
    """
    import subprocess
    return(subprocess.check_output(["git", "describe", "--always"]).strip().decode('utf-8'))

# Setup the options to run the script and to ask from the user
parser = OptionParser()
usage = 'usage: %prog [options] arg'
parser.add_option('-f', '--folder', dest='SampleFolder', type='str',
                  metavar='SampleA',
                  help='Sample folder. We will look for the "rec" folder inside.')
parser.add_option('-n', '--FileNumber', dest='NumFiles', type=int, default=15,
                  metavar='18',
                  help='Number of reconstructions to convert for STEPanizer. The script will select them equally spaced throughout the whole set of images. (Default=%default)')
parser.add_option('-p', '--pixelsize', dest='pixelsize', type='float',
                  metavar=11,
                  help='Pixel/Voxel size of the scan. Read from the log file, but can be overriden manually')
parser.add_option('-d', '--disector', dest='Disector', type='float',
                  metavar=5.3, help='Disector thickness in um.')
parser.add_option('-b', '--ScaleBar', dest='scalebar', type=int, default=1000,
                  metavar='256', help='Draw a scale bar with the given length (in micrometer) in the bottom right of the image. (Default scalebar length=%default um)')
parser.add_option('-r', '--Resize', dest='resize', type=int, metavar='1600',
                  help='Resize the input image to this side length (for the *longest* axis).')
parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                  help='Be really chatty, (Default=Be quiet)', metavar=1)
(options, args) = parser.parse_args()

# Show the help if necessary parameters are missing
if not options.SampleFolder:
    parser.print_help()
    print
    sys.exit('You need to give me a sample folder as input...')

if options.Disector:
    sys.exit('Disector functionality not implemented yet, sorry!')

if not os.path.isdir(options.SampleFolder):
    print('Please give me a correct folder (and only the folder) as input')

try:
    OutFolder = os.path.join(options.SampleFolder, 'STEPanizer')
    os.makedirs(OutFolder)
except OSError:
    print('STEPanizer directory already exists, we just continue')

print('Looking for *.png files in %s' % os.path.join(options.SampleFolder, 'rec'))
ReconstructionNames = glob.glob(os.path.join(options.SampleFolder, 'rec', '*rec*.png'))
print('We found %s reconstructions' % len(ReconstructionNames))
print('We will select %s images from these and rewrite them to %s' % (options.NumFiles,
                                                                      OutFolder))

# Get image size (which we need for resizing), obviously only if requested
# We then use this to calculate a resize fraction. This float value then takes
# care of non-square image resizing according to https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imresize.html
if options.resize:
    # Read a random image from the dataset, grab its side lengths and save the maximum (for non-square images).
    longest_side = numpy.max(numpy.shape(
        scipy.misc.imread(random.choice(ReconstructionNames), flatten=True)))
    if options.resize > longest_side:
        print('\nWe will not upscale images (from %s px to %s px)' % (
            longest_side, options.resize))
        sys.exit(
            'Please reduce the "-r" option to somethign below %s px' % longest_side)
    options.resize /= float(longest_side)

# Set up logging
logging.basicConfig(filename=os.path.join(OutFolder, 'STEPanizerizer.log'),
                    level=logging.INFO, format='%(message)s')
logging.info('STEPanizerizer (version %s) has been run with this command line\n--\n%s\n--' % (get_git_hash(),
                                                                                              ' '.join(sys.argv)))
logging.info('Conversion started at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
logging.info(80 * '-')
logging.info('Approximately %s images are written fom %s to %s' % (options.NumFiles,
                                                                   os.path.abspath(os.path.join(options.SampleFolder, 'rec')),
                                                                   os.path.abspath(OutFolder)))
# Get pixel size, which we need for the scale bar
if not options.pixelsize:
    options.pixelsize = get_pixelsize(
        glob.glob(os.path.join(options.SampleFolder, 'rec', '*.log'))[0])
print('The scan was done with a voxel size of %0.2f um.' % options.pixelsize)

# Calculate the pixel length of the scale bar
ScaleBarPixels = int(round(options.scalebar / float(options.pixelsize)))

# Set up resize value, if requested
if options.resize:
    logging.info('The longest side of the image is being resized from %s px to %0.2f%% of it: %0.0f px' % (longest_side,
                                                                                                           (100 * options.resize),
                                                                                                           longest_side * options.resize))
    print('A scale bar of %s um will thus be about %0.0f px long.' % (options.scalebar,
                                                                      ScaleBarPixels * options.resize))
else:
    print('A scale bar of %s um will thus be about %s px long.' % (options.scalebar,
                                                                   ScaleBarPixels))

# Log some more
logging.info('The scale bar at the bottom right of the images corresponds to %s um.' % options.scalebar)
logging.info('We use uniform random sampling, so the start and end slice will be different each time the script is run!')
logging.info(80 * '-')

# Get the common prefix of all the reconstructions. Strip trailing zeroes and
# 'rec'. And also strip the InstaRecon suffix if we have that. The resulting
# string is the prefix of the STEPanizer files.
CommonPrefix = os.path.split(os.path.abspath(os.path.commonprefix(ReconstructionNames)))[1].rstrip('0').strip('_rec').strip('_IR')

# Calculate which files we need to read, based on the total and the requested file number
StepWidth = int(round(len(ReconstructionNames) / float(options.NumFiles)))

# Actually read the files now.
# They are converted from *.png to (scale-barred and resized) *.jpg with 'no leading zero' numbering, as STEPanizer would like.
# Start at a random interval from 0 to 'StepWidth'.
# This takes care of Systematic Uniform Random Sampling, where we have equal distance between slices but a different start (see: http://www.stereology.info/sampling/)
if options.verbose:
    plt.figure()
    plt.ion()
for c, i in enumerate(ReconstructionNames[numpy.random.randint(StepWidth)::StepWidth]):
    rec = scipy.misc.imread(i, flatten=True)
    OutputName = os.path.join(OutFolder, '%s_%s.jpg' % (CommonPrefix, c + 1))
    Output = '%s/%s: %s --> %s' % (c + 1, len(ReconstructionNames[::StepWidth]),
                                   os.path.split(i)[1],
                                   os.path.split(OutputName)[1])
    print(Output)
    if options.scalebar:
        # Add white scalebar with the given length (and 1/10 of it as height) at the bottom right of the image
        fromborder = 200
        rec[int(round(-fromborder - ScaleBarPixels / 10.)):-fromborder,
            int(round(-fromborder - ScaleBarPixels)):-fromborder] = 255
    if options.resize:
        print('Shrinking image to %0.2f %% of original size' % (100 * options.resize))
        # Resize with float value of requested and given size
        rec = scipy.misc.imresize(rec, options.resize)
    if options.verbose:
        plt.imshow(rec)
        plt.title(Output)
        plt.draw()
        plt.pause(0.001)
    scipy.misc.imsave(OutputName, rec)
    logging.info(Output)

# TODO: Not only load N slices throughout dataset, but load slices M um apart
# TODO: Implement Disector

logging.info(80 * '-')
logging.info('Conversion finished at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
