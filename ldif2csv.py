#!/usr/bin/python

from __future__ import print_function
import re
import argparse as arg
import sys
from collections import OrderedDict
import csv

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# define the arguments first

descript    = "Convert LDIF files to CSV"
parser      = arg.ArgumentParser( description = descript, epilog = epilogstr )
parser.add_argument('infile', metavar = 'inputfile|-', help = 'LDIF input file.')
parser.add_argument('--debug', action='store_true', help = 'debug')
parser.add_argument('--debug2', action='store_true', help = 'debug long line logic')

# define a list of regexes of attributes to remove (modify as needed)
badAttrList = [ '^authpassword;oid:', '^authpassword;orclcommonpwd:'  ]

# compile the regexes for the match function. Ignore case
badRegexList = [re.compile(x, re.IGNORECASE) for x in badAttrList]

# extract the fields and parse into lists

regexDN = re.compile('^dn: ', re.IGNORECASE)

regexKeyVal = re.compile('^(.*): (.*)$')


# return True if the attribute should be excluded; false otherwise
def filterattr(ln):
  for pattern in badRegexList:
    if pattern.match(ln):
       return True
  return False

# NOTE: Modify the desired columns for your directory. The "dn" column is required. 
COLUMNS = ["dn", "cn", "creatorsname", "givenname", "mail", "objectclass", "obver", "orclaci", 
"orclentrylevelaci", "orclguid", "orclisenabled", "orclnormdn", "orclpassword", "orclrevpwd", 
"ou", "sn", "uid", "userpassword"]

# print block and filter out unwanted attributes
def block2csv(blk, outcsv):
  csvDict = OrderedDict()
  if args.debug2:
    return
  if len(blk) > 0:
    for i in blk:
      if not filterattr(i):
        s = regexKeyVal.search(i)
        if s is not None:
          k = s.group(1).strip()
          v = s.group(2).strip()
          #print(k,v)
          # generalized so that any attribute can be multi-valued (except dn)
          try:
            cls = csvDict[k]
            csvDict[k] = cls + ';' + v
          except KeyError:
            csvDict[k] = v
    # now that we have a dictionary of key and value lists, we want to print out the csv row
    # Since we're programming interactively, we'll print out the dictionary
    if args.debug:
      print(csvDict)
    # when we are done printing out the csvDict as a csv row then we need a new dictionary
    row = []
    for col in COLUMNS:
      try:
        v = csvDict[col]
        row.append(v)
      except KeyError:
        row.append('')
    if args.debug:
       print(row)
    outcsv.writerow(row)

# The following lookahead function was borrowed from 
# https://stackoverflow.com/questions/4197805/python-for-loop-look-ahead/4198074
from itertools import tee, islice, izip_longest
def get_next(some_iterable, window=1):
    items, nexts = tee(some_iterable, 2)
    nexts = islice(nexts, window, None)
    return izip_longest(items, nexts)

block = list()

args = parser.parse_args()  # parse command line arguments
outcsv = csv.writer(sys.stdout)
outcsv.writerow(COLUMNS)

try:

  f = open(args.infile, 'r') if args.infile <> '-' else sys.stdin
  for line, nextline in get_next(f):
    l = line.rstrip()
    m = ''
    if nextline is not None:
       m = nextline.strip()
    if regexDN.match(l):  # You found a new block -- these starr with dn
      block2csv(block, outcsv) # print the prior block, if there is one
      block = list()    # start with new block
    # check if the next line starts with an attribute. If not, append
    if not regexKeyVal.match(m) and len(m) > 0:
      if args.debug2:
         print('Found long line: ', l+m, len(l+m))
      block.append(l+m)
    else:
      block.append(l)

  # print the last block
  block2csv(block, outcsv)

except IOError as e:
  raise IOError, "I/O error({0}): {1}".format(e.errno, e.strerror)
