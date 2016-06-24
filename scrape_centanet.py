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
parser.add_option("--pages", dest="pages", type="int", help="Number of Pages (Starting from Page 1)", default=99999999)
parser.add_option("--workers", dest="workers", type="int", help="Number of Processes", default=10)
(options, args) = parser.parse_args()

try:
    os.makedirs(options.directory)
except OSError:
    pass

# Centanet - Orders on Market

class PageTask:
    def __init__(self, page):
        self.page = page
    def __call__(self):
        try:
            page_contents = centanet_utils.parse_page_content(centanet_utils.get_page(self.page))
            return (self.page, page_contents)
        except:
            return (self.code, None)

contents = []

try:
    pagePool = worker.WorkerPool(options.workers)
    pagePool.start()
    n_pages = centanet_utils.get_page_count()
    count = 0
    for i in range(0, min(n_pages, options.pages)):
        pagePool.put(PageTask(i + 1))
    while count < min(n_pages, options.pages):
        try:
            result = pagePool.get(timeout=1)
        except queue.Empty:
            result = None
        if result:
            (page, page_contents) = result
            if not page_contents:
                pagePool.put(PageTask(page))
                print("Retrying page %d ..." % page, file=sys.stderr)
            else:
                contents += page_contents
                count += 1
                print("Downloaded page %d." % page, file=sys.stderr)
except KeyboardInterrupt:
    print("Download Interrupted.", file=sys.stderr)
finally:
    pagePool.terminate()

df = pandas.DataFrame.from_dict(contents)
df = df[["title", "district", "details", "sale_price", "is_bo", "net_area", "net_price", "gross_area", "gross_price"]]
df.to_csv(os.path.join(options.directory, "centanet_orders_%s.csv" % datetime.strftime(datetime.now(), "%Y%m%d")), header=True, index=False, encoding='utf-8')

print("Downloaded.", file=sys.stderr)

