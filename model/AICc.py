
import csv
import glob
import math
import os
import struct

import numpy as np

from osgeo import gdalconst
from osgeo.osr import SpatialReference

from core.model.BaseFile import BaseFile
from core.model.Chunker import Chunker
from core.model.GeospatialImageFile import GeospatialImageFile


# -----------------------------------------------------------------------------
# class AICc
# -----------------------------------------------------------------------------
class AICc(object):

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self):
        
        self._ascFile = None
        self._ascImageDir = None
        self._lambdaFile = None
        self._obsFile = None
        
    # -------------------------------------------------------------------------
    # likelihood
    # 
    # http://finzi.psych.upenn.edu/library/ENMeval/html/calc.aicc.html
    # L = sum(log(vals / total))
    # Where vals is a vector of Maxent raw values at occurrence localities and
    # total is the sum of Maxent raw values across the entire study area. 
    # -------------------------------------------------------------------------
    def _likelihood(self, obs):
        
        # Create a vector of output values at the observation points.  The
        vals = []
        occInside = 0
         
        for ob in obs:
            
            #                                     lon    lat
            imagePt = self._ascFile.groundToImage(ob[0], ob[1])
            
            # ---
            # MaxEnt trims occurences near the boundary of the input images.
            # These points will not fall within the output .asc file.
            # ---
            binVal = self._ascFile._getDataset().ReadRaster(
                                                  imagePt[0],  # x
                                                  imagePt[1],  # y
                                                  1,
                                                  1,
                                                  None,
                                                  None,
                                                  gdalconst.GDT_Float32)

            if binVal:

                vals.append(struct.unpack('f', binVal)[0])
                occInside += 1
        
        # ---
        # Compute total by chunking through the image row by row, accumulating
        # the sum of each value in the row.
        # ---
        total = 0.0
        chunker = Chunker(self._ascFile.fileName())
        chunker.setChunkAsRow()
        noDataValue = self._ascFile._dataset.GetRasterBand(1).GetNoDataValue()

        while not chunker.isComplete():
            
            loc, rowNp = chunker.getChunk()
            total += np.sum(rowNp[rowNp != noDataValue])
            
        if total <= 0:
            
            msg = 'Cannot compute log likelihood because the sum of all ' + \
                  'values in the MaxEnt output image is less than or ' + \
                  'equal to zero.'
                  
            raise RuntimeError(msg)
            
        # Compute the likelihood.
        logL = 0.0
        
        for val in vals:
            logL += math.log(val / total)

        return logL, occInside
        
    # -------------------------------------------------------------------------
    # parseObservations
    # -------------------------------------------------------------------------
    def _parseObservations(self):
        
        obs = []
        
        with open(self._obsFile) as csvFile:

            first = True
            fdReader = csv.reader(csvFile, delimiter=',')

            for row in fdReader:

                if first:

                    first = False
                    
                else:
                    obs.append([float(row[1]), float(row[2])])

        return obs
        
    # -------------------------------------------------------------------------
    # run
    # 
    # (2 * K - 2 * logLikelihood) + (2 * K) * (K+1) / (n - K - 1)
    # K = number of parameters in the model (i.e., number of non-zero 
    # parameters in Maxent lambda file)
    # n = number of occurrence localities
    # -------------------------------------------------------------------------
    def run(self):
        
        # ---
        # Parse the MaxEnt observation file.  We are relying on MaxEnt's,
        # instead of the IL's class format, to make it easier to run this AICC
        # application.  Instead of providing the original observation file,
        # user's need only point to MaxEnt's output directory to run this.
        # ---
        obs = self._parseObservations()
        
        # Log likelihood and n
        logLikelihood, n = self._likelihood(obs)
        
        # K
        k = 0
        
        linesToSkip = ['linearPredictorNormalizer',
                       'densityNormalizer',
                       'numBackgroundPoints',
                       'entropy']
                       
        with open(self._lamFile) as csvFile:

            lambdaReader = csv.reader(csvFile, delimiter=',')

            for row in lambdaReader:
            
                if row[0] not in linesToSkip and row[1] != 0:
                    k += 1
                
        # aicc
        aicc = (2 * k - 2 * logLikelihood) + (2 * k) * (k+1) / (n - k - 1)
        
        return aicc
    
    # -------------------------------------------------------------------------
    # setAscFile
    # -------------------------------------------------------------------------
    def setAscFile(self, ascFile):
        
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        self._ascFile = GeospatialImageFile(ascFile, srs)
        
    # -------------------------------------------------------------------------
    # setAscImageDir
    # -------------------------------------------------------------------------
    def setAscImageDir(self, ascImageDir):
        
        if not (os.path.exists(ascImageDir) and os.path.isdir(ascImageDir)):
            raise RuntimeError(ascImageDir + ' is an invalid directory.')
        
        self._ascImageDir = ascImageDir

    # -------------------------------------------------------------------------
    # setLambdaFile
    # -------------------------------------------------------------------------
    def setLambdaFile(self, lamFile):
        
        self._lamFile = BaseFile(lamFile).fileName()
        
    # -------------------------------------------------------------------------
    # setObsFile
    # -------------------------------------------------------------------------
    def setObsFile(self, obsFile):
        
        # ---
        # Construct as a BaseFile because we only need to validate it.  We
        # don't need it as an observation file.
        # ---
        self._obsFile = BaseFile(obsFile).fileName()
        
        