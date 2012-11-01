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

import sys,os
import argparse
from uuid import uuid3, NAMESPACE_URL
from shutil import copyfile
from subprocess import check_output,check_call,STDOUT,CalledProcessError
from re import search

checked_dirs=dict()

def check_and_modify_dir(verbose, chattr, lsattr, path):
    """
    check directory has +C attribute, if not set it
    """
    if dirname in checked_dirs:
        return
    
    out = check_output([lsattr, "-d",  path])
    if not search("-?C",out):
        if verbose: print "setting +C for %s" % (path)
        try:
            check_call([chattr, "+C", path])
            checked_dirs[path]=1
        except:
            print "Error setting +C for %s" % (path)
            sys.exit(-2)
        

parser = argparse.ArgumentParser(description='Create new non-COW files with old data.',
                                 epilog="""This script needs an as yet un-released
version of e2fsprogs to manipulate the COW attributes on files and directories.
If you don't have this on your system you can build e2fsprog and point the script
at the new binaries with the appropriate flags""")

parser.add_argument('files', metavar='FILE', nargs='+', help='filepath to uncow')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose output")
parser.add_argument('--chattr', default="chattr", help="path to the chattr binary")
parser.add_argument('--lsattr', default="lsattr", help="path to the lsattr binary")
args = parser.parse_args()

# First verify lsattr/chattr support +C flag
try:
    out = check_output(args.chattr, stderr=STDOUT)
except CalledProcessError as c:
    # no args returns -1 anyway
    out = c.output
    

if not search("\[-\+=.*C", out):
    print "Your copy of chattr doesn't support marking files/dirs as non-COW\n\n"
    parser.print_help()
    sys.exit(-1)


for p in args.files:
    absp = os.path.abspath(p)
    if os.path.exists(absp):
        old_filename=os.path.basename(absp)
        dirname=os.path.dirname(absp)
        check_and_modify_dir(args.verbose, args.chattr, args.lsattr, dirname)
            
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
        
