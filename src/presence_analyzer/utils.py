# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import urllib2

import time
import threading
from lxml import etree
from json import dumps
from functools import wraps
from datetime import datetime

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

CACHE = {}
TIMESTAMPS = {}


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def memoize(key, validity_peroid):
    """
    Memorizing decorator. Returning cached data
    if its validity period is not expired
    """
    def _decorating_wrapper(function):
        @wraps(function)
        def _caching_wrapper(*args, **kwargs):
            cache_key = key
            now = time.time()

            if TIMESTAMPS.get(cache_key, now) > now:
                return CACHE[cache_key]

            result = function(*args, **kwargs)
            CACHE[cache_key] = result
            TIMESTAMPS[cache_key] = now + validity_peroid
            return result
        return _caching_wrapper
    return _decorating_wrapper


def locker(function):
    """
    Global thread locking decorator.
    """
    function.__lock__ = threading.Lock()

    @wraps(function)
    def _lock_wrapper(*args, **kwargs):
        with function.__lock__:
            result = function(*args, **kwargs)
        return result
    return _lock_wrapper


@locker
@memoize('get_data', 600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def get_data_from_xml():
    """
    Extracts personal data and server adress from XML file
    """
    data = {}
    with open(app.config['DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        root = tree.getroot()
        config = root[0]
        server = {
            u'host': unicode(config.findtext('host')),
            u'protocol': unicode(config.findtext('protocol')),
        }
        data['server'] = "%(protocol)s://%(host)s" % server
        users = root[1]
        data['users'] = [
            {
                u'id': int(user.attrib['id']),
                u'name': unicode(user.findtext('name')),
                u'avatar': unicode(user.findtext('avatar'))
            }
            for user in users
        ]

        return data


def get_xml():
    """
    Download xml user data file from server and
    save it  in runtime/data directory.
    """
    response = urllib2.urlopen(app.config['XML_URL'])
    with open(app.config['DATA_XML'], 'wb') as xmlfile:
        while True:
            chunk = response.read(16 * 1024)
            if not chunk:
                break
            xmlfile.write(chunk)


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_by_weekday_start_end(items):
    """
    Groups presence entries by weekday start end.
    """
    result = {
        i: {
            'start': [],
            'end': [],
        }
        for i in range(7)
    }
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(
            seconds_since_midnight(start)
        )
        result[date.weekday()]['end'].append(
            seconds_since_midnight(end)
        )
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
