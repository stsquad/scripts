#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Compiledb clean-up script
#
# Copyright (C) 2018, Alex Bennée <alex@bennee.com>
# License: GPLv3
#
# This is a script for post-processing compile_commands.json generated
# by other tools. The initial use case it to canconicalize "file"
# entries so libclang can find things that where referenced in a
# sub-build directory.
#

# for Python3 cleanliness
from __future__ import print_function

from argparse import ArgumentParser
import json
import os.path as path


def parse_arguments(options=None):
    """
    Read the arguments and return them to main.
    """
    parser = ArgumentParser(description="Clean-up compiledb.")

    parser.add_argument("compiledb", type=file, nargs=1,
                        help="compile database to process")

    return parser.parse_args(options)


def canconicalize_files(json_cbd):
    """
    Parse the directory and file entries and canconicalize any
    indirect files.
    """
    fixed = 0

    for entry in json_cbd:
        fn = entry["file"]
        if not path.isabs(fn):
            nfn = entry["directory"] + "/" + fn
            entry["file"] = path.normpath(nfn)
            print("new file: %s" % (entry["file"]))
            fixed += 1

    return (fixed, json_cbd)


if __name__ == "__main__":
    args = parse_arguments()

    for f in args.compiledb:
        db = json.load(f)
        (fixed, new_db) = canconicalize_files(db)

        if fixed > 0:
            nf = f.name + ".fixed"
            ndb = open(nf, "w")
            json.dump(new_db, ndb)
            print ("Updated %d entries" % (fixed))
