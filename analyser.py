
__all__ = ['GraphAnalyser', 'ComponentAnalyser']

def get_median(data, strip_max=False):
  d = sorted(data)
  if strip_max:
    d = d[:-1]
  if len(d) % 2 == 1:
    return d[len(d)/2]
  return (d[len(d)/2 - 1] + d[len(d)/2])/2

def get_average(data, strip_max=False):
  total = sum(data)
  size = len(data)
  if strip_max:
    total -= max(data)
    size -= 1
  return total / size

class GraphAnalyser(object):
  def parse_ts(self, data, template):
    """ Parses a ts data dictionary (can only have one key:value pair)"""

    if len(data) != 1:
      print "Multiple ts results, skipping"
      return None
    nums = [float(x) for x in data[data.keys()[0]].split(',')]

    result = template.copy()
    result['result'] = get_average(nums, True)
    return [result]

  def parse_tp(self, data, template):
    """ Parsed a tp data dictionary """
    medians = []
    for key,value in data.items():
      median = get_median([float(x) for x in value.split(',')])
      medians.append(median)

    result = template.copy()
    result['result'] = get_average(medians, True)
    return [result]

  def get_headers(self):
    return ['result']

class ComponentAnalyser(object):
  """ Returns a result for each component of a test """

  def __init__(self):
    self.max_tests = -1

  def parse_data(self, data, template):
    results = []
    for key, value in data.items():
      result = template.copy()
      result['test_name'] = key
      for num, run in enumerate(value.split(',')):
        result["test_%d" % num] = run
      self.max_tests = max(self.max_tests, num)
      result['test_runs'] = num + 1
      results.append(result)
    return results

  def parse_ts(self, data, template):
    return self.parse_data(data, template)

  def parse_tp(self, data, template):
    return self.parse_data(data, template)

  def get_headers(self):
    headers = ['test_name', 'test_runs']
    for i in range(self.max_tests+1):
      headers.append('test_%d' % i)
    return headers
