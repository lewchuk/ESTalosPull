# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is espull, a log extractor for talos logs stored in ES.
#
# The Initial Developer of the Original Code is
# Stephen Lewchuk (slewchuk@mozilla.com).
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import argparse
import random
import os.path
from datetime import datetime

from statlib import stats

from formatter import *
from analyser import get_median, get_average

class Simulation(object):
  """ This class runs a sample size simulation based on a set of observations

      The simulation is run using the run_simulation method specifying the number of repetitions.

      Parameters:
        source_data -- a list of observed values to sample from
        sample_size -- the sample size to use for the simulation
        threshold -- the magnitude of change to try and detect

      Output:
        Once the simulation is complete three pieces of data is produced:
          rev_results - the mean and median of each sample taken
          conf_results - the a set of probabilities of the sample compared to different values
          simulation_result - the ratios of detection for this sample size
  """

  def __init__(self, source_data, sample_size, test_name, threshold=0.01):
    self.data = source_data
    self.popmean = stats.mean(source_data)
    self.sample_size = sample_size
    self.rev_results = []
    self.conf_results = []
    self.simulation_result = {}
    self.threshold = threshold
    self.index = 0
    self.test_name = test_name
    self.template = {'sample_size' : self.sample_size, 'test_name' : self.test_name }

  def analyse_sample_set(self, samples):
    """ Analyses a set of sample of length sample_size """
    result = self.template.copy()
    result.update( { 'index' : self.index,
                     'mean' : get_average(samples)[0],
                     'median': get_median(samples),
                   } )
    self.rev_results.append(result)
    if len(set(samples)) == 1:
      t_prob1 = -1
      t_prob2 = -1
      t_prob3 = -1
    else:
      (t_stat, t_prob1) = stats.ttest_1samp(samples, self.popmean)
      (t_stat, t_prob2) = stats.ttest_1samp(samples, min(int(self.popmean * (1-self.threshold)), self.popmean - 1))
      (t_stat, t_prob3) = stats.ttest_1samp(samples, max(int(self.popmean * (1+self.threshold)), self.popmean + 1))
    result = self.template.copy()
    result.update( { 'index' : self.index,
                     'same' : t_prob1 > 0.05,
                     'same_stat' : t_prob1,
                     'less' : t_prob2 < 0.05,
                     'less_stat' : t_prob2,
                     'more' : t_prob3 < 0.05,
                     'more_stat' : t_prob3,
                   } )
    self.conf_results.append(result)

  def analyse_simulation(self):
    """ Analyse the whole set of samples for this simulation """
    less_valid = sum([r['less_stat'] != -1 for r in self.conf_results])
    less_passed = sum([r['less'] for r in self.conf_results if r['less_stat'] != -1])
    more_valid = sum([r['more_stat'] != -1 for r in self.conf_results])
    more_passed = sum([r['more'] for r in self.conf_results if r['more_stat'] != -1])
    same_valid = sum([r['same_stat'] != -1 for r in self.conf_results])
    same_passed = sum([r['same'] for r in self.conf_results if r['same_stat'] != -1])
    self.simulation_result = self.template.copy()
    self.simulation_result.update( { 'less_ratio' : float(less_passed)/less_valid,
                                     'more_ratio' : float(more_passed)/more_valid,
                                     'same_ratio' : float(same_passed)/same_valid,
                                   } )

  def run_simulation(self, repetitions):
    """ Runs the simulation repetitions number of times """
    print "Simulating sample size: %d" % self.sample_size
    for i in xrange(repetitions):
      samples = []
      for j in xrange(self.sample_size):
        sample = random.choice(self.data)
        samples.append(sample)
      self.analyse_sample_set(samples)
      self.index += 1
    self.analyse_simulation()

def read_data(source_file):
  """ Parses a data file with one observation per line """
  data = []
  for line in source_file:
    data.append(int(line))
  print "Source data size: %d" % len(data)
  return data


def run_simulations(source_data, repetitions, sample_sizes, test_name, threshold = 0.01):
  """ Run a series of simulations on the same source data with a set of sample sizes

      Returns a dictionary of key names to arrays of maps with output values.
  """

  rev_results = []
  conf_results = []
  detection_results = []
  for s in sample_sizes:
    sim = Simulation(source_data, s, test_name)
    sim.run_simulation(repetitions)
    rev_results.extend(sim.rev_results)
    conf_results.extend(sim.conf_results)
    detection_results.append(sim.simulation_result)
  return {'rev': rev_results, 'conf': conf_results, 'detect' : detection_results}

def run_sim(args):
  print "%r" % args.analysers
  random.seed()
  samples = range(args.min_sample, args.max_sample+1)
  out_files = {}

  for source in args.source:
    source_data = read_data(source)
    filename = os.path.basename(source.name)
    test_name = filename[0:filename.rfind('.')]
    print "Simulating %s - %s" % (test_name, datetime.now().strftime("%H:%M:%S"))

    for _ in xrange(args.calibrate):
      start = datetime.now()
      for (key, results) in run_simulations(source_data, args.repetitions,
                                            samples, test_name, args.threshold).items():
        if key not in out_files:
          headers = results[0].keys()
          if args.split:
            f = open(args.output + "_" + filename + "_" + key + ".csv", 'w')
          else:
            f = open(args.output + "_simulation_" + key + ".csv", 'w')
          formatter = CSVFormatter(headers=headers)
          formatter.output_header(f)
          out_files[key] = (formatter, f)

        out_files[key][0].output_records(results, out_files[key][1])
      print "Took: %s" % (datetime.now()-start)

    if args.split:
      for key, pair in out_files.items():
        pair[1].close()
        del out_files[key]

    print "Finished %s - %s" % (test_name, datetime.now().strftime("%H:%M:%S"))

  for _, pair in out_files.items():
    pair[1].close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Simulate talos runs with various sample sizes based on a sample of real data.")
  parser.add_argument("source", help="Data files to use in simulation", nargs='+', type=argparse.FileType('r'))
  parser.add_argument("output", help="Prefix to write output csv to")

  parser.add_argument("--min_sample", help="smallest sample to simulate", type=int, default=3)
  parser.add_argument("--max_sample", help="largest sample to simulate", type=int, default=20)
  parser.add_argument("--repetitions", help="number of repetitions at each sample size", type=int, default=1000)
  parser.add_argument("--threshold", help="the size of change to detect", type=float, default=0.01)
  parser.add_argument("--split", help="when multiple source files are specified, don't combine the results of each type into a single file.", action="store_true", default=False)
  parser.add_argument("--calibrate", help="If specified the simulation will be run the specified number of times allowing for confidence intervals", type=int, default=1)
  parser.add_argument("--analyser", dest="analysers", help="Additional Output Types (rev "\
                      "= mean and median of each sample, conf= confidence "\
                      "probabilities for each sample)", choices=['rev', 'conf', 'detect'],
                      action="append", default=['detect'])


  run_sim(parser.parse_args())
