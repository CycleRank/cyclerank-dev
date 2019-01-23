#!/usr/bin/env python3

import sys
import csv
import re
import argparse
import pathlib
import itertools


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Filter Wikipedia networks from a list of ids.')

    parser.add_argument('GRAPH',
                        type=pathlib.Path,
                        help='Graph file.')
    parser.add_argument('-d', '--delimiter',
                        type=str,
                        default='\t',
                        help='output file name [default: stdout].')
    parser.add_argument('--skip-header',
                        action='store_true',
                        help='Skip graph file header.')

    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='output file name [default: stdout].')

    parser.add_argument('--match-titles',
                        action='store_true',
                        help='Match page titles instead of ids.')

    parser.add_argument('-k', '--maxloop',
                        type=int,
                        dest='K',
                        help='Limit cycles to this length (K) '
                             '[default: No limit].')

    parser.add_argument('-f', '--filter',
                        type=pathlib.Path,
                        required=True,
                        help='Filter file (with ids, pageloop cycles or page '
                             'titles).')
    parser.add_argument('--filter-delimiter',
                        type=str,
                        default=' ',
                        help="Filter file delimiter [default: ' '].")

    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )
    parser.add_argument('--snapshot-delimiter',
                        type=str,
                        default='\t',
                        help="Wikipedia snapshot delimiter [default: ' ']."
                        )

    parser.add_argument('--map',
                        type=pathlib.Path,
                        help="Map new ids to old ids."
                        )


    args = parser.parse_args()
    print(args)

    graphfile = args.GRAPH
    filterfile = args.filter
    snapshot = args.snapshot
    mapo2n = args.map
    K = args.K
    output = args.output

    with graphfile.open('r') as graphfp:
        reader = csv.reader(graphfp, delimiter=args.delimiter)
        if args.skip_header:
            next(reader)
        foo = [_ for _ in reader]
        import ipdb; ipdb.set_trace()

    ids = set()
    titles = set()
    with filterfile.open('r') as filterfp:
        reader = csv.reader(filterfp, delimiter=args.filter_delimiter)
        if args.match_titles:
            titles = set([title for title
                          in itertools.chain.from_iterable([_ for _ in reader])
                          ])
        else:
            ids = set([int(idx) for idx
                       in itertools.chain.from_iterable([_ for _ in reader])
                       ])

    snapshotdict = dict()
    with snapshot.open('r') as snapfp:
        reader = csv.reader(snapfp, delimiter=args.snapshot_delimiter)
        snapshotdict = dict([(int(line[0]), line[1]) 
                             for line in reader])

    import ipdb; ipdb.set_trace()

    exit(0)
