import optparse
import pyes
import json

from analyser import *

analysers = {
    'graph' : GraphAnalyser,
}

basic_fields = ['revision', 'machine', 'starttime']
parametric_fields = ['testgroup', 'testsuite', 'os', 'buildtype', 'tree']

def parse_results(data, analyser, spec_fields):
  """ Parses a testrun document """
  template = {}
  for field in basic_fields:
    template[field] = data.get(field, None)
  for field in spec_fields:
    template[field] = data.get(field, None)

  test_data = data['testruns']
  results = None
  if 'format' not in data:
    print "no format, skipping"
  elif data['format'] == 'ts_format':
    results = analyser.parse_ts(test_data, template)
  elif data['format'] == 'tp_format':
    results = analyser.parse_tp(test_data, template)

  return results

def request_data(args):
  conn = pyes.ES(args.get("es_server","localhost:9200"))
  if "index" in args:
    conn.open_index(args.get("index"))
  
  query = pyes.query.ConstantScoreQuery()

  spec_fields = []
  strip_fields = args.get("strip_fields", False)

  for field in parametric_fields:
    if field in args:
      val = args.get(field)
      for seg in val.split('-'):
        query.add(pyes.filters.TermFilter(field, seg))
      if not strip_fields:
        spec_fields.append(field)
    else:
      spec_fields.append(field)

  if "from" in args and "to" in args:
    erange = pyes.utils.ESRange("date", from_value=args.get("from"), to_value=args.get("to"))
    query.add(pyes.filters.RangeFilter(erange))

  size = args.get("size", 20)
  if args.get("all", False):
    data = conn.count(query)
    size = data.get("count")

  print "Query: %s" % query.serialize()
  data = conn.search(query=query, size=size)

  print "Data: %d/%d" % (len(data["hits"]["hits"]), data["hits"]["total"])
  
  analyser_name = args.get("analyser", "graph")
  analyser = analysers.get(analyser_name, None)
  if analyser is None:
    print "Unrecognized analyser: %s" % analyser_name
    return

  analyser = analyser()

  if args.get("summarize",False):
    results = []
    for dp in data['hits']['hits']:
      if dp['_type'] == 'testruns':
        result = parse_results(dp['_source'], analyser, spec_fields)
        if result:
          results.extend(result)
    out_format = args.get("format", "json")
    if out_format == "json":
      result_string = json.dumps(results)
    elif out_format == "csv":
      s = []
      if spec_fields:
        specs = "%(revision)s,%(machine)s,%(starttime)s,%(" + ")s,%(".join(spec_fields) + ")s,%(result)s"
        s.append("revision,machine,starttime," + ",".join(spec_fields) + ",result")
      else:
        specs = "%(revision)s,%(machine)s,%(starttime)s,%(result)s"
        s.append("revision,machine,starttime,result")
      for d in results:
        s.append(specs % d)
      result_string =  '\n'.join(s)
  else:
    print data['hits']['hits']
  
  if "output" in args:
    f = open(args.get("output"),'w')
    f.write(result_string)
    f.close()
  else:
    print result_string

def cli():
  usage = "usage: %prog [options]"
  parser = optparse.OptionParser(usage=usage)

  # server spec options
  parser.add_option("--es-server", dest="es_server", help="ES Server to query", action="store", default="localhost:9200")
  parser.add_option("--index", dest="index", help="Index to query (optional)", action="store")

  # query spec options
  parser.add_option("--from", dest="from_date", help="Start Date of query (also needs --to)", action="store")
  parser.add_option("--to", dest="to", help="End Date of query (also needs --from)", action="store")
  parser.add_option("--tree", dest="tree", help="Tree to query", action="store")
  parser.add_option("--testsuite", dest="testsuite", help="Test to query", action="store")
  parser.add_option("--testgroup", dest="testgroup", help="Testgroup to query", action="store")
  parser.add_option("--os", dest="os", help="OS to query", action="store")
  parser.add_option("--buildtype", dest="buildtype", help="Buildtype to query", action="store")

  # result size options
  parser.add_option("--all", dest="all", help="Retrieve all results", action="store_true") 
  parser.add_option("--size", dest="size", help="Size of query, overridden by --all", action="store", default=20)

  # output options
  parser.add_option("--format", dest="format", help="Output format (json, csv)", action="store", default="json")
  parser.add_option("--output", dest="output", help="File to dump output to", action="store")
  parser.add_option("--summarize", dest="summarize", help="Apply graph server summary algorithm", action="store_true")
  parser.add_option("--analyser", dest="analyser", help="Analyser to use for summarization, options=(graph)",
                    action="store", default="graph")
  parser.add_option("--strip-spec-fields", dest="strip_fields", help="Remove fields constrained by a spec option from output",
                    action="store_true")

  (options, args) = parser.parse_args()

  request = {"es_server":options.es_server,
             "summarize":options.summarize,
             "all":options.all,
             "size":options.size,
             "format":options.format,
             "analyser":options.analyser,
             "strip_fields":options.strip_fields,
             }

  if options.index:
    request.update({"index":options.index})
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
