#!/usr/bin/env python3

import sys
import csv
import re
import argparse
import pathlib
from collections import defaultdict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a clique graph of '
                                                 'the given dimension.')

    parser.add_argument('FILE',
                        type=pathlib.Path,
                        help='Input file.')

    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='output file name [default: stdout].')

    parser.add_argument('-k', '--maxloop',
                        type=int,
                        dest='K',
                        help='Limit loops to this length (K) '
                             '[default: No limit].')

    args = parser.parse_args()

    infile = args.FILE
    output = args.output
    K = args.K

    scores = defaultdict(float)
    with infile.open('r') as infp:
        reader = csv.reader(infp, delimiter=' ')

        for cycle in reader:
            csize = len(cycle)
            if K is not None and csize > K: continue

            cycle = [int(node) for node in cycle]

            for node in cycle:
                scores[node] += 1.0/csize

    outfile = None
    if output is None:
        outfile = sys.stdout
    else:
        outfile = output.open('w+')

    for nid, score in sorted(scores.items()):
        outfile.write("score({}): {}\n".format(nid, score))

    exit(0)
