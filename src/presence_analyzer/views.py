# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import make_response
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    group_by_weekday_start_end
)

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

AVAILABLE_TEMPLATES = (
    'mean_time_weekday',
    'presence_weekday',
    'presence_start_end',
)


@app.route('/')
@app.route('/<string:template_name>', methods=['GET'])
def templateview(template_name='presence_weekday'):
    """
    Render templates make response when page doesn't exist
    """
    try:
        if template_name in AVAILABLE_TEMPLATES:
            return render_template(template_name+'.html')
        else:
            raise TopLevelLookupException
    except TopLevelLookupException:
        return make_response('Page does not exist', 404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
            for i in data.keys()]


@app.route('/api/v1/mean_time_weekday/', methods=['GET'])
@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id=None):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/', methods=['GET'])
@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id=None):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/', methods=['GET'])
@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id=None):
    """
    Returns start and end time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday_start_end(data[user_id])
    result = [
        (
            calendar.day_abbr[weekday],
            mean(mean_per_day['start']),
            mean(mean_per_day['end']),
        )
        for weekday, mean_per_day in weekdays.items()
    ]

    return result
