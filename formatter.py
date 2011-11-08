import json

__all__ = ['JsonFormatter', 'CSVFormatter']

class BaseFormatter(object):
  def __init__(self, headers):
    self.headers = headers

  def get_suffix(self):
    raise NotImplementedError

class JsonFormatter(BaseFormatter):
  def __init__(self, **kwargs):
    BaseFormatter.__init__(self, **kwargs)

  def output_records(self, records, output):
    output.write("%s\n" % json.dumps(records))

  def get_suffix(self):
    return ".json"

class CSVFormatter(BaseFormatter):
  def __init__(self, **kwargs):
    BaseFormatter.__init__(self, **kwargs)
    self.formatter = "%(" + ")s,%(".join(self.headers) + ")s\n"

  def fill_record(self, record):
    for header in self.headers:
      if header not in record:
        record[header] = "NA"

  def output_records(self, records, output):
    output.write("%s\n" % ','.join(self.headers))
    for record in records:
      self.fill_record(record)
      output.write(self.formatter % record)

  def get_suffix(self):
    return ".csv"

