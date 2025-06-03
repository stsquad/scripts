#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Clean an mbox archive, like we get from lore.kernel.org
#
# (C)opyright 2025 Alex Bennée
#
# The archive rightly contains a bunch of metadata and alternative
# copies of patches. But really we just want the basic facts of the
# thread.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import argparse
import mailbox
import re
import sys
from email.header import decode_header
from html.parser import HTMLParser

# Define the arguments
parser = argparse.ArgumentParser(
    description="Sanitize an mbox archive and output the text content to stdout."
)
parser.add_argument("mbox_file", help="Path to the mbox archive file.")


class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


def decode_header_field(header):
    """Decode email header field handling encoding properly."""
    if not header:
        return ""

    try:
        decoded_parts = decode_header(header)
        parts = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                parts.append(str(part))
        return "".join(parts)
    except Exception as e:
        print(f"Warning: Error decoding header: {e}", file=sys.stderr)
        return str(header)


def strip_html(html_content):
    """Remove HTML tags from content."""
    stripper = HTMLStripper()
    try:
        stripper.feed(html_content)
        return stripper.get_text()
    except Exception:
        # Fallback to regex if HTML parser fails
        return re.sub(r'<[^>]+>', '', html_content)


def process_message_content(message):
    """Extract and return the text content of a message."""
    content_parts = []

    if message.is_multipart():
        # Look for text/plain first, fall back to text/html
        plain_text = None
        html_text = None

        for part in message.walk():
            if part.get_content_type() == "text/plain" and not plain_text:
                payload = part.get_payload(decode=True)
                if payload:
                    plain_text = payload.decode(part.get_charset() or 'utf-8', errors='replace')
            elif part.get_content_type() == "text/html" and not html_text:
                payload = part.get_payload(decode=True)
                if payload:
                    html_text = payload.decode(part.get_charset() or 'utf-8', errors='replace')

        content_parts.append(plain_text or strip_html(html_text or ""))
    else:
        # Single part message
        payload = message.get_payload(decode=True)
        if payload:
            text = payload.decode(message.get_charset() or 'utf-8', errors='replace')
            if message.get_content_type() == "text/html":
                text = strip_html(text)
            content_parts.append(text)

    return ''.join(filter(None, content_parts))


def sanitize_mbox_stream(mbox_path):
    """Process mbox file and output cleaned content."""
    try:
        mbox = mailbox.mbox(mbox_path)

        for message in mbox:
            # Decode headers consistently
            subject = decode_header_field(message.get('Subject'))
            from_addr = decode_header_field(message.get('From'))
            date = decode_header_field(message.get('Date'))

            # Print headers
            if subject:
                print(f"Subject: {subject}")
            if from_addr:
                print(f"From: {from_addr}")
            if date:
                print(f"Date: {date}")

            print()  # Blank line after headers

            # Process and print content
            content = process_message_content(message)
            if content.strip():  # Only print if there's actual content
                print(content.rstrip())

            print("---")  # Message separator

    except FileNotFoundError:
        print(f"Error: File not found at {mbox_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    args = parser.parse_args()

    sanitize_mbox_stream(args.mbox_file)
