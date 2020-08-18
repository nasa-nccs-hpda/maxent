#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import csv
import fileinput
import os
import pickle
import shutil
import sys

from core.model.GeospatialImageFile import GeospatialImageFile
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class MaxEntRequest
# -----------------------------------------------------------------------------
class MaxEntRequest(object):

    MAX_ENT_JAR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'libraries',
                               'maxent.jar')

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, observationFile, listOfImages, outputDirectory):

        if not os.path.exists(outputDirectory):

            raise RuntimeError('Output directory, ' +
                               str(outputDirectory) +
                               ' does not exist.')

        # Ensure all the images are in the same SRS.
        self._images = listOfImages
        self._imageSRS = self._images[0].srs()

        for image in self._images:

            if not self._imageSRS.IsSame(image.srs()):

                raise RuntimeError('Image ' +
                                   image.fileName() +
                                   ' is not in the same SRS as the others.')

        self._imagesToProcess = self._images
        self._outputDirectory = outputDirectory

        self._observationFile = observationFile
        self._observationFile.transformTo(self._imageSRS)
        self._maxEntSpeciesFile = self._formatObservations()

        # Create a directory for the ASC files.
        self._ascDir = os.path.join(self._outputDirectory, 'asc')

        try:
            os.mkdir(self._ascDir)

        except OSError:

            # Do not complain, if the directory exists.
            pass

    # -------------------------------------------------------------------------
    # _formatObservations
    # -------------------------------------------------------------------------
    def _formatObservations(self):

        path, name = os.path.split(self._observationFile.fileName())
        samplesFile = os.path.join(self._outputDirectory, name)

        meWriter = csv.writer(open(samplesFile, 'w'), delimiter=',')
        meWriter.writerow(['species', 'x', 'y'])

        for i in range(self._observationFile.numObservations()):

            obs = self._observationFile.observation(i)

            # Skip absence points.
            if obs[1] > 0:

                speciesNoBlank = self._observationFile. \
                                 species(). \
                                 replace(' ', '_')

                meWriter.writerow([speciesNoBlank,
                                   obs[0].GetX(),
                                   obs[0].GetY()])

        return samplesFile

    # -------------------------------------------------------------------------
    # prepareImage
    #
    # This method prepares one image for use with maxent.jar.  Clients can use
    # this to control the preparation of a batch of images outside a single
    # MaxEntRequest.  MmxRequest will use this to prepare all images once,
    # instead of preparing a new set for each trial.
    # -------------------------------------------------------------------------
    @staticmethod
    def prepareImage(image, srs, envelope, ascDir):

        # ---
        # First, to preserve the original files, copy the input file to the
        # output directory.
        # ---
        baseName = os.path.basename(image.fileName())
        nameNoExtension = os.path.splitext(baseName)[0]
        ascImagePath = os.path.join(ascDir, nameNoExtension + '.asc')

        if not os.path.exists(ascImagePath):

            copyPath = os.path.join(ascDir, baseName)
            print ('Processing ' + copyPath)
            shutil.copy(image.fileName(), copyPath)
            imageCopy = GeospatialImageFile(copyPath, srs)
            imageCopy.clipReproject(envelope)

            squareScale = imageCopy.getSquareScale()
            imageCopy.resample(squareScale, squareScale)

            # Convert to ASCII Grid.
            cmd = 'gdal_translate -ot Float32 -of AAIGrid -a_nodata -9999.0' +\
                  ' "' + imageCopy.fileName() + '"' + \
                  ' "' + ascImagePath + '"'

            SystemCommand(cmd, None, True)

            # Fix NaNs.
            for line in fileinput.FileInput(ascImagePath, inplace=1):

                line = line.replace('nan', '-9999')
                sys.stdout.write(line)

        else:
            print(baseName, 'was previously prepared.')

        return ascImagePath

    # -------------------------------------------------------------------------
    # prepareImages
    # -------------------------------------------------------------------------
    def prepareImages(self):

        ascGifs = []
        numLeft = len(self._imagesToProcess)

        for gif in self._imagesToProcess:

            ascGifs.append(MaxEntRequest.prepareImage(
                gif,
                self._imageSRS,
                self._observationFile.envelope(),
                self._ascDir))

            numLeft -= 1
            print(numLeft, ' images remaining to process.')

        return ascGifs

    # -------------------------------------------------------------------------
    # run
    # -------------------------------------------------------------------------
    def run(self, jarFile=MAX_ENT_JAR):

        self.prepareImages()
        self.runMaxEntJar(jarFile)

    # -------------------------------------------------------------------------
    # runMaxEntJar
    # -------------------------------------------------------------------------
    def runMaxEntJar(self, jarFile=MAX_ENT_JAR):

        print ('Running MaxEnt.')

        # Invoke maxent.jar.
        baseCmd = 'java -Xmx1024m -jar ' + \
                  jarFile + \
                  ' visible=false autorun -P -J writeplotdata ' + \
                  '"applythresholdrule=Equal training sensitivity and ' + \
                  'specificity" removeduplicates=false '

        cmd = baseCmd + \
            '-s "' + self._maxEntSpeciesFile + '" ' + \
            '-e "' + self._ascDir + '" ' + \
            '-o "' + self._outputDirectory + '"'

        SystemCommand(cmd, None, True)
