#!/usr/bin/env python3

import re
import sys
import csv
import argparse
import pathlib

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    description='Map wikipedia page ids to page titles.')

    parser.add_argument('FILE',
                        type=pathlib.Path,
                        help='File with degrees and ids to map'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )
    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='Output file name.'
                        )

    args = parser.parse_args()

    snapshotname = args.snapshot
    id2title = {}
    title2id = {}
    with snapshotname.open('r') as snapshotfile:
        reader = csv.reader(snapshotfile, delimiter='\t')
        for l in reader:
            pageid = int(l[0])
            title = l[1]
            id2title[pageid] = title
            title2id[title] = pageid

    output = pathlib.Path('degree_map.output.dat')
    if args.output is not None:
        output = args.output

    outfile = output.open('w+')
    infile = args.FILE.open('r')

    with outfile as ofp:
        writer = csv.writer(ofp, delimiter='\t')
        for line in infile:
            data = line.strip().split()
            count = int(data[0])
            pageid = int(data[1])
            writer.writerow((count, id2title[pageid]))

    exit(0)