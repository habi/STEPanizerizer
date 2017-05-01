# -*- coding: utf-8 -*-

"""
Script to prepare a (Bruker) tomographic dataset for stereological analysis with the [STEPanizer](http://stepanizer.com/).
It implements uniform random sampling through the files and draws a scale bar if requested.
The user either selects a number of files to export (-n) or requests a slice distance (-s).
Disector thickness is not implemented yet...
"""

# Import modules
import datetime
import glob
import logging
import matplotlib.pyplot as plt
import numpy
import os
import random
import scipy.misc
import sys
from optparse import OptionParser

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
    Get the current git hash of the script, which is written to the log file.
    Based on http://stackoverflow.com/a/14989911/323100
    """
    import subprocess
    return(subprocess.check_output(["git", "describe", "--always"]).strip().decode('utf-8'))

# Setup the options to run the script and to ask from the user
parser = OptionParser()
usage = 'usage: %prog [options] arg'
parser.add_option('-f', '--folder', dest='samplefolder', type='str', metavar='SampleA',
                  help='Sample folder. We will look for the "rec" folder inside.')
parser.add_option('-n', '--numberoffiles', dest='numfiles', type=int, metavar='18',
                  help='Number of slices to convert for STEPanizer. The script will select them equally spaced throughout the whole set of images. (No default)')
parser.add_option('-s', '--slicedistance', dest='slicedistance', type=float, metavar='26.7',
                  help='Slice distance in micrometers. (No default)')
parser.add_option('-p', '--pixelsize', dest='pixelsize', type='float', metavar=11,
                  help='Pixel/Voxel size of the scan. (Default=Read from scan log file)')
parser.add_option('-d', '--disectorthickness', dest='disectorthickness', type='float', metavar=5.3,
                  help='Disector thickness in um. (No default)')
parser.add_option('-b', '--ScaleBar', dest='scalebar', type=int, default=1000, metavar='256',
                  help='Draw a scale bar with the given length (in micrometer) in the bottom right of the image. (Default=%default um)')
parser.add_option('-r', '--Resize', dest='resize', type=int, metavar='1600',
                  help='Resize the input image to this side length (for the *longest* axis). (No Default)')
parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true', metavar=1,
                  help='Be chatty/informative. (Default=Be quiet)')
(options, args) = parser.parse_args()

# Sanity check for options
# Show the help if necessary parameters are missing
if not options.samplefolder:
    parser.error('You need to give me a sample folder as input (with the "-f" option).')
# Check if the folder actually exists
if not os.path.isdir(options.samplefolder):
    print('Please give me a correct (i.e. existing) folder as input')
if not options.numfiles and not options.slicedistance:
    parser.error('Yo need to give me either a number of files I should export (-n) or a slice distance (-s) between the exported files.')
# 'Slice distance' and 'number of files' are mutually exclusive, the user has to choose one or the other.
if options.numfiles and options.slicedistance:
    parser.error('The options "Number of files (-n) and "Slice Distance (-s) are mutually exclusive.\nChoose one or the other, please.\n')
# The 'disector thickness' in not implemented yet'
if options.disectorthickness:
    parser.error('Disector functionality not implemented yet, sorry!\nPlease remove the -d option...')

# RecFolder
# TODO: Make it work if there is more than one 'rec' folder
options.recfolder = 'rec_HU'

# Get the (isotropic) pixel size of the scan.
# We need it for the scale bar and - if requested - disector thickness.
if not options.pixelsize:
    options.pixelsize = get_pixelsize(
        glob.glob(os.path.join(options.samplefolder, options.recfolder, '*.log'))[0])
print('The scan was done with a voxel size of %0.2f um.' % options.pixelsize)

# Make output directory, named with relevant parameters
OutFolder = os.path.join(options.samplefolder, 'STEPanizer')
OutFolder += '_%s' % options.recfolder
if options.numfiles:
    OutFolder += '_numfls%s' % options.numfiles
if options.slicedistance:
    OutFolder += '_slcdst%0.fum' % options.slicedistance
OutFolder += '_pxsz%0.fum' % options.pixelsize
OutFolder += '_sclbr%sum' % options.scalebar
try:
    os.makedirs(OutFolder)
except FileExistsError:
    print('\n\nThe output folder %s already exists' % OutFolder)
    print('We try to not overwrite anything...\n')
    sys.exit('Please delete the folder or choose other parameters')

print('Looking for *.png files in %s' % os.path.join(options.samplefolder, options.recfolder))
ReconstructionNames = sorted(glob.glob(os.path.join(options.samplefolder, options.recfolder, '*rec*.png')))
print('We found %s reconstructions.' % len(ReconstructionNames))
if options.numfiles:
    print('We will select %s images from these and rewrite them to %s' % (options.numfiles,
                                                                          OutFolder))
if options.slicedistance:
    print('We will select slices spaced by %0.2f um and rewrite them to %s' % (options.slicedistance,
                                                                               OutFolder))

# Get image size (which we need for resizing), obviously only if requested
# We then use this to calculate a resize fraction. This float value then takes
# care of non-square image resizing according to https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imresize.html
ImageShape = numpy.shape(scipy.misc.imread(random.choice(ReconstructionNames),
                                           flatten=True))
if options.resize:
    # Read a random image from the dataset, grab its side lengths and save the maximum (for non-square images)
    longest_side = numpy.max(ImageShape)
    if options.resize > longest_side:
        print('\nWe will not upscale images (from %s px to %s px)' % (longest_side,
                                                                      options.resize))
        parser.error('Please reduce the "-r" option to something below %s px' % longest_side)
    options.resize /= float(longest_side)

# Set up logging
logging.basicConfig(filename=os.path.join(OutFolder, 'STEPanizerizer.log'),
                    level=logging.INFO, format='%(message)s')
logging.info('STEPanizerizer (version %s) has been started at %s as below\n--\n%s\n--' % (get_git_hash(),
                                                                                          datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"),
                                                                                          ' '.join(sys.argv)))
logging.info(80 * '-')

# Scale bar and resizing
# Calculate the pixel length of the scale bar, based on the given um
ScaleBarPixels = int(round(options.scalebar / float(options.pixelsize)))
# Set up resize value, if requested
print('The original images have a size of %sx%s px at %0.2f um per px' % (ImageShape[0],
                                                                          ImageShape[1],
                                                                          options.pixelsize))
if options.resize:
    print('The longest side of the image is being resized to %0.2f%% of %s px: %0.0f px' % ((100 * options.resize),
                                                                                            longest_side,
                                                                                            longest_side * options.resize))
    logging.info('The longest side of the image is being resized to %0.2f%% of %s: %0.0f px' % ((100 * options.resize),
                                                                                                longest_side,
                                                                                                longest_side * options.resize))
    print('A scale bar of %s um will be about %0.0f px long.' % (options.scalebar,
                                                                 ScaleBarPixels * options.resize))
else:
    print('A scale bar of %s um will be about %s px long.' % (options.scalebar,
                                                              ScaleBarPixels))

# Log some more
logging.info('The scale bar at the bottom right of the images corresponds to %s um.' % options.scalebar)

# Get the common prefix of all the reconstructions.
# Strip trailing zeroes and 'rec'.
# And also strip the InstaRecon suffix if we have that.
# The resulting string is the prefix of the STEPanizer files.
CommonPrefix = os.path.split(os.path.abspath(os.path.commonprefix(ReconstructionNames)))[1].rstrip('0').strip('_rec').strip('_IR')

# Calculate which files we need to read, based on the requested file number (-n) or slice distance (-s)
# We use numpy.floor to get a bit more files than necessary if rounding kicks in
if options.numfiles:
    # Load every nth file
    StepWidth = int(numpy.floor(len(ReconstructionNames) / float(options.numfiles)))
if options.slicedistance:
    # One step = Requested slice distance divided by pixel size
    StepWidth = int(numpy.floor(options.slicedistance / options.pixelsize))

# Slice distance
if options.numfiles:
    print('%s requested files correspond to every %sth file of %s total files' % (options.numfiles,
                                                                                  StepWidth,
                                                                                  len(ReconstructionNames)))
    logging.info('As requested, %s images are written fom %s to %s' % (options.numfiles,
                                                                       os.path.abspath(os.path.join(options.samplefolder, options.recfolder)),
                                                                       os.path.abspath(OutFolder)))
if options.slicedistance:
    print('A requested slice distance of %s correspond to every %sth file of %s total files' % (options.slicedistance,
                                                                                                StepWidth,
                                                                                                len(ReconstructionNames)))
    logging.info('As requested, slices spaced by %s um are written fom %s to %s' % (options.slicedistance,
                                                                                    os.path.abspath(os.path.join(options.samplefolder, options.recfolder)),
                                                                                    os.path.abspath(OutFolder)))
print('The resulting slice distance in the exported files is (rounded) to %0.2f um' % (StepWidth * options.pixelsize))
logging.info('The resulting slice distance in the exported files is (rounded) %0.2f um' % (StepWidth * options.pixelsize))
logging.info(80 * '-')
logging.info('We use uniform random sampling, so the start and end slice will be different each time we run the script!')

# Actually read the files now.
# They are converted from *.png to (scale-barred and resized) *.jpg with 'no leading zero' numbering, as the STEPanizer likes.
# Start at a random interval between [0,StepWidth), this takes care of Systematic Uniform Random Sampling, where we have equal distance between slices but a different start (see: http://www.stereology.info/sampling/)
if options.verbose:
    plt.figure()
    plt.ion()
for c, i in enumerate(ReconstructionNames[numpy.random.randint(StepWidth)::StepWidth]):
    rec = scipy.misc.imread(i, flatten=True)
    OutputName = os.path.join(OutFolder, '%s_%s.jpg' % (CommonPrefix, c + 1))
    Output = '%2s/%s: %s --> %s' % (c + 1, len(ReconstructionNames[::StepWidth]),
                                    os.path.split(i)[1],
                                    os.path.split(OutputName)[1])
    print(Output)
    if options.scalebar:
        # Add white scalebar with the given length (and 1/10 of it as height) at the bottom right of the image
        fromborder = 50
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

# TODO: Implement Disector

logging.info(80 * '-')
logging.info('Conversion finished at %s' % datetime.datetime.now().strftime("%H:%M:%S on %d.%m.%Y"))
