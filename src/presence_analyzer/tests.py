# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday(self):
        """
        Test mean presence time of given user.
         """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            data,
            [
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_presence_start_end(self):
        """
        Testing presence start and end
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertListEqual(
            data,
            [
                [u'Mon', 0, 0],
                [u'Tue', 34745.0, 64792.0],
                [u'Wed', 33592.0, 58057.0],
                [u'Thu', 38926.0, 62631.0],
                [u'Fri', 0, 0],
                [u'Sat', 0, 0],
                [u'Sun', 0, 0],
            ],
        )


    def test_api_apesence_weekday(self):
        """
        Test presence weekday.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(
            data,
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_group_by_weekday(self):
        """
        Test grouping by weekdays
        """
        self.assertDictEqual(
            utils.group_by_weekday(utils.get_data()[10]),
            {
                0: [],
                1: [30047],
                2: [24465],
                3: [23705],
                4: [],
                5: [],
                6: [],
            },
        )

    def test_group_start_end_weekday(self):
        """
        Test weekday grouping start end
        """
        data = utils.get_data()
        weekdays = utils.group_by_weekday_start_end(data[11])
        self.assertItemsEqual(weekdays.keys(), range(7))
        self.assertSequenceEqual(weekdays, {
            0: {'start': [33134], 'end': [57257]},
            1: {'start': [33590], 'end': [50154]},
            2: {'start': [33206], 'end': [58527]},
            3: {'start': [37116, 34088], 'end': [60085, 57087]},
            4: {'start': [47816], 'end': [54242]},
            5: {'start': [], 'end': []},
            6: {'start': [], 'end': []},
        })

    def test_seconds_since_midnight(self):
        """
        Test seconds since midnight.
        """
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(12, 00, 00)),
            43200
        )
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(17, 21, 11)),
            62471
        )

    def test_interval(self):
        """
        Test interval function.
        """
        self.assertEqual(
            utils.interval(
                (datetime.time(10, 00, 00)),
                (datetime.time(11, 00, 00)),
            ),
            3600,
        )
        self.assertEqual(
            utils.interval(
                (datetime.time(10, 00, 00)),
                (datetime.time(10, 00, 30)),
            ),
            30,
        )

    def test_mean(self):
        """
        Test if mean function works correctly.
        """
        self.assertEqual(utils.mean([1, 2, 3, 4]), 2.5)
        self.assertEqual(utils.mean([1.11, 2.22, 3.33, 4.1234562]), 2.69586405)
        self.assertEqual(utils.mean([]), 0)


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
