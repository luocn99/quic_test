#!/bin/python
#
#
#lancelotluo@tencent.com  2017.02.14
#

import sys
import re
import os

#grep -o "\:\:.*(" gdb.record|awk -F '(' '{print $1}' >func_frame

def parse_log(log):
    with open(log, "r") as f:
        lines = f.readlines()
        num = len(lines)
        i = num - 1
        print "digraph G {"
        while i > 0:
            print "\"%s\"->\"%s\"" % (lines[i].strip("\n"), lines[i-1].strip("\n"))
            i -= 1
        print "}"

if __name__ == "__main__":
    if len(sys.argv) != 2 :
        print("wrong arg num, usage: log_file")
        exit(1)
    parse_log(sys.argv[1])
