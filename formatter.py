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

