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

from gzip import GzipFile
import re
import argparse
import os

class CorruptParser(object):
  talosTestRe = re.compile(r"^Running test (.*?):$")
  corruptRe = re.compile(r"^Corrupt JPEG.*$")
  pageloadRe = re.compile(r"^.*NOISE: Cycle (\d*?): loaded (\S*?) .*$")
  talosEndTestRe = re.compile(r"^Completed test (.*?):$")

  def __init__(self):
    self.linenumber = 0
    self.corrupt_pages = []
    self.in_test = False
    self.seen_corrupt = False
    self.test_name = ""

  def parse(self, fp):
    while 1:
      line = fp.readline()
      self.linenumber += 1
      if not line:
        break
      line = line.rstrip()

      if self.in_test:
        m = self.talosEndTestRe.match(line)
        if m:
          self.in_test = False
          self.test_name = ""
          continue
        m = self.corruptRe.match(line)
        if m:
          self.seen_corrupt = True
          continue
        if self.seen_corrupt:
          m = self.pageloadRe.match(line)
          if m:
            self.corrupt_pages.append((self.test_name, m.group(1), m.group(2)))
          self.seen_corrupt = False
          continue
      else:
        m = self.talosTestRe.match(line)
        if m:
          self.in_test = True
          self.test_name = m.group(1)
          continue

    return (self.corrupt_pages, self.linenumber)

def parse_file(log):
    print log
    try:
      fp = GzipFile(log)
      fp.readline()
      fp.seek(0)
    except IOError, e:
      fp = open(log, "rb")

    parser = CorruptParser()
    (results, _) = parser.parse(fp)
    print results

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some logs')
  parser.add_argument('files', metavar='files', nargs='+',
                     help='a file to parse')
  parser.add_argument('--dir', dest="dir", action="store_true")
  args = parser.parse_args()

  for f in args.files:
    if args.dir:
      for l in os.listdir(f):
        parse_file(os.path.join(f,l))
    else:
      parse_file(f)

