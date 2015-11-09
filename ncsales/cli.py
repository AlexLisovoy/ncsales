#!/usr/bin/env python3.5

"""A simple console tool, which calculate scores for sales leads."""

import argparse
import logging
import os
import csv
from collections import defaultdict

__all__ = ('EVENT_TYPES', 'EVENT_FACTORS', 'QUARTILE_LABELS', 'process_file')


logger = logging.getLogger(__name__)

# constants
EVENT_TYPES = ('web', 'email', 'social', 'webinar')
EVENT_FACTORS = (
    ('web', 1.0),
    ('email', 1.2),
    ('social', 1.5),
    ('webinar', 2.0),
)
QUARTILE_LABELS = (
    ('platinum', (75, 100)),
    ('gold', (50, 74)),
    ('silver', (25, 49)),
    ('bronze', (0, 24)),
)


class ValidationError(Exception):
    """Base class for validation row errors."""


def get_data(the_file):
    """
    Returns generator by rows of the file.

    Args:
        the_file (str): path to file

    Returns:
        generator: generator by rows of the file or None if the file
                   is malformed (doesn't exist, bad perms or empty
    """
    if not os.path.exists(the_file):
        logger.error('The file does not exist: %s', the_file)
        return

    if not os.access(the_file, os.R_OK):
        logger.error('Bad file permissions: %s', the_file)
        return

    with open(the_file) as csv_file:
        # determine the format of CSV file
        try:
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
        except csv.Error:
            logger.exception('Could not determine csv dialect')
            return

        csv_file.seek(0)
        yield from csv.reader(csv_file, dialect)


def parse_row(row):
    """
    Extracts the necessary data from the row of file

    Args:
        the_file (str): path to file

    Returns:
        list: Returns list with data:
               contact_id(int), event_type(str), score(float).

    Raises:
        ValidationError: raise exceptions if:
                           - row doesn't contain 3 items
                           - contact id can't convert to int
                           - unknown event type
                           - score can't convert to float
    """
    if len(row) < 3:
        raise ValidationError('Malformed row')

    try:
        row[0] = int(row[0])
    except ValueError:
        raise ValidationError('Bad contact id')

    if row[1] not in EVENT_TYPES:
        raise ValidationError('Unknown event type')

    try:
        row[2] = float(row[2])
    except ValueError:
        raise ValidationError('Bad score')

    return row


def get_quartile_label(score):
    """
    Calculate quartile label by provided score.

    Args:
        score (int): normalized contact score

    Returns:
        str: Returns quartile label or empty string if label
             can't be determined
    """
    for label, scores in dict(QUARTILE_LABELS).items():
        if scores[0] <= score <= scores[1]:
            return label
    else:
        logger.warning('Cannot determine quartile label by score: %s', score)
        return ''


def process_file(the_file):
    """
    The core of application, which implement following algorithm:

        1. Event scores will first be weighted by type as follows
        2. All scores should then be summed by **contact id**.
        3. The summed scores should then be normalized on a scale of 0 to 100.
        4. Finally, the contacts should be labeled by quartile based on the
           normalized score.

    Args:
        score (int): normalized contact score

    Returns:
        generator: in next format: contact_id, quartile_label, normalized_score
    """
    logger.debug('Start processing file: %s', the_file)

    contacts = defaultdict(float)
    factors = dict(EVENT_FACTORS)

    for row in get_data(the_file):
        try:
            contact_id, event_type, score = parse_row(row)
        except ValidationError:
            logger.exception('Invalid row: %s', row)
        else:
            contacts[contact_id] += score * factors[event_type]
    logger.debug('Found contacts with unique id: %s', len(contacts))

    max_score, min_score = None, None
    for score in contacts.values():
        if max_score is None or score > max_score:
            max_score = score

        if min_score is None or score < min_score:
            min_score = score
    logger.debug('Found extreme points: max - %.2f, min - %.2f',
                 max_score, min_score)

    for contact_id, score in contacts.items():
        if max_score == min_score:  # only 1 contact or all scores are equals
            normalized_score = 0
        else:
            normalized_score = int(round(
                (score - min_score) / (max_score - min_score) * 100
            ))
        logger.debug('Normalized score for contact %s: %s(%.2f)',
                     contact_id, normalized_score, score)

        label = get_quartile_label(normalized_score)
        logger.debug('Get label by score %s for contact %s: %s',
                     normalized_score, contact_id, label)
        yield contact_id, label, normalized_score


def main():
    """
    Main program.
    Parse arguments, process file, print report.
    """
    parser = argparse.ArgumentParser(
        description="Scoring engine for sales leads")
    parser.add_argument('filepath', help='Path to csv file with sales data')
    parser.add_argument(
        '-v', '--verbose', action='count', dest='level',
        default=1, help='Verbose logging (repeat for more verbose)')
    parser.add_argument(
        '-q', '--quiet', action='store_const', const=0, dest='level',
        default=1, help='Quiet logging (opposite of --verbose)')

    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels)-1)])

    for contact_id, label, score in process_file(args.filepath):
        print("{}, {}, {}".format(contact_id, label, score))
