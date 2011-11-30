import json
import sys

__all__ = ['JsonFormatter', 'CSVFormatter', 'BaseOutput', 'FileOutput']

class BaseFormatter(object):
  def __init__(self, headers):
    self.headers = headers

  def get_suffix(self):
    raise NotImplementedError

  def output_header(self, output):
    pass

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
    for record in records:
      self.fill_record(record)
      output.write(self.formatter % record)

  def output_header(self, output):
    output.write("%s\n" % ','.join(self.headers))

  def get_suffix(self):
    return ".csv"

class BaseOutput(object):
  def __init__(self, analyser, formatter):
    self.analyser = analyser
    self.formatter = formatter
    self.output = sys.stdout

  def output_header(self):
    self.formatter.output_header(self.output)

  def output_records(self):
    self.formatter.output_records(self.analyser.get_results(), self.output)
    self.analyser.flush()

  def close(self):
    pass

class FileOutput(BaseOutput):
  def __init__(self, output, *pargs):
    BaseOutput.__init__(self, *pargs)
    out_file = output + "_" + self.analyser.get_suffix() + self.formatter.get_suffix()
    self.output = open(out_file, 'w')

  def close(self):
    self.output.close()

