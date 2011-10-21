
__all__ = ['GraphAnalyser']

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
  def parse_ts(self, data):
    """ Parses a ts data dictionary (can only have one key:value pair)"""

    if len(data) != 1:
      print "Multiple ts results, skipping"
      return None
    nums = [float(x) for x in data[data.keys()[0]].split(',')]
    return get_average(nums, True)

  def parse_tp(self, data):
    """ Parsed a tp data dictionary """
    medians = []
    for key,value in data.items():
      median = get_median([float(x) for x in value.split(',')])
      medians.append(median) 
    return get_average(medians, True)


