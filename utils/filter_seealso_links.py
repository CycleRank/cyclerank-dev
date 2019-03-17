#!/usr/bin/env python3

import sys
import csv
import tqdm
import pathlib
import argparse
import subprocess
from collections import defaultdict


# Create (sane/safe) filename from any (unsafe) string
# https://stackoverflow.com/a/7406369/2377454
def safe_filename(filename):
 eliminate_chars = ('/')
 return "".join(c for c in filename
                if c not in eliminate_chars).rstrip()


def normalize_title(title):
    norm_title = title[0].upper() + title[1:]
    norm_title = norm_title.replace('_', ' ')
    norm_title = ' '.join(norm_title.split())

    return norm_title


# How to get line count cheaply in Python?
# https://stackoverflow.com/a/45334571/2377454
def count_file_lines(file_path):
    """
    Counts the number of lines in a file using wc utility.
    :param file_path: path to file
    :return: int, no of lines
    """
    num = subprocess.check_output(['wc', '-l', file_path])
    num = num.decode('utf-8').strip().split(' ')
    return int(num[0])


def get_header(afile):
    with afile.open('r') as fp:
        reader = csv.reader(fp)
        header = next(reader)

    return header


FILTER_HEADER = ('page_title', 'page_id')
SNAPSHOT_HEADER = ('page_id', 'page_title')
OUTFILE_HEADER = ('link_title', 'link_id')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract "See also" links ids for a list of pages.')
    parser.add_argument('SEEALSO',
                        type=pathlib.Path,
                        help='File with "See also" data.'
                        )
    parser.add_argument('-m', '--id-map',
                        type=pathlib.Path,
                        required=True,
                        help='File with id map.'
                        )
    parser.add_argument('-f', '--filter-list',
                        type=pathlib.Path,
                        required=True,
                        help='File with page titles and ids to filter.'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='File with (new) page ids and page titles, '
                             'i.e., snapshot.'
                        )

    args = parser.parse_args()

    seealso_file = args.SEEALSO
    filter_file = args.filter_list
    idmap_file = args.id_map
    snapshot_file = args.snapshot


    print('* Read the "map" file: ', file=sys.stderr)
    idmap_o2n = dict()
    maplen = count_file_lines(idmap_file)
    with tqdm.tqdm(total=maplen) as pbar:
        with idmap_file.open('r') as mapfp:
            mapreader = csv.reader(mapfp, delimiter=' ')
            next(mapreader)
            pbar.update(1)

            for data in mapreader:
                oldid = int(data[0])
                newid = int(data[1])

                idmap_o2n[oldid] = newid
                pbar.update(1)


    print('* Read the "snapshot" file: ', file=sys.stderr)
    snap_id2title = dict()
    snap_title2id = dict()
    snaplen = count_file_lines(snapshot_file)
    with tqdm.tqdm(total=snaplen) as pbar:
        with snapshot_file.open('r') as snapfp:
            snapreader = csv.DictReader(snapfp,
                                        fieldnames=SNAPSHOT_HEADER,
                                        delimiter='\t')
            for data in snapreader:
                page_id = int(data['page_id'])
                page_title = data['page_title']

                snap_id2title[page_id] = page_title
                snap_title2id[page_title] = page_id

                pbar.update(1)


    print('* Read the "filter" file: ', file=sys.stderr)
    filter_newids = set()
    flen = count_file_lines(filter_file)
    with tqdm.tqdm(total=flen) as pbar:
        with filter_file.open('r') as ffp:
            freader = csv.DictReader(ffp,
                                     fieldnames=FILTER_HEADER,
                                     delimiter='\t')       
            for data in freader:
                page_id = int(data['page_id'])
                filter_newids.add(page_id)

                pbar.update(1)

    print('* Read the "See also" file: ', file=sys.stderr)
    saheader = get_header(seealso_file)

    seealso_links = defaultdict(list)
    salen = count_file_lines(seealso_file)
    with tqdm.tqdm(total=salen) as pbar:
        with seealso_file.open('r') as safp:
            sareader = csv.DictReader(safp, fieldnames=saheader)

            # discard header
            next(sareader)
            pbar.update(1)

            for data in sareader:
                seealso_page_oldid = int(data['page_id'])

                if not data['wikilink.link']:
                    continue

                link_title = normalize_title(data['wikilink.link'])

                if not link_title:
                    import ipdb; ipdb.set_trace()

                is_active = True if int(data['wikinlink.is_active']) == 1 \
                                 else False

                seealso_page_newid = idmap_o2n[seealso_page_oldid]

                if is_active and seealso_page_newid in filter_newids:
                    try:
                        link_id = snap_title2id[link_title]
                    except KeyError:
                        import ipdb; ipdb.set_trace()
                    (seealso_links[seealso_page_newid]
                     .append((link_id, link_title))
                     )

                pbar.update(1)

    for sa_newid, link_list in seealso_links.items():
        sa_title = snap_id2title[sa_newid]

        safe_title = safe_filename(sa_title.replace(' ', '_'))
        outfile = ('{lang}.comparison.{title}.seealso.txt'
                   .format(lang='enwiki',
                           title=safe_title)
                   )
        with open(outfile, 'w+') as outfp:
            writer = csv.writer(outfp, delimiter='\t')
            writer.writerow(OUTFILE_HEADER)
            for link_id, link_title in link_list:
                writer.writerow((link_title, link_id))

    exit(0)