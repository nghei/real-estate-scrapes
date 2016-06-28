#!/usr/bin/env python

import sys
import os
from datetime import datetime
from optparse import OptionParser
import queue
import pandas

import centanet_utils
import worker

parser = OptionParser()
parser.add_option("--directory", dest="directory", help="Directory to Store Data", default="data")
parser.add_option("--pages", dest="pages", type="int", help="Number of Pages", default=99999999)
parser.add_option("--workers", dest="workers", type="int", help="Number of Processes", default=10)
(options, args) = parser.parse_args()

try:
    os.makedirs(options.directory)
except OSError:
    pass

# Centanet - Historical Transactions

dt = datetime.now()

estates = centanet_utils.findLinksToEstate()

class EstateTask:
    def __init__(self, estate_code, estate_type):
        self.estate_code = estate_code
        self.estate_type = estate_type
    def __call__(self):
        try:
            estate_details = centanet_utils.get_estate_details(self.estate_code, self.estate_type)
            estate_contents = centanet_utils.getHistoricalTransactionEstate(self.estate_code, self.estate_type)
            return ((self.estate_code, self.estate_type), (estate_details, estate_contents))
        except:
            return ((self.estate_code, self.estate_type), None)

details = []
contents = []

try:
    estatePool = worker.WorkerPool(options.workers)
    estatePool.start()
    for estate in estates[:options.pages]:
        estatePool.put(EstateTask(estate["code"], estate["type"]))
    count = 0
    while count < len(estates[:options.pages]):
        try:
            result = estatePool.get(timeout=1)
        except queue.Empty:
            result = None
        if result:
            (estate, estate_results) = result
            if not estate_results:
                estatePool.put(EstateTask(estate[0], estate[1]))
                print("Retrying estate (%s, %s) ..." % estate, file=sys.stderr)
            else:
                (estate_details, estate_contents) = estate_results
                details.append(estate_details)
                contents += estate_contents
                count += 1
                print("Downloaded estate (%s, %s)." % estate, file=sys.stderr)
except KeyboardInterrupt:
    print("Download Interrupted.", file=sys.stderr)
finally:
    estatePool.terminate()

df = pandas.DataFrame.from_dict(details)
df = df[["estate_name", "code", "type", "address", "school_net", "developer", "start_date", "tower_count", "flat_count"]]
df.to_csv(os.path.join(options.directory, "centanet_estate_details_%s.csv" % datetime.strftime(dt, "%Y%m%d")), header=True, index=False, encoding='utf-8')

df = pandas.DataFrame.from_dict(contents)
df = df[["code", "type", "flat_name", "date", "sale_price", "net_area", "net_price", "gross_area", "gross_price"]]
df.to_csv(os.path.join(options.directory, "centanet_historical_transactions_%s.csv" % datetime.strftime(dt, "%Y%m%d")), header=True, index=False, encoding='utf-8')

print("Downloaded.", file=sys.stderr)

