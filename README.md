# ESTalosPull #

This repository contains code for extracting and analysing Talos results.  There are two python scripts (espull.py and simulate.py) along with some R code for producing visualizations.  Also included are some samples of how to use all three pieces together.  This code supports the creation of all the conclusions and visualizations in: https://wiki.mozilla.org/Metrics/Talos_Investigation.

## espull.py ##

This script will query and ElasticSearch instance to extract talos test information.  It requires the pyes library available: http://pypi/python.org/pypi/pyes.  For usage information run:

'python espull.py --help'

## simulate.py ##

This script will take a set of data and generate random samples from that population.  Various sample sizes are generated and statistical tests are applied to each sample.  The result is information about the performance of a regime with those sample sizes. This package uses the statlib library: http://code.google.com/p/python-statlib/.  For usage information run:

'python simulate.py --help'

## Samples ##

Also included in this repository are some samples, which are found in the samples directory.

* retrive_data.sh - will pull tdhtml and tsvg test data for the first two weeks of November 2011 and data from the pine branch experiment.
* generate_plots.sh - will generate three pdf files with graphs about the talos data.
* simulation/run_simulation.sh - will generate samples from the pine branch and run a single simulation on each component.
* simulation/run_calibration.sh - will generate samples from the pine branch and calibrate each component using 20 simulations on each.


