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

