#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob
import sys

from osgeo.osr import SpatialReference

from core.model.GeospatialImageFile import GeospatialImageFile

from maxent.model.MaxEntRequest import MaxEntRequest
from maxent.model.MaxEntRequestCelery import MaxEntRequestCelery
from maxent.model.ObservationFile import ObservationFile


# -----------------------------------------------------------------------------
# main
#
# cd innovation-lab
# export PYTHONPATH=`pwd`
# view/MerraRequestCLV.py -e -125 50 -66 24 --epsg 4326 --start_date 2013-02-03 --end_date 2013-03-12 -c m2t1nxslv --vars QV2M TS --op avg -o /att/nobackup/rlgill/testMaxEnt/merra
# view/MaxEntRequestCommandLineView.py -e 4326 -f /att/nobackup/rlgill/maxEntData/ebd_Cassins_1989.csv -s "Cassin's Sparrow" -i /att/nobackup/rlgill/testMaxEnt/merra -o /att/nobackup/rlgill/testMaxEnt
#
# Celery
# redis-server&
# celery -A maxent.model.CeleryConfiguration worker --loglevel=info&
# view/MaxEntRequestCommandLineView.py -e 4326 -f /att/nobackup/rlgill/maxEntData/ebd_Cassins_1989.csv -s "Cassin's Sparrow" -i /att/nobackup/rlgill/testMaxEnt/merra -o /att/nobackup/rlgill/testMaxEnt --celery
# -----------------------------------------------------------------------------
def main():

    # Process command-line args.
    desc = 'This application runs Maximum Entropy.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--celery',
                        action='store_true',
                        help='Use Celery for distributed processing.')

    parser.add_argument('-e',
                        required=True,
                        type=int,
                        help='Integer EPSG code representing the spatial ' +
                             'reference system of the input images.')

    parser.add_argument('-f',
                        required=True,
                        help='Path to observation file')

    parser.add_argument('-i',
                        default='.',
                        help='Path to directory of image files')

    parser.add_argument('-o',
                        default='.',
                        help='Path to output directory')

    parser.add_argument('-s',
                        required=True,
                        help='Name of species in observation file')

    args = parser.parse_args()

    srs = SpatialReference()
    srs.ImportFromEPSG(args.e)

    imageFiles = glob.glob(args.i + '/*.nc')
    geoImages = [GeospatialImageFile(i, srs) for i in imageFiles]
    observationFile = ObservationFile(args.f, args.s)

    if args.celery:

        maxEntReq = MaxEntRequestCelery(observationFile, geoImages, args.o)

    else:
        maxEntReq = MaxEntRequest(observationFile, geoImages, args.o)

    maxEntReq.run()

# ------------------------------------------------------------------------------
# Invoke the main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
