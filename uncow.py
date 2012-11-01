#!/usr/bin/python
#
# uncow, a simple script to uncow files copied into a fresh btrfs subvolume
#
# Usage:
#  - create a new btrfs subvolume with nodatacow mount option
#  - move all the data you want into the new subvolume
#  - find <SPEC> | uncow.py
#
# What the script does:
#  - create a new file
#  - copy the contents of the old file to new
#  - rm the old file
#  - rename the new file to the old files name
#

import os
import argparse
from uuid import uuid3, NAMESPACE_URL
from shutil import copyfile

parser = argparse.ArgumentParser(description='Create new files with old data.')
parser.add_argument('files', metavar='FILE', nargs='+', help='filepath to uncow')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose output")
args = parser.parse_args()

for p in args.files:
    absp = os.path.abspath(p)
    if os.path.exists(absp):
        old_filename=os.path.basename(absp)
        dirname=os.path.dirname(absp)
        new_filename="%s/%s-%s" % (dirname, old_filename, uuid3(NAMESPACE_URL, old_filename))
        try:
            if args.verbose: print "creating new file %s" % (new_filename)
            copyfile(absp, new_filename)
            if args.verbose: print "removing old file %s" % (absp)
            os.unlink(absp)
            if args.verbose: print "renaming %s to %s" % (new_filename, absp)
            os.rename(new_filename, absp)
        except:
            print "error with %s, %s" % (absp, new_filename)
            exit -1
        
