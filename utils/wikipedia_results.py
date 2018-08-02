#!/usr/bin/env python3

import sys
import csv
import re
import argparse
import pathlib
import itertools


REGEX_SCORE = r'score\([0-9]+\): (.*)'
REGEX_PAGEID = r'score\(([0-9]+)\): .*'

regex_score = re.compile(REGEX_SCORE)
regex_pageid = re.compile(REGEX_PAGEID)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a clique graph of '
                                                 'the given dimension.')

    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='max lenght of the loop [default: K].')

    args = parser.parse_args()

    snapshotname = args.snapshot

    with snapshotname.open('r') as snapshotfile:
        reader = csv.reader(snapshotfile, delimiter='\t')
        snapshot = dict((int(l[0]), l[1]) for l in reader)

    try:
        for line in sys.stdin:
            pageid = int(regex_pageid.match(line).group(1))
            score = float(regex_score.match(line).group(1))
            page = snapshot[pageid]

            outline = 'score({page}): {score}\n'.format(page=page,
                                                        score=repr(score)
                                                        )
            sys.stdout.write(outline)
    except IOError as err:
        if err.errno == errno.EPIPE:
            pass


    exit(0)
