#!/bin/python
#
#
#lancelotluo@tencent.com  2017.02.14
#

import sys
import re
import os

#grep -o "\:\:.*(" gdb.record|awk -F '(' '{print $1}' >func_frame
dot_file = "auto.dot"
func_file = "func_frame"
def make_fun():
    cmd = "grep -o '\:\:.*(' gdb.record|awk -F '(' '{print $1}' >func_frame"
    os.system(cmd)
def make_pic():
    os.system("dot -Tpng %s -o %s.png" % (dot_file, sys.argv[1]))
def parse_frame():
    of = open(dot_file, "w") 
    of.write("digraph G {\n")
    with open(func_file, "r") as f:
        lines = f.readlines()
        num = len(lines)
        i = num - 1
        print "digraph G {"
        while i > 0:
            print "\"%s\"->\"%s\"" % (lines[i].strip("\n"), lines[i-1].strip("\n"))
            of.write("\"%s\"->\"%s\" \n" % (lines[i].strip("\n"), lines[i-1].strip("\n")))
            i -= 1
        print "}"
        of.write("}")
    of.close()

if __name__ == "__main__":
    make_fun()
    parse_frame()
    make_pic()
