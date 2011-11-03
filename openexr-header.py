#!/usr/bin/env python

import openexr
import optparse
from pprint import pprint as pp


def main():
    opter = optparse.OptionParser()
    opter.add_option("--all", dest = "allheaders", action = "store_true", help = "show all headers")
    opter.add_option("--header", dest = "showheader", action = "append", default = [], help = "header values to show (can be specified multiple times)")
    opts, args = opter.parse_args()

    for f in args:
        img = openexr.OpenEXR(open(f))
        img.parse_headers()
        if len(opts.showheader) == 0 or opts.allheaders:
            print f
            pp(img.headers)

        for headkey in opts.showheader:
            print f, headkey, img.headers[headkey]['value']


if __name__ == "__main__":
    main()
