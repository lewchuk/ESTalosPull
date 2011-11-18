import math

__all__ = ['TestSuite', 'BuildAnalyser', 'ComponentAnalyser', 'RunAnalyser']

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

  def get_results(self):
    return [result for result in self.results]

  def flush_results(self):
    self.results = []

class BuildAnalyser(BaseAnalyser):
  def __init__(self):
    BaseAnalyser.__init__(self)

  def parse_data(self, data, template):
    result = template.copy()
    (result['graph_result'], result['graph_std']) = data.old_average
    (result['new_result'], result['new_std']) = data.new_average
    self.results.append(result)

  def get_headers(self):
    return ['graph_result', 'new_result', 'graph_std', 'new_std']

  def get_suffix(self):
    return "builds"

class ComponentAnalyser(BaseAnalyser):
  """ Returns a result for each component of a test """

  def __init__(self):
    BaseAnalyser.__init__(self)
    self.max_tests = -1
    self.index = 1

  def parse_data(self, data, template):
    for name, comp in data.components.items():
      result = template.copy()
      result['test_name'] = name
      for num, run in enumerate(comp.values):
        result["test_%d" % num] = int(run)
      self.max_tests = max(self.max_tests, len(comp))
      result['max'] = comp.max
      result['min'] = comp.min
      result['graph_median'] = comp.get_median(strip_max=True)
      result['new_median'] = comp.get_median(strip_first=True)
      (avg, std_dev) = comp.get_average(strip_first=True)
      result['new_average'] = avg
      result['new_std_dev'] = std_dev
      result['test_runs'] = num + 1
      result['index'] = self.index
      self.results.append(result)
    self.index += 1

  def get_headers(self):
    headers = ['index', 'test_name', 'test_runs', 'max', 'min', 'graph_median', 'new_median', 'new_average', 'new_std_dev']
    for i in range(self.max_tests):
      headers.append('test_%d' % i)
    return headers

  def get_suffix(self):
    return "components"

class RunAnalyser(BaseAnalyser):
  """ Returns a result for each run of every component of a test """

  def __init__(self):
    BaseAnalyser.__init__(self)
    self.index = 1

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

  def get_headers(self):
    return ['index', 'test_name', 'run_num', 'value']

  def get_suffix(self):
    return "runs"

