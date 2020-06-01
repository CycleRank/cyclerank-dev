#!/usr/bin/env python3

import argparse
import pathlib
import scipy
from scipy.stats import wilcoxon, normaltest, ttest_1samp
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

    # normality test
    nt, p_nt = normaltest(data)
    print('normality test: {} (p-value: {})'.format(nt, p_nt))

    # normality test
    tt, p_tt = ttest_1samp(data, 0.05)
    print('t-tests test (mean: 0.0): {} (p-value: {})'.format(tt, p_tt))

    # wilcoxon test
    w, p_w = wilcoxon(data)
    n = len(data)
    sigma_w = np.sqrt(n*(n+1)*(2*n+1))
    zscore_w = w/sigma_w
    print('wilcoxon test (z-score): {} (p-value: {})'
          .format(zscore_w, p_w))

    # mean and standard deviation
    mu = np.mean(data)
    sigma = np.std(data)
    print('mu: {mu} sigma: {sigma}'.format(mu=mu,sigma=sigma))


    exit(0)
