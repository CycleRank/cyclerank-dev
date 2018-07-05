#!/usr/bin/env python3

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a clique graph of '
                                                 'the given dimension.')
    parser.add_argument('K',
                        metavar='<dimension>',
                        type=int,
                        help='dimension of the clique to generate.')

    parser.add_argument('-s', '--start',
                        type=int,
                        help='starting node for pageloop algorithm.')

    parser.add_argument('-l', '--lenght',
                        type=int,
                        help='max lenght of the loop.')


    args = parser.parse_args()

    K = args.K
    start = args.start
    lenght = args.lenght

    print("{nodes} {edges} {start} {lenght}"
          .format(nodes=K, edges=K**2-K, start=start, lenght=lenght))

    for i in range(K):
        for j in range(K):
            if j == i: continue
            print("{} {}".format(i, j))

    exit(0)
