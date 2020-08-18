# -*- coding: utf-8 -*-

import csv

from osgeo import ogr
from osgeo.osr import SpatialReference

from core.model.BaseFile import BaseFile
from core.model.Envelope import Envelope


# -----------------------------------------------------------------------------
# class ObservationFile
#
# TIP: This class uses minimal abstractions.  The purest implementation would
# include an Observation class, a class representing a collection of
# observations with methods like envelope, and some sort of serialization
# class.  For now, keep it simple.  More decomposition might be helpful later,
# especially if we need to add or remove observations.  Things like the
# envelope and disk file would need to be updated.
#
# TIP: This class uses a Point abstraction implemented with GDAL.
# -----------------------------------------------------------------------------
class ObservationFile(BaseFile):

    FILE_KEY = 'PathToFile'
    SPECIES_KEY = 'Species'

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, pathToFile, species):

        if not species:
            raise RuntimeError('A species must be specified.')

        # Initialize the base class.
        super(ObservationFile, self).__init__(pathToFile)

        # Initialize the data members.
        self._species = species
        self._srs = None
        self._envelope = None
        self._observations = []

        self._parse()

    # -------------------------------------------------------------------------
    # envelope
    # -------------------------------------------------------------------------
    def envelope(self):

        if not self._envelope:

            self._envelope = Envelope()

            for obs in self._observations:
                self._envelope.addOgrPoint(obs[0].Clone())

        return self._envelope

    # -------------------------------------------------------------------------
    # numObservations
    # -------------------------------------------------------------------------
    def numObservations(self):

        return len(self._observations)

    # -------------------------------------------------------------------------
    # observation
    # -------------------------------------------------------------------------
    def observation(self, index):

        if index >= self.numObservations():
            raise IndexError

        return self._observations[index]

    # -------------------------------------------------------------------------
    # _parse
    #
    # This parser requires a header and understands the following formats:
    # - x,y,response:binary,epsg:nnnnn
    # -------------------------------------------------------------------------
    def _parse(self):

        with open(self._filePath) as csvFile:

            first = True
            fdReader = csv.reader(csvFile, delimiter=',')

            for row in fdReader:

                if first:

                    first = False

                    # If the first element is a float, there is no header row.
                    try:
                        float(row[0])

                        raise RuntimeError('The observation file, ' +
                                           str(self.fileName()) +
                                           ' must have a header.')

                    except ValueError:

                        if ':' not in row[3]:

                            raise RuntimeError('EPSG in header field ' +
                                               'must contain a colon ' +
                                               'then integer EPSG code.')

                        epsg = row[3].split(':')[1]
                        self._srs = SpatialReference()
                        self._srs.ImportFromEPSG(int(epsg))

                else:

                    # Parse a row.
                    ogrPt = ogr.Geometry(ogr.wkbPoint)
                    ogrPt.AddPoint(float(row[0]), float(row[1]), 0)
                    ogrPt.AssignSpatialReference(self._srs)
                    # self._envelope.addOgrPoint(ogrPt)
                    self._observations.append((ogrPt, float(row[2])))

    # -------------------------------------------------------------------------
    # species
    # -------------------------------------------------------------------------
    def species(self):

        return self._species

    # -------------------------------------------------------------------------
    # srs
    # -------------------------------------------------------------------------
    def srs(self):

        return self._srs

    # -------------------------------------------------------------------------
    # transformTo
    # -------------------------------------------------------------------------
    def transformTo(self, newSRS):

        if newSRS.IsSame(self._srs):
            return

        self._envelope = None
        self._srs = newSRS

        for obs in self._observations:
            obs[0].TransformTo(newSRS)

    # -------------------------------------------------------------------------
    # __getstate__
    # -------------------------------------------------------------------------
    def __getstate__(self):

        state = {ObservationFile.FILE_KEY: self._filePath,
                 ObservationFile.SPECIES_KEY: self._species}

        return state

    # -------------------------------------------------------------------------
    # __setstate__
    #
    # e2 = pickle.loads(pickle.dumps(env))
    # -------------------------------------------------------------------------
    def __setstate__(self, state):

        self.__init__(state[ObservationFile.FILE_KEY],
                      state[ObservationFile.SPECIES_KEY])
