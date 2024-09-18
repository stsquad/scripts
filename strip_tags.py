#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# strip_tags, a simple script remove bad tags from video files.
#
# (C)opyright 2024 Alex Bennée
# License: GPLv3
#
# What it does:
#  - copy input file using ffmpeg:
#    ffmpeg -i <file> -map_metadata:g:TAG -1 -c copy temp.mp4
#  - remove the old <file>
#  - mv temp.mp4 to the original position in the filesystem renaming
#    to replace

import os
from os.path import basename, dirname, join
from argparse import ArgumentParser


def parse_arguments(options=None):
    """
    Read the file name and which tag to clean (Movie name or Title)
    """
    parser = ArgumentParser(description="Clean tags.")

    # add arguments
    parser.add_argument("file", help="input file")
    parser.add_argument("--movie-name", action='store_true',
                        help="strip Movie Name tag")
    parser.add_argument("--title", action='store_true',
                        help="strip Title tag")

    return parser.parse_args(options)


if __name__ == "__main__":
    args = parse_arguments()

    if args.file is None:
        print("Need to specify a file")
        exit(-1)

    ffmpeg_cmd = ["ffmpeg", "-c", "copy", "-i", args.file]

    orig_name = basename(args.file)
    orig_path = dirname(args.file)

    if args.movie_name:
        ffmpeg_cmd += ["-map_metadata:g:Movie name", -1]

    if args.title:
        ffmpeg_cmd += ["-map_metadata:g:track_info_title", -1]

    # local copy of file
    copy_file = join(os.getcwd(), orig_name)

    ffmpeg_cmd += [copy_file]

    print(ffmpeg_cmd)
