from feedserver.models.feed import Feed

__author__ = 'sis13'
import unittest
import Queue
import threading
import feedserver

from feedserver import feedreader
from feedserver.database import db_session


class TestFeedreader(unittest.TestCase):

    def setUp(self):
        self.feed_q = Queue.Queue()
        self.error_q = Queue.Queue()
        self.result_q = Queue.Queue()
        self.feed_url = "http://downgoat.net/feed/"
        self.feed_url_bad = "http://asfdysdhfsjdkfksdfgusdfugshyudf.no/asd/feed/"  # I hope nobody buys this domain...
        self.feed_url_malformed = "http://acme.com"

        self.pool = [feedreader.ReaderThread(self.feed_q, self.result_q, self.error_q) for x in range(1)]

        for t in self.pool:
            t.start()

    def test_feed_requester(self):
        data = feedreader.feed_requester(self.feed_url)

        self.assertTrue(data[0] == self.feed_url and data[1][0].get("title") is not None)

    def test_thread(self):
        self.feed_q.put(self.feed_url)

        result = self.result_q.get()

        self.assertIsNotNone(result[0].get("title"))

    def test_offline(self):
        self.feed_q.put(self.feed_url_bad)

        result = self.error_q.get()

        self.assertEqual(result, self.feed_url_bad)

    def test_malformed(self):
        self.feed_q.put(self.feed_url_malformed)

        result = self.error_q.get()

        self.assertEqual(result, self.feed_url_malformed)


    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
