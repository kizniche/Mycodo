# -*- coding: utf-8 -*-
# Checks if the version of Python installed is greater than the version being tested

import argparse
import sys


def parseargs(parser):
    parser.add_argument('--version', metavar='VERSION', type=str,
                        help='Python version to test against (e.g. "3.6")',
                        required=True)
    return parser.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tests Python version")
    args = parseargs(parser)

    try:
        version_major = int(args.version.split('.')[0])
        version_minor = int(args.version.split('.')[1])

        if not sys.version_info.major >= version_major:
            sys.exit(1)
        if not sys.version_info.minor >= version_minor:
            sys.exit(1)
    except:
        sys.exit(1)
