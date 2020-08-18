# -*- coding: utf-8 -*-

import csv
import os
import tempfile
import unittest

from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope

from maxent.model.ObservationFile import ObservationFile


# -----------------------------------------------------------------------------
# class ObservationFileTestCase
#
# python -m unittest discover model/tests/
# python -m unittest model.tests.test_ObservationFile
# -----------------------------------------------------------------------------
class ObservationFileTestCase(unittest.TestCase):

    _species = 'Cheat Grass'
    _testObsFile = None

    # -------------------------------------------------------------------------
    # setUpClass
    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        ObservationFileTestCase._testObsFile = \
            tempfile.mkstemp(suffix='.csv')[1]

        print('_testObsFile: ', ObservationFileTestCase._testObsFile)

        with open(ObservationFileTestCase._testObsFile, 'w') as csvFile:

            fields = ['x', 'y', 'pres/abs', 'epsg:32612']
            writer = csv.writer(csvFile, fields)
            writer.writerow(fields)
            writer.writerow((374187, 4124593, 1))
            writer.writerow((393543, 4100640, 0))
            writer.writerow((395099, 4130094, 0))
            writer.writerow((486130, 4202663, 1))
            writer.writerow((501598, 4142175, 0))

    # -------------------------------------------------------------------------
    # tearDownClass
    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        os.remove(ObservationFileTestCase._testObsFile)

    # -------------------------------------------------------------------------
    # testEnvelope
    # -------------------------------------------------------------------------
    def testEnvelope(self):

        testEnv = Envelope()
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        testEnv.addPoint(374187, 4202663, 0, srs)
        testEnv.addPoint(501598, 4100640, 0, srs)

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        self.assertTrue(testEnv.Equals(obs.envelope()))

    # -------------------------------------------------------------------------
    # testGetSetState
    # -------------------------------------------------------------------------
    def testGetSetState(self):

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        obsDump = obs.__getstate__()

        # Create a temporary file in which to set the state.
        obs2FileName = tempfile.mkstemp(suffix='.csv')[1]
        obs2 = ObservationFile(obs2FileName, 'Snow Dog')
        obs2.__setstate__(obsDump)

        self.assertEqual(obs.fileName(), obs2.fileName())
        self.assertEqual(obs.species(), obs2.species())
        self.assertEqual(obs.srs().ExportToProj4(), obs2.srs().ExportToProj4())
        self.assertTrue(obs.envelope().Equals(obs2.envelope()))
        self.assertEqual(obs.numObservations(), obs2.numObservations())

        for observation in obs._observations:

            found = False

            for observation2 in obs2._observations:

                if observation[0].Equals(observation2[0]) and \
                     observation[1] == observation2[1]:

                    found = True
                    break

            self.assertTrue(found)

    # -------------------------------------------------------------------------
    # testNotA_CSV_File
    # -------------------------------------------------------------------------
    def testNotA_CSV_File(self):

        with self.assertRaises(RuntimeError):

            ObservationFile('Common/tests/test_BaseFile.py',
                            ObservationFileTestCase._species)

    # -------------------------------------------------------------------------
    # testInvalidFile
    # -------------------------------------------------------------------------
    def testInvalidFile(self):

        # Create a file with multiple SRSs.
        invalidFile = tempfile.mkstemp(suffix='.csv')[1]
        print('invalidFile: ', invalidFile)

        with open(invalidFile, 'w') as csvFile:

            fields = ['x', 'y', 'pres/abs', 'epsg']
            writer = csv.writer(csvFile, fields)
            writer.writerow(fields)
            writer.writerow((374187, 4124593, 1))

        with self.assertRaisesRegex(RuntimeError, 'must contain a colon'):
            ObservationFile(invalidFile, ObservationFileTestCase._species)

        os.remove(invalidFile)

    # -------------------------------------------------------------------------
    # testNoSpecies
    # -------------------------------------------------------------------------
    def testNoSpecies(self):

        with self.assertRaises(TypeError):
            ObservationFile(ObservationFileTestCase._testObsFile)

    # -------------------------------------------------------------------------
    # testSpecies
    # -------------------------------------------------------------------------
    def testSpecies(self):

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        self.assertEqual(obs.species(), ObservationFileTestCase._species)

    # -------------------------------------------------------------------------
    # testSRS
    # -------------------------------------------------------------------------
    def testSRS(self):

        testSRS = SpatialReference()
        testSRS.ImportFromEPSG(32612)

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        self.assertTrue(obs.srs().IsSame(testSRS))

    # -------------------------------------------------------------------------
    # testTransformTo
    # -------------------------------------------------------------------------
    def testTransformTo(self):

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        srs = obs.srs()
        newSRS = SpatialReference()
        newSRS.ImportFromEPSG(4326)

        obs1 = obs.observation(0)
        obs.transformTo(newSRS)

        self.assertFalse(srs.IsSame(obs.srs()))

        self.assertAlmostEqual(obs.observation(0)[0].GetX(),
                               -112.41880490511376,
                               places=9)

        self.assertAlmostEqual(obs.observation(0)[0].GetY(),
                               37.259406381055626,
                               places=7)

    # -------------------------------------------------------------------------
    # testValidFile
    # -------------------------------------------------------------------------
    def testValidFile(self):

        obs = ObservationFile(ObservationFileTestCase._testObsFile,
                              ObservationFileTestCase._species)

        self.assertEqual(obs.numObservations(), 5)
        self.assertEqual(obs.observation(0)[0].GetX(), 374187)
        self.assertEqual(obs.observation(1)[1], False)
        self.assertEqual(obs.observation(2)[0].GetY(), 4130094)
        self.assertEqual(obs.observation(3)[1], True)

        # Test a spatial reference.
        crs = SpatialReference()
        crs.ImportFromEPSG(32612)

        self.assertTrue(obs.observation(4)[0].
                        GetSpatialReference().
                        IsSame(crs))
