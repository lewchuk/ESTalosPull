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

import math
import urllib2
import re
import StringIO
from gzip import GzipFile
from logparser import CorruptParser

__all__ = ['TestSuite', 'BuildAnalyser', 'ComponentAnalyser', 'RunAnalyser', 'CorruptAnalyser',
           'RunDifferenceAnalyser']

def get_median(data, strip_max=False, strip_first=False):
  d = data
  if strip_first:
    d = data[1:]
  d = sorted(d)
  if strip_max:
    d = d[:-1]
  if len(d) % 2 == 1:
    return d[len(d)/2]
  return (d[len(d)/2 - 1] + d[len(d)/2])/2

def get_average(data, strip_max=False, strip_first=False):
  d = data
  if strip_first:
    d = data[1:]
  d = sorted(d)
  if strip_max:
    d = d[:-1]
  total = sum(d)
  size = len(d)
  avg = total/size
  diffs = [pow((x - avg),2) for x in d]
  std_dev = math.sqrt(sum(diffs)/size)
  return (avg, std_dev)

class TestComponent(object):
  def __init__(self, values):
    self.values = values
    self.min = min(values)
    self.max = max(values)

  # For TP tests
  def get_median(self, **kwargs):
    return get_median(self.values, **kwargs)

  # For TS Tets
  def get_average(self, **kwargs):
    return get_average(self.values, **kwargs)

  def __len__(self):
    return len(self.values)

class TestSuite(object):
  def __init__(self, data, is_ts=False):
    self._data = data
    self.is_ts = is_ts
    self.components = {}
    for key, value in self._data.items():
      self.components[key] = TestComponent([float(v) for v in value.split(',')])

  def __len__(self):
    return len(self.components)

  @property
  def old_average(self):
    if self.is_ts:
      assert(len(self) == 1)
      comp = self.components.values()[0]
      return comp.get_average(strip_max=True)
    else:
      d = [comp.get_median(strip_max=True) for comp in self.components.values()]
      return get_average(d, True)

  @property
  def new_average(self):
    if self.is_ts:
      assert(len(self) == 1)
      comp = self.components.values()[0]
      return comp.get_average()
    else:
      d = [comp.get_median(strip_first=True) for comp in self.components.values()]
      return get_average(d)

class BaseAnalyser(object):
  """ A base class for analysers which holds onto results """
  def __init__(self):
    self.results = []
    self.headers = []
    self.suffix = "NA"
    self.types = ["testruns"]

  def get_results(self):
    return [result for result in self.results]

  def flush(self):
    self.results = []

  def get_headers(self):
    return self.headers

  def get_suffix(self):
    return self.suffix

  def types_parsed(self):
    return self.types

class BuildAnalyser(BaseAnalyser):
  def __init__(self):
    BaseAnalyser.__init__(self)
    self.headers = ['graph_result', 'new_result', 'graph_std', 'new_std']
    self.suffix = "builds"

  def parse_data(self, data, template):
    result = template.copy()
    (result['graph_result'], result['graph_std']) = data.old_average
    (result['new_result'], result['new_std']) = data.new_average
    self.results.append(result)

class ComponentAnalyser(BaseAnalyser):
  """ Returns a result for each component of a test """

  def __init__(self):
    BaseAnalyser.__init__(self)
    self.max_tests = -1
    self.index = 1
    self.headers = ['index', 'test_name', 'test_runs', 'max', 'min', 'test_0', 'graph_median', 'new_median', 'new_average', 'new_std_dev']
    self.suffix = "components"

  def parse_data(self, data, template):
    for name, comp in data.components.items():
      result = template.copy()
      result['test_name'] = name
      result['test_0'] = int(comp.values[0])
      result['max'] = comp.max
      result['min'] = comp.min
      result['graph_median'] = comp.get_median(strip_max=True)
      result['new_median'] = comp.get_median(strip_first=True)
      (avg, std_dev) = comp.get_average(strip_first=True)
      result['new_average'] = avg
      result['new_std_dev'] = std_dev
      result['test_runs'] = len(comp.values)
      result['index'] = self.index
      self.results.append(result)
    self.index += 1

class RunAnalyser(BaseAnalyser):
  """ Returns a result for each run of every component of a test """

  def __init__(self):
    BaseAnalyser.__init__(self)
    self.index = 1
    self.headers = ['index', 'test_name', 'run_num', 'value']
    self.suffix = "runs"

  def parse_data(self, data, template):
    for name, comp in data.components.items():
      test_template = template.copy()
      test_template['index'] = self.index
      self.index += 1
      test_template['test_name'] = name
      for pos, value in enumerate(comp.values):
        result = test_template.copy()
        result['run_num'] = pos
        # cast to int so as not to give false impression of precision
        result['value'] = int(value)
        self.results.append(result)

class RunDifferenceAnalyser(RunAnalyser):
  """ Returns a result for the difference in run value from the previous """

  def __init__(self):
    RunAnalyser.__init__(self)
    self.suffix = "run_diffs"

  def parse_data(self, data, template):
    for name, comp in data.components.items():
      test_template = template.copy()
      test_template['index'] = self.index
      self.index += 1
      test_template['test_name'] = name
      last_value = 0
      for pos, value in enumerate(comp.values):
        result = test_template.copy()
        result['run_num'] = pos
        # cast to int so as not to give false impression of precision
        result['value'] = int(value) - last_value
        last_value = int(value)
        self.results.append(result)

class CorruptAnalyser(BaseAnalyser):
  """ Downloads full logs and searches for Corrupt JPEG messages """

  def __init__(self):
    BaseAnalyser.__init__(self)
    self.headers = ['test_name', 'run_num']
    self.suffix = "corrupted"
    self.types = self.types = ["builds"]

  def parse_data(self, data, template):
    url = data['logurl']
    conn = urllib2.urlopen(url)
    raw_data = conn.read()
    data = StringIO.StringIO(raw_data)
    data_file = GzipFile(fileobj=data)
    parser = CorruptParser()
    (entries, _) = parser.parse(data_file)
    for (testsuite, cycle, page) in entries:
      urlRe = re.compile("^http://localhost/page_load_test/%s/(.*?)$" % testsuite)
      m = urlRe.match(page)
      if not m:
        print "unmatched url: %s" % page
        continue
      result = template.copy()
      result['test_name'] = m.group(1)
      result['run_num'] = int(cycle) - 1
      result['testsuite'] = testsuite
      self.results.append(result)


