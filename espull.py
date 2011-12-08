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

import sys
import os
import argparse
import pyes
import json

from analyser import *
from formatter import *

analyser_classes = {
    'build' : BuildAnalyser,
    'comp' : ComponentAnalyser,
    'run' : RunAnalyser,
    'corrupt' : CorruptAnalyser,
    'run_diff' : RunDifferenceAnalyser,
}

formatters = {
    'json' : JsonFormatter,
    'csv' : CSVFormatter,
}

basic_fields = ['revision', 'machine', 'starttime']
parametric_fields = ['testgroup', 'testsuite', 'os', 'buildtype', 'tree']

def parse_results(data, analysers, spec_fields, log_type):
  """ Parses a testrun document into the specified analyser"""
  template = {}
  for field in basic_fields:
    template[field] = data.get(field, None)
  for field in spec_fields:
    template[field] = data.get(field, None)

  results = None
  if log_type == "testruns" and 'format' not in data:
    print "no format, skipping"
    return

  data_obj = data
  if log_type == "testruns":
    data_obj = TestSuite(data['testruns'], data['format'] == 'ts_format')

  for analyser in analysers:
    if log_type in analyser.types_parsed():
      analyser.parse_data(data_obj, template)

def generate_query(args):
  query = pyes.query.ConstantScoreQuery()

  spec_fields = []
  strip_fields = args.get("strip_fields", False)

  for field in parametric_fields:
    if field in args:
      val = args.get(field)

      # allow OR specs
      or_filters = []
      for or_seg in val.split('|'):
        and_filters = []
        # hack to allow filtering on trees as ES tokenizes on -
        for and_seg in or_seg.split('-'):
          and_filters.append(pyes.filters.TermFilter(field, and_seg))
        or_filters.append(pyes.filters.ANDFilter(and_filters))
      query.add(pyes.filters.ORFilter(or_filters))

      if not strip_fields or len(or_filters) > 1:
        spec_fields.append(field)
    else:
      spec_fields.append(field)

  if "from" in args and "to" in args:
    erange = pyes.utils.ESRange("date", from_value=args.get("from"), to_value=args.get("to"))
    query.add(pyes.filters.RangeFilter(erange))

  print "Query: %s" % query.serialize()

  return (query, spec_fields)

def build_analysers(spec_fields, args):
  analyser_names = args.get("analysers", ["build"])
  analysers = []
  for name in analyser_names:
    a_class = analyser_classes.get(name, None)
    if a_class is None:
      print "Unrecognized analyser: %s" % name
      continue
    analysers.append(a_class())

  if not analysers:
    print "No recognized analyser"
    return

  if args.get("dump",False):
    print data
    return

  out_format = args.get("format", "json")
  formatter = formatters.get(out_format, None)
  if formatter is None:
    print "Unrecognized formatter: %s" % out_format
    return

  outputters = []
  for analyser in analysers:
    headers = []
    headers.extend(basic_fields)
    headers.extend(spec_fields)
    headers.extend(analyser.get_headers())

    a_formatter = formatter(headers=headers)
    if 'output' in args:
      outputters.append(FileOutput(args.get('output'), analyser, a_formatter))
    else:
      outputters.append(BaseOutput(analyser, a_formatter))

    outputters[-1].output_header()

  return outputters

def retrieve_data(conn, query, from_i, size, args):
  print "Retrieving Data %s - %s" % (from_i, from_i + size)
  kwargs = {'query' : query,
            'size' : size,
            'from' : from_i,
            'indexes' : [args.get('index','talos')]
           }
  data = conn.search(**kwargs)
  print "Data: %d/%d" % (len(data["hits"]["hits"])+from_i, data["hits"]["total"])

  return data

def analyse_data(data, outputters, spec_fields, args):
  analysers = [o.analyser for o in outputters]

  types = set()
  for a in analysers:
    types.update(a.types_parsed())

  errors = []

  data_iter = iter(data['hits']['hits'])
  total_data = len(data['hits']['hits'])
  for dp in data['hits']['hits']:
    log_type = dp['_type']
    if log_type in types:
      if log_type == "testruns" and not dp['_source']['testruns']:
        errors.append(dp)
      else:
        parse_results(dp['_source'], analysers, spec_fields, log_type)

  for outputter in outputters:
    outputter.output_records()

  return errors

def request_data(args):
  (query, spec_fields) = generate_query(args)
  outputters = build_analysers(spec_fields, args)

  address = args.get("es_server", "localhost:9200")
  print "Connecting to: %s" % address
  conn = pyes.ES(address)

  size = args.get("size", 20)
  if args.get("all", False):
    print "Retrieving count"
    data = conn.count(query)
    size = data.get("count")

  batch = min(args.get("batch", 1000), size)

  splits = range(0, size, batch)

  errors = []
  for s in splits:
    data = retrieve_data(conn, query, s, batch, args)
    e = analyse_data(data, outputters, spec_fields, args)
    errors.extend(e)

  if errors:
    if 'output' in args:
      output_file = args.get('output') + "_errors.json"
      output = open(output_file, 'w')
      output.write("%s\n" % json.dumps(errors))
      output.close()
    else:
      print "Errors:"
      print errors



def cli():
  parser = argparse.ArgumentParser(description="Script to pull a filtered set of talos logs down from ElasticSearch.  The set of log summaries can be filtered by a variety of dimensions.  Once downloaded the summaries are analysed, formatted and stored in the specified location.")

  server_options = parser.add_argument_group('Server Specification')
  # server spec options
  server_options.add_argument("--es-server", dest="es_server", help="ES Server to query", default="localhost:9200")
  server_options.add_argument("--index", help="Index to query", default="talos")

  # query spec options
  filter_options = parser.add_argument_group('Filter Specification')
  filter_options.add_argument("--from", dest="from_date",
                              help="Start Date of query YYYY-MM-DD (also needs --to)")
  filter_options.add_argument("--to", help="End Date of query YYYY-MM-DD (also needs --from)")
  filter_options.add_argument("--tree", help="Tree to query")
  filter_options.add_argument("--testsuite", help="Test to query")
  filter_options.add_argument("--testgroup", help="Testgroup to query")
  filter_options.add_argument("--os", help="OS to query")
  filter_options.add_argument("--buildtype", help="Buildtype to query")

  # result size options
  retrieval_options = parser.add_argument_group('Retrieval Options')
  retrieval_options.add_argument("--all", help="Retrieve all results", action="store_true")
  retrieval_options.add_argument("--size", help="Size of query, overridden by --all",
                                 default=20, type=int)
  retrieval_options.add_argument("--batch", help="Maximum size of batch to download and analyse",
                                 default=1000, type=int)

  # output options
  output_options = parser.add_argument_group('Output Options')
  output_options.add_argument("--format", help="Output format", choices=formatters.keys(),
                              default="csv")
  output_options.add_argument("--output", help="File prefix to dump output to")
  output_options.add_argument("--dump", help="Dump raw ES results to stdout",
                              action="store_true")
  output_options.add_argument("--analyser", dest="analysers",
                              help="Analyser to use for summarization (can specify multiple)",
                              choices=analyser_classes.keys(), action="append")
  output_options.add_argument("--strip-spec-fields", dest="strip_fields",
                              help="Remove fields constrained by a spec option from output",
                              action="store_true")

  options = parser.parse_args()

  request = {"es_server":options.es_server,
             "dump":options.dump,
             "all":options.all,
             "size":options.size,
             "format":options.format,
             "analysers":options.analysers or ['build'],
             "strip_fields":options.strip_fields,
             "index":options.index,
             "batch":options.batch,
             }

  if options.from_date:
    request.update({"from":options.from_date})
  if options.to:
    request.update({"to":options.to})
  if options.tree:
    request.update({"tree":options.tree})
  if options.testsuite:
    request.update({"testsuite":options.testsuite})
  if options.testgroup:
    request.update({"testgroup":options.testgroup})
  if options.os:
    request.update({"os":options.os})
  if options.buildtype:
    request.update({"buildtype":options.buildtype})
  if options.output:
    request.update({"output":options.output})

  request_data(request)

if __name__ == "__main__":
  cli()
