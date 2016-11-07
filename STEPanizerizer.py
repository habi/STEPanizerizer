# -*- coding: utf-8 -*-

"""
Script to prepare a (Bruker) tomographic dataset for stereological analysis with
the  [STEPanizer](http://stepanizer.com/).
It implements uniform random sampling through the files and draws a scale bar if
requested.
Disector is It looks how many reconstructed files we have and letzs the user decide
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


# Functions
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
parser.add_option('-f', '--folder', dest='samplefolder', type='str', metavar='SampleA',
                  help='Sample folder. We will look for the "rec" folder inside.')
parser.add_option('-n', '--numberoffiles', dest='numfiles', type=int, default=15, metavar='18',
                  help='Number of slices to convert for STEPanizer. The script will select them equally spaced throughout the whole set of images. (Default=%default)')
parser.add_option('-s', '--slicedistance', dest='slicedistance', type=float, metavar='18',
                  help='Slice distance in *micrometers*. (No default)')
parser.add_option('-p', '--pixelsize', dest='pixelsize', type='float', metavar=11,
                  help='Pixel/Voxel size of the scan. Read from the log file, but can be overriden manually')
parser.add_option('-d', '--disectorthickness', dest='disectorthickness', type='float', metavar=5.3,
                  help='Disector thickness in um. (No default)')
parser.add_option('-b', '--ScaleBar', dest='scalebar', type=int, default=1000, metavar='256',
                  help='Draw a scale bar with the given length (in micrometer) in the bottom right of the image. (Default scalebar length=%default um)')
parser.add_option('-r', '--Resize', dest='resize', type=int, metavar='1600',
                  help='Resize the input image to this side length (for the *longest* axis). (No Default)')
parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true', metavar=1,
                  help='Be chatty/informative. (Default=Be quiet)')
(options, args) = parser.parse_args()

# Sanity check for options
# Show the help if necessary parameters are missing
if not options.samplefolder:
    sys.exit('You *need* to give me a sample folder as input (with the "-f" option)...')
# Check if the folder actually exists
if not os.path.isdir(options.samplefolder):
    print('Please give me a correct (i.e. existing) folder as input')
# 'Slice distance' and 'number of files' are mutually exclusive, the user has to choose one or the other.
if options.numfiles and options.slicedistance:
    parser.error('The options "Number of files (-n) and "Slice Distance (-s) are mutually exclusive.\nChoose one or the other, please.\n')
# The 'disector thickness' in not implemented yet'
if options.disectorthickness:
    sys.exit('Disector functionality not implemented yet, sorry!')

# Get the (isotropic) pixel size of the scan.
# We need it for the scale bar and - if requested - disector thickness.
if not options.pixelsize:
    options.pixelsize = get_pixelsize(
        glob.glob(os.path.join(options.samplefolder, 'rec', '*.log'))[0])
print('The scan was done with a voxel size of %0.2f um.' % options.pixelsize)

# Make output directory, named with most important parameters
OutFolder = os.path.join(options.samplefolder, 'STEPanizer')
if options.numfiles:
    OutFolder += '_n' + str(options.numfiles)
if options.disectorthickness:
    OutFolder += '_d%sum' % options.numfiles
OutFolder += '_pixelsize%0.fum' % options.pixelsize
OutFolder += '_scalebar%sum' % options.scalebar
os.makedirs(OutFolder,  exist_ok=True)

print('Looking for *.png files in %s' % os.path.join(options.samplefolder, 'rec'))
ReconstructionNames = glob.glob(os.path.join(options.samplefolder, 'rec', '*rec*.png'))
print('We found %s reconstructions.' % len(ReconstructionNames))
print('We will select %s images from these and rewrite them to %s' % (options.numfiles, OutFolder))

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
            'Please reduce the "-r" option to something below %s px' % longest_side)
    options.resize /= float(longest_side)

# Set up logging
logging.basicConfig(filename=os.path.join(OutFolder, 'STEPanizerizer.log'),
                    level=logging.INFO, format='%(message)s')
logging.info('STEPanizerizer (version %s) has been run with this command line\n--\n%s\n--' % (get_git_hash(),
                                                                                              ' '.join(sys.argv)))
logging.info('Conversion started at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
logging.info(80 * '-')
logging.info('Approximately %s images are written fom %s to %s' % (options.numfiles,
                                                                   os.path.abspath(os.path.join(options.samplefolder, 'rec')),
                                                                   os.path.abspath(OutFolder)))

# Calculate the pixel length of the scale bar, based on the given um
ScaleBarPixels = int(round(options.scalebar / float(options.pixelsize)))

# Set up resize value, if requested
if options.resize:
    logging.info('The longest side of the image is being resized from %s px to %0.2f%% of it: %0.0f px' % (longest_side,
                                                                                                           (100 * options.resize),
                                                                                                           longest_side * options.resize))
    print('A scale bar of %s um will thus be about %0.0f px long.' % (options.scalebar, ScaleBarPixels * options.resize))
else:
    print('A scale bar of %s um will thus be about %s px long.' % (options.scalebar, ScaleBarPixels))

# Log some more
logging.info('The scale bar at the bottom right of the images corresponds to %s um.' % options.scalebar)
logging.info('We use uniform random sampling, so the start and end slice will be different each time the script is run!')
logging.info(80 * '-')

# Get the common prefix of all the reconstructions.
# Strip trailing zeroes and 'rec'.
# And also strip the InstaRecon suffix if we have that.
# The resulting string is the prefix of the STEPanizer files.
CommonPrefix = os.path.split(os.path.abspath(os.path.commonprefix(ReconstructionNames)))[1].rstrip('0').strip('_rec').strip('_IR')

# Calculate which files we need to read, based on the total and the requested file number
if options.numfiles:
    StepWidth = int(round(len(ReconstructionNames) / float(options.numfiles)))
if options.disectorthickness:
    # One step = options.pixelsize ->
    StepWidth = int(round(options.disectorthickness / options.pixelsize))

print(StepWidth)
exit()



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

# TODO: Not only load N slices throughout dataset, but load slices M um apart i.e. slicedistance
# TODO: Implement Disector

logging.info(80 * '-')
logging.info('Conversion finished at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
