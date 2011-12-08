import argparse
import random

from statlib import stats

from formatter import *
from analyser import get_median, get_average

class Simulation(object):
  def __init__(self, source_data, sample_size):
    self.data = source_data
    self.popmean = stats.mean(source_data)
    self.sample_size = sample_size
    self.raw_results = []
    self.rev_results = []
    self.conf_results = []
    self.index = 0

  def analyse_sample(self, sample, j):
    result = {'sample_size' : self.sample_size,
              'index' : self.index,
              'run_num' : j,
              'value' : sample,
           }
    self.raw_results.append(result)

  def analyse_sample_set(self, samples):
    result = {'sample_size' : self.sample_size,
              'index' : self.index,
              'mean' : get_average(samples)[0],
              'median': get_median(samples),
             }
    self.rev_results.append(result)
    if len(set(samples)) == 1:
      t_prob1 = -1
      t_prob2 = -1
    else:
      (t_stat, t_prob1) = stats.ttest_1samp(samples, self.popmean)
      (t_stat, t_prob2) = stats.ttest_1samp(samples, min(int(self.popmean * 0.99), self.popmean - 1))
    result = {'sample_size' : self.sample_size,
              'index' : self.index,
              'same' : t_prob1 > 0.05,
              'same_stat' : t_prob1,
              'diff' : t_prob2 < 0.05,
              'diff_stat' : t_prob2,
             }
    self.conf_results.append(result)

  def run_simulation(self, repetitions):
    print "Simulating sample size: %d" % self.sample_size
    for i in xrange(repetitions):
      samples = []
      for j in xrange(self.sample_size):
        sample = random.choice(self.data)
        self.analyse_sample(sample, j)
        samples.append(sample)
      self.analyse_sample_set(samples)
      self.index += 1

def read_data(source_file):
  data = []
  for line in source_file:
    data.append(int(line))
  print "Source data size: %d" % len(data)
  return data


def run_simulations(source_data, repetitions, sample_sizes):
  raw_results = []
  rev_results = []
  conf_results = []
  for s in sample_sizes:
    sim = Simulation(source_data, s)
    sim.run_simulation(repetitions)
    raw_results.extend(sim.raw_results)
    rev_results.extend(sim.rev_results)
    conf_results.extend(sim.conf_results)
  return {'raw': raw_results, 'rev': rev_results, 'conf': conf_results}

def run_sim(args):
  random.seed()
  source_data = read_data(args.source)
  samples = range(args.min_sample, args.max_sample+1)
  for (key, results) in run_simulations(source_data, args.repetitions, samples).items():
    print key, len(results)
    headers = results[0].keys()
    output_file = open(args.output + "_" + key + ".csv", 'w')
    formatter = CSVFormatter(headers=headers)
    formatter.output_header(output_file)
    formatter.output_records(results, output_file)
    output_file.close()

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Simulate talos runs with various sample sizes based on a sample of real data.")
  parser.add_argument("source", help="Data file to use in simulation", type=argparse.FileType('r'))
  parser.add_argument("output", help="File to write output csv to")

  parser.add_argument("--min_sample", help="smallest sample to simulate", type=int, default=3)
  parser.add_argument("--max_sample", help="largest sample to simulate", type=int, default=20)
  parser.add_argument("--repetitions", help="number of repetitions at each sample size", type=int, default=1000)

  run_sim(parser.parse_args())
