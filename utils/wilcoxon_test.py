#!/usr/bin/env python3

import argparse
import pathlib
import scipy
from scipy.stats import wilcoxon
import numpy as np


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ikjMatrix multiplication")
    parser.add_argument("input",
                        metavar="INPUT",
                        help="input file",
                        type=pathlib.Path
                        )
    args = parser.parse_args()

    # load the data with NumPy function loadtxt
    data = np.loadtxt(args.input)
    w, p = wilcoxon(data)

    exit(0)
