#!/usr/bin/env python3

import csv
import argparse
import pathlib
import scipy
from scipy.stats import wilcoxon, normaltest, ttest_1samp, ttest_ind
import numpy as np


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Wilcoxon test for Clickstream"
        )
    parser.add_argument("input",
                        metavar="INPUT",
                        help="input file",
                        type=pathlib.Path
                        )

    args = parser.parse_args()

    with args.input.open('r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        res_algo = []
        res_cyclerank = []
        for row in reader:
            # print(row)
            try:
                tau_algo = float(row[0])
                tau_cyclerank = float(row[1])
                res_algo.append(tau_algo)
                res_cyclerank.append(tau_cyclerank)
            except:
                # print('.', end='')
                pass

    # load the data with NumPy function loadtxt
    data_algo = np.array(res_algo)
    data_cyclerank = np.array(res_cyclerank)

    # normality test
    nt, p_nt = normaltest(data_algo-data_cyclerank)
    print('normality test: {} (p-value: {})'.format(nt, p_nt))

    # normality test
    tt, p_tt = ttest_ind(data_algo, data_cyclerank)
    print('t-tests test: {} (p-value: {})'
          .format(tt, p_tt))

    # wilcoxon test
    w, p_w = wilcoxon(data_algo, data_cyclerank)
    n = len(data_algo)
    sigma_w = np.sqrt(n*(n+1)*(2*n+1))
    zscore_w = w/sigma_w
    print('wilcoxon test (z-score): {} (p-value: {})'
          .format(zscore_w, p_w))

    exit(0)
