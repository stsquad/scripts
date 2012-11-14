#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# uncow, a simple script to uncow files copied into a fresh btrfs subvolume
#
# (C)opyright 2012 Alex Bennée
# License: GPLv3
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
from array import array
from fcntl import ioctl

# IOCTL constants, ganked from strace of lsattr/chattr
FS_GET_FLAGS=0x80086601
FS_SET_FLAGS=0x80086601
FS_NOWCOW_FL=0x00800000

checked_dirs=dict()

def check_and_modify_dir(verbose, path):
    """
    check directory has +C attribute, if not set it
    """
    if dirname in checked_dirs:
        return

    flags=array('I', [0])
    fd=os.open(path, os.O_DIRECTORY)

    ioctl(fd, FS_GET_FLAGS, flags, 1)
    if not (flags[0] & FS_NOWCOW_FL):
        flags[0] |= FS_NOWCOW_FL
        if verbose: print "setting +C/%x for %s" % (flags[0], path)
        try:
            ioctl(fd, FS_SET_FLAGS, flags)
            checked_dirs[path]=1
        except:
            print "Error setting +C for %s" % (path)
            sys.exit(-2)

    os.close(fd)
        

parser = argparse.ArgumentParser(description='Create new non-COW files with old data.')

parser.add_argument('files', metavar='FILE', nargs='+', help='filepath to uncow')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose output")
args = parser.parse_args()

for p in args.files:
    absp = os.path.abspath(p)
    if os.path.exists(absp):
        old_filename=os.path.basename(absp)
        dirname=os.path.dirname(absp)
        check_and_modify_dir(args.verbose, dirname)
            
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
        

