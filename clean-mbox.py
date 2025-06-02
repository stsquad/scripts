#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Clean mbox archive
#
# The archive rightly contains a bunch of metadata and alternative
# copies of patches. But really we just want the basic facts of the
# thread.
#

import mailbox
import re
from email.parser import Parser
from email.header import decode_header

import argparse
import sys


def decode_and_join(header):
    """
    Decodes a header string that might contain encoded parts and joins them into a single string.

    Args:
        header (str): The header string to decode.

    Returns:
        str: The decoded and joined header string, or an empty string if the header is None.
    """
    if not header:
        return ""

    try:
        decoded_parts = decode_header(header)
        parts = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                except UnicodeDecodeError:
                    parts.append(part.decode('utf-8', errors='replace'))  # Try UTF-8 with replacement
            else:
                parts.append(str(part))  # Already a string

        return "".join(parts)
    except Exception as e:
        sys.stderr.write(f"Error decoding header: {e}\n")
        return header  # Return original header on failure (best effort)



def _process_payload(payload, content_type, charset):
    """
    Helper function to decode and output the text content of a payload.
    """
    if payload:
        try:
            decoded_payload = payload.decode(charset or 'utf-8', errors='ignore')
            if content_type == "text/plain":
                sys.stdout.write(decoded_payload)
            elif content_type == "text/html":
                sys.stdout.write(re.sub(r'<[^>]+>', '', decoded_payload))
        except Exception as e:
            sys.stderr.write(f"Error decoding payload: {e}\n")



def sanitize_mbox_stream(mbox_path):
    """
    Takes an mbox archive path and yields the plain text content of each
    email, stripped of excessive headers and HTML, directly to stdout.

    Args:
        mbox_path (str): The path to the mbox file.
    """
    try:
        mbox = mailbox.mbox(mbox_path)
        parser = Parser()

        for key, message in mbox.iteritems():

            from_header = message.get('From')
            date_header = message.get('Date')

            if from_header:
                sys.stdout.write(f"From: {decode_and_join(from_header)}\n")
            if date_header:
                sys.stdout.write(f"Date: {date_header}\n")

            sys.stdout.write("\n")

            text_content = ""
            if message.is_multipart():

                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        _process_payload(part.get_payload(decode=True), "text/plain", part.get_charset())
                        break  # Prefer plain text

            else:
                content_type = message.get_content_type()
                payload = message.get_payload(decode=True)
                _process_payload(payload, content_type, message.get_charset())

            sys.stdout.write("\n---\n")  # Separator for easier reading

    except FileNotFoundError:
        sys.stderr.write(f"Error: File not found at {mbox_path}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An error occurred: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sanitize an mbox archive and output the text content to stdout.")
    parser.add_argument("mbox_file", help="Path to the mbox archive file.")
    args = parser.parse_args()

    sanitize_mbox_stream(args.mbox_file)
