import re
import csv
import logging
import os


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
    """
    num_target_words = 0
    matched_words = []
    for token in list_of_target_words:  # Goes through the tokens in the list
        regex = re.compile(".*({}).*".format(token))
        # found_what = [m.group(0) for l in list_of_target_words for m in [regex.search(l)] if m]
        found_what = [m.group(1) for l in list_of_tokens for m in [regex.search(l)] if m]
        if len(found_what) > 0:  # For each one it checks if it is in the target list
            num_target_words = len(found_what)
            matched_words.append((token, num_target_words))
    return num_target_words, matched_words  # Note that we are returning a tuple (2 values)


def write_csv(output_file, keywords_header, keywords_x_freqs):
    """Write a CSV file in the format url, <keyword1>, <keyword2>, <keyword3>, ...
    output_file - the name of created CSV file
    keywords_header - list with all the keywords to create header row of CSV
    keywords_x_freqs - dictionary list with keywords and frequencies
    return boolean
    """
    try:
        if os.path.exists(output_file):
            append_write = 'a'  # append if already exists
        else:
            append_write = 'w'  # make a new file if not

        with open(output_file, append_write) as f:
            # Using dictionary keys as fieldnames for the CSV file header
            writer = csv.DictWriter(f, keywords_header)
            if append_write == 'w':
                writer.writeheader()

            for d in keywords_x_freqs:
                writer.writerow(d)
        return True
    except Exception as e:
        logging.error('Something bad happend while writing CSV:' + str(e))
        return False
