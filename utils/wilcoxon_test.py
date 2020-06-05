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
    parser.add_argument("--t-test-mean",
                        help="Value of the t-test 1-sample mean",
                        dest='tt_mean',
                        default=0.0,
                        type=float
                        )

    args = parser.parse_args()

    # load the data with NumPy function loadtxt
    data = np.loadtxt(args.input)

    # normality test
    nt, p_nt = normaltest(data)
    print('normality test: {} (p-value: {})'.format(nt, p_nt))

    # normality test
    tt, p_tt = ttest_1samp(data, args.tt_mean)
    print('t-tests test (mean: {}): {} (p-value: {})'
          .format(args.tt_mean, tt, p_tt))

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
