#!/usr/bin/env python3

import re
import os
import sys
import csv
import tqdm
import pathlib
import argparse
import subprocess

SPECIAL_SOURCES = [
'other-empty',
'other-search',
'other-internal',
'other-external'
'other-other'
]

OUTPUT_HEADER = [
'link_title',
'link_id',
'click_count'
]

# sanitize regex
sanre01 = re.compile(r'[\\/:&\*\?"<>\|\x01-\x1F\x7F]')
sanre02 = re.compile(r'^\(nul\|prn\|con\|lpt[0-9]\|com[0-9]\|aux\)\(\.\|$\)',
                     re.IGNORECASE)
sanre03 = re.compile(r'^\.*$')
sanre04 = re.compile(r'^$')

def sanitize(filename: str) -> str:
    res = sanre01.sub('', filename)
    res = sanre02.sub('', res)
    res = sanre03.sub('', res)
    res = sanre04.sub('', res)

    return res


# Processing non-UTF-8 Posix filenames using Python pathlib?
# https://stackoverflow.com/a/45724695/2377454
def safe_path(path: pathlib.Path) -> pathlib.Path:
    encoded_path = path.as_posix().encode('utf-8')
    return pathlib.Path(os.fsdecode(encoded_path))


# How to get line count cheaply in Python?
# https://stackoverflow.com/a/45334571/2377454
def count_file_lines(file_path: pathlib.Path) -> int:
    """
    Counts the number of lines in a file using wc utility.
    :param file_path: path to file
    :return: int, no of lines
    """

    num = subprocess.check_output(
        ['wc', '-l', safe_path(file_path).as_posix()])
    num = num.decode('utf-8').strip().split(' ')
    return int(num[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract clickstream data.')

    parser.add_argument('CLICKSTREAM_FILE',
                        type=pathlib.Path,  
                        help='Clickstream file.'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Snapshot file.'
                        )
    parser.add_argument('-t', '--titles',
                        type=pathlib.Path,
                        required=True,
                        help='Titles file.'
                        )

    args = parser.parse_args()

    print('* Read the "titles" file: ', file=sys.stderr)
    titles = set()
    titles_files = args.titles
    titleslen = count_file_lines(titles_files)
    with tqdm.tqdm(total=titleslen) as pbar:
        with safe_path(titles_files).open('r', encoding='utf-8') as titlesfp:
            reader = csv.reader(titlesfp, delimiter='\t')
            for line in reader:
                titles.add(line[0])
                pbar.update()

    print('len(titles): {}'.format(len(titles)), file=sys.stderr)

    print('* Read the "snapshot" file: ', file=sys.stderr)
    snapshot_file = args.snapshot
    snaplen = count_file_lines(snapshot_file)
    title2id = dict()
    with tqdm.tqdm(total=snaplen) as pbar:
        with safe_path(snapshot_file).open('r', encoding='utf-8') as snapfp:
            reader = csv.reader(snapfp, delimiter='\t')
            for l in reader:
                page_title = l[1].replace(' ', '_')
                page_id = int(l[0])
                title2id[page_title] = page_id
                pbar.update(1)

    print('* Read the "clickstream" file: ', file=sys.stderr)
    clickstream_file = args.CLICKSTREAM_FILE
    cslen = count_file_lines(clickstream_file)
    with tqdm.tqdm(total=cslen) as pbar:
        with safe_path(clickstream_file).open('r', encoding='utf-8') as csfp:
            reader = csv.reader(csfp, delimiter='\t')
            for line in reader:
                pbar.update()
                if line[0] in SPECIAL_SOURCES:
                    continue
                else:
                    source_title = line[0]
                    target_title = line[1]
                    link_type = line[2]
                    click_count = int(line[3])

                    if link_type == 'link' and \
                            source_title in titles:

                        if title2id.get(target_title, None) is None:
                            # import ipdb; ipdb.set_trace()
                            print('Error: "{}" not found'.format(target_title))
                            continue
                        else:
                            target_id = title2id[target_title]

                        outfile = pathlib.Path(
                            'enwiki.comparison.{}.clickstream.txt'
                            .format(sanitize(source_title))
                            )
                        with safe_path(outfile).open('a+', encoding='utf-8') \
                                as outfp:
                            writer = csv.writer(outfp, delimiter='\t')

                            # new file, write header
                            if outfp.tell() == 0:
                                writer.writerow(OUTPUT_HEADER)


                            writer.writerow((target_title.replace('_', ' '),
                                             target_id,
                                             click_count
                                             )
                                            )



    exit(0)
