#!/usr/bin/env python3

import argparse
import pathlib
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a clique graph of '
                                                 'the given dimension.')
    parser.add_argument('K',
                        metavar='<dimension>',
                        type=int,
                        help='dimension of the clique to generate.')

    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='output file name [default: stdout]')

    parser.add_argument('-l', '--lenght',
                        type=int,
                        help='max lenght of the loop.')

    parser.add_argument('-s', '--start',
                        type=int,
                        help='starting node for pageloop algorithm.')

    args = parser.parse_args()

    # import ipdb; ipdb.set_trace()

    K = args.K
    output = args.output
    start = args.start
    lenght = args.lenght
    edges = K**2-K

    outfile = None
    if output is None:
        outfile = sys.stdout
    else:
        outfile = open(output, 'w+')

    if start and length:
        outfile.write("{nodes} {edges} {start} {lenght}\n"
              .format(nodes=K, edges=edges, start=start, lenght=lenght))
    else:
        outfile.write("{nodes} {edges}\n".format(nodes=K, edges=edges))


    for i in range(K):
        for j in range(K):
            if j == i: continue
            outfile.write("{} {}\n".format(i, j))

    exit(0)
