#!/usr/bin/env python
import argparse
import sys
import re
import csv
import logging
import os
import glob
from collections import Counter
import pandas as pd
from tqdm import tqdm


logger = logging.getLogger(__name__)


def main():

    current_working_dir = os.getcwd()  # current directory we are standing on

    # with every run, remove any older result CSVs for the folder
    try:
        os.remove(csv_file_name)
        os.remove(sorted_csv_file_name)
    except FileNotFoundError as e:
        pass

    # given the name of the folder, this gets all the saved page files as
    # a list
    all_txt_files = glob.glob(
        os.path.join(current_working_dir,
                     "{}*/*.*.txt".format(folder_name)),
        recursive=False
    )

    # Not a good sign if list if empty...
    if not all_txt_files:
        logger.error("{}: Folder is empty or does not exist.".
                     format(folder_name))
        sys.exit()

    # read keywords from file into a list
    keywords = get_file_content_as_list(keywords_file)
    # make the keywords lowercase
    keywords = [x.lower() for x in keywords]
    # make keywords dictionary with zero frequency as value
    all_keywords = dict((strip_weights(el)[0], 0) for el in keywords)
    all_keywords_dict = Counter(all_keywords)

    sorted_keywords_list = sorted(all_keywords_dict.items())

    # extract a sorted list of keywords to write as CSV headers
    headers = [str(x) for x, y in sorted_keywords_list]
    # prepend url header onto the keywords list
    headers.insert(0, u'url')
    headers.insert(1, u'frequency_sum')

    pbar = tqdm(total=len(all_txt_files))
    tqdm.write("Found {} files to search. Please wait.".
               format(len(all_txt_files)))

    with open(csv_file_name, 'a+', encoding="utf-8") as f:
        # Using dictionary keys as fieldnames for the CSV file header
        writer = csv.DictWriter(f, headers)
        writer.writeheader()

        for idx, txt_file in enumerate(all_txt_files):
            with open(txt_file) as fp:
                visible_text_list = fp.readlines()
                current_url = visible_text_list[0].strip().rstrip()
                num_digits = len(str(len(all_txt_files)))
                tqdm.write("{0:0{width}d}) Done! {1}".
                           format(idx+1, current_url, width=num_digits))

                visible_text_list = [x.lower() for x in visible_text_list]

                # counts keywords in page
                found_count, found_keywords = count_keywords(
                    visible_text_list,
                    keywords
                )
                found_keywords_as_dict = dict((x, y) for x, y in found_keywords)

                found_keywords_freq_dict = Counter(found_keywords_as_dict)

                all_keywords_dict = Counter(all_keywords)
                # combine both dicts to have uniform dictionary for all pages
                all_keywords_dict.update(found_keywords_freq_dict)
                # after merging, sort the resulting dictionary based on keys to
                # make a tuples list that is always uniform for every page
                sorted_keywords_list = sorted(all_keywords_dict.items())

                # create a sorted dictionary list
                final_csv_dict = []
                final_csv_dict.append({x: y for x, y in sorted_keywords_list})

                # prepend the current URL onto the frequencies dict object
                final_csv_dict[0]['frequency_sum'] = sum(final_csv_dict[0].values())
                final_csv_dict[0]['url'] = current_url

                for d in final_csv_dict:
                    writer.writerow(d)

                pbar.update(1)

    pbar.close()
    sort_csv(csv_file_name, sorted_csv_file_name)


def sort_csv(csv_input, csv_output):
    """Uses pandas to sort the CSV from the highest frequency
    summation to the lowest.
    """
    df = pd.read_csv(csv_input)
    df = df.sort_values(['frequency_sum'], ascending=[0])
    df.to_csv(csv_output, index=False)


def strip_weights(token):
    """Extracts the weights from keywords from the file
    Return keyword and assigned weight if any otherwise default weight one
    """
    try:
        weighted_token = token.split("|", 1)[0].strip()
        token_weight = token.split("|", 1)[1]
    except IndexError as e:  # catch IndexError since no weight is observed
        weighted_token = token.strip()
        token_weight = 1

    return weighted_token, token_weight


def get_file_content_as_list(file_name):
    """Give a filename, open and read the contents into a list
    file_name - file to be opened
    return list of words
    """
    with open(file_name, 'r') as file_name_handle:
        return file_name_handle.read().splitlines()


def count_keywords(list_of_tokens, list_of_target_words):
    """Counts how many instances of the keywords were found
    list_of_tokens - The list of words as haystack
    list_of_target_words - The list of words as needle
    return number of words, list of keywords found

    Inspiration: http://www.cademuir.eu/blog/2011/10/20/python-searching-for-a-string-within-a-list-list-comprehension/
    https://developmentality.wordpress.com/2011/09/22/python-gotcha-word-boundaries-in-regular-expressions/
    """
    num_target_words = 0
    matched_words = []
    for token in list_of_target_words:  # Goes through the tokens in the list
        weighted_token, token_weight = strip_weights(token)

        # regex = re.compile(".*({}).*".format(token)) # does match in-word substrings
        regex = re.compile(".*(\\b{}\\b).*".format(weighted_token)) # match strictly whole words only
        # found_what = [m.group(0) for l in list_of_target_words for m in [regex.search(l)] if m]
        found_what = [m.group(1) for l in list_of_tokens for m in [regex.search(l)] if m]
        if len(found_what) > 0:  # For each one it checks if it is in the target list
            num_target_words = len(found_what)*int(token_weight)
            matched_words.append((weighted_token, num_target_words))
    return num_target_words, matched_words  # Note that we are returning a tuple (2 values)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Generate a sorted CSV file with keyword frequencies'
        ' from scraped web pages.'
    )

    parser.add_argument(
        '-f',
        '--folder',
        dest='folder_name',
        default=None,
        required=True,
        help='Name of directory with scraped pages (mandatory)'
    )
    parser.add_argument(
        '-k',
        '--keywords_file',
        dest='keywords_file',
        default=None,
        required=True,
        help='File with keywords to search for in the directory (mandatory)'
    )

    # these are module global variables and can be access by any function in
    # this module
    args = parser.parse_args()
    folder_name = args.folder_name
    keywords_file = args.keywords_file

    # the output files of all observed keyword frequencies
    csv_file_name = "{}_results.csv".format(folder_name)
    sorted_csv_file_name = "{}_results_sorted.csv".format(folder_name)

    try:
        main()
    except KeyboardInterrupt as e:
        logger.info("Script interrupted by user")
        sort_csv(csv_file_name, sorted_csv_file_name)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
