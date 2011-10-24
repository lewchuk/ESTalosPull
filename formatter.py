import json

__all__ = ['JsonFormatter', 'CSVFormatter']

class BaseFormatter(object):
  def __init__(self, headers):
    self.headers = headers

class JsonFormatter(BaseFormatter):
  def __init__(self, **kwargs):
    BaseFormatter.__init__(self, **kwargs)

  def output_records(self, records, output):
    output.write("%s\n" % json.dumps(records))

class CSVFormatter(BaseFormatter):
  def __init__(self, **kwargs):
    BaseFormatter.__init__(self, **kwargs)
    self.formatter = "%(" + ")s,%(".join(self.headers) + ")s\n"

  def output_records(self, records, output):
    output.write("%s\n" % ','.join(self.headers))
    for record in records:
      output.write(self.formatter % record)

