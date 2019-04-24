#!/usr/bin/env python3

import argparse
import pathlib
from itertools import groupby


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("file",
                        type=pathlib.Path,
                        help='Input file.')

    args = parser.parse_args()

    with args.file.open('r') as infile:
        loops = []
        for line in infile.readlines():
            data = [int(el) for el in line.strip().split()]
            loops.append(data)

    loopslen = [len(loop) for loop in loops]

    # How to count the frequency of the elements in a list?
    # https://stackoverflow.com/a/55437321/2377454
    results = {value: len(list(freq))
               for value, freq in groupby(sorted(loopslen))}


    print('{two}\t{three}\t{four}\t{file}'
          .format(two=results.get(2, 0),
                  three=results.get(3, 0),
                  four=results.get(4, 0),
                  file=args.file
                  )
          )
    exit(0)
