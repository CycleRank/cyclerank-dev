#!/usr/bin/env python3

import sys
import csv
import pathlib
import argparse

INPUT_FILENAME = 'enwiki.{algo}.{title}.2018-03-01.compare_lr-pr.txt'
COMPARISON_FILE_HEADER = ('pos', 'title', 'page_id', 'score')


def read_comparison_file(algo, title, comparison_dir):
    input_filename = INPUT_FILENAME.format(algo=algo, title=title)
    input_file = comparison_dir/input_filename


    links = {}
    with input_file.open('r') as infp:
        reader = csv.reader(infp, delimiter='\t')

        # ['5', 'Bijbehara railway station', '11119524', '2.41667']
        for line in reader:
            data = dict()
            data['pos'] = int(line[0])
            data['title'] = line[1]
            data['score'] = float(line[3])

            page_id = int(line[2])

            links[page_id] = data

    return links


def compute_score(links):
    pos = 0
    score = 0.0
    title = ''
    try:
        pos = links[lid]['pos']
        title = links[lid]['title']
    except KeyError:
        pass

    try:
        score = 1.0/pos
    except ZeroDivisionError:
        score = 0.0

    return score, title


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute comparison score between LR and SSPPR.')
    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with page titles '
                             '[default: read from stdin].'
                        )
    parser.add_argument('--comparison-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='File with page titles '
                             '[default: read from stdin].'
                        )
    args = parser.parse_args()
    comparison_dir = args.comparison_dir

    print('* Read input. ', file=sys.stderr)
    infile = None
    if args.input:
        infile = args.input.open('r')
    else:
        infile = sys.stdin

    titles = [_.strip() for _ in infile.readlines()]

    print('* Processing titles: ', file=sys.stderr)
    for title in titles:
        score = 0.0
        links_lr = {}
        links_ssppr = {}
        scores = dict()
        print('-'*80)
        print('    - {}'.format(title), file=sys.stderr)

        links_lr = read_comparison_file('looprank',
                                        title,
                                        comparison_dir
                                        )

        links_ssppr = read_comparison_file('ssppr',
                                           title,
                                           comparison_dir
                                           )


        links_set = set(links_lr.keys()).union(set(links_ssppr.keys()))
        for lid in links_set:
            score_lr, title_lr = compute_score(links_lr)
            score_ssppr, title_ssppr = compute_score(links_ssppr)

            score_link = score_lr - score_ssppr
            score += score_link

            title = title_lr if title_lr else title_ssppr
            scores[title] = score_link


        outfile = ('enwiki.{title}.2018-03-01.compare_lr-pr.scores.txt'
                   .format(title=title.replace(' ', '_')))
        with open(outfile, 'w+') as outfp:
            writer = csv.writer(outfp, delimiter='\t')
            writer.writerow((score,))
            for link_title in scores:
                writer.writerow((scores[link_title], link_title))

    exit(0)
