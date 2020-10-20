#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob
import os
import sys

from maxent.model.AICc import AICc


# -----------------------------------------------------------------------------
# main
#
# Cd to the directory containing the repositories
# export PYTHONPATH=`pwd`:`pwd`/core:`pwd`/maxent
# maxent/view/AICc_CLV.py -a /att/nobackup/jschnase/MMX/js-runs/output-maxent-baseline-raw/CassinsSparrow_0.asc -f /att/nobackup/jschnase/MMX/js-runs/input/gbif/CSp_2016_016km_thin.csv -i /att/nobackup/jschnase/MMX/js-runs/input/bioclim/ -l /att/nobackup/jschnase/MMX/js-runs/output-maxent-baseline-raw/CassinsSparrow_0.lambdas
# -----------------------------------------------------------------------------
def main():

    # Define command-line args.
    desc = 'This application computes AICc, given a MaxEnt output directory.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-a',
                          help='Path to ASC image file')

    parser.add_argument('-f',
                          help='Path to observation file')

    parser.add_argument('-i',
                          help='Path to ASC image directory')

    parser.add_argument('-l',
                          help='Path to lambda file')

    args = parser.parse_args()

    # Process the arguments.
    ascFile = args.a
    ascImageDir = args.i
    lamFile = args.l
    obsFile = args.f
        
    print('ASC file: ', ascFile)
    print('Lambda file: ', lamFile)
    print('Observation file: ', obsFile)

    aicc = AICc()
    aicc.setAscFile(ascFile)
    aicc.setAscImageDir(ascImageDir)
    aicc.setLambdaFile(lamFile)
    aicc.setObsFile(obsFile)
    aiccValue = aicc.run()
    print('AICc: ', aiccValue)
    
# ------------------------------------------------------------------------------
# Invoke the main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
