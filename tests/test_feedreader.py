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
    """
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

        self.assertEqual(result, self.feed_url_malformed)"""

    def test_add_feed(self):
        feeds = [
            "http://cyb3rsleuth.blogspot.com/feeds/posts/default",
            "http://feeds.feedburner.com/TheSecurityLedger",
            "http://www.thegreycorner.com/feeds/posts/default",
            "http://artemonsecurity.blogspot.com/feeds/posts/default",
            "http://www.securelist.com/en/rss/weblog",
            "https://www.securelist.com/en/rss/allupdates",
            "http://siri-urz.blogspot.com/feeds/posts/default",
            "https://community.rapid7.com/community/metasploit/blog/feeds/posts",
            "http://malwareint.blogspot.com/feeds/posts/default",
            "http://malware.dontneedcoffee.com/feeds/posts/default",
            "http://krebsonsecurity.com/feed/atom/",
            "http://www.exposedbotnets.com/feeds/posts/default",
            "https://threatpost.com/en_us/podcasts/feed/all",
            "http://blog.eset.com/feed",
            "http://eromang.zataz.com/feed/",
            "http://freak.no/forum/external.php?type=RSS2",
            "http://www.diskusjon.no/index.php?app=core&amp;module=global&amp;section=rss&amp;type=forums&amp;id=17",
            "http://www.diskusjon.no/index.php?app=core&amp;module=global&amp;section=rss&amp;type=forums&amp;id=1",
            "http://thablawg.net/?feed=rss2",
            "http://www.strategypage.com/index.xml",
            "http://darklordnorge.net/?feed=rss2",
            "http://skepsis.no/blog/?feed=atom",
            "http://downgoat.net/feed/",
            "http://seventhstyle.com/feed/",
            "http://rabbababb.no/feed/",
            "http://www.globalsecurity.org/globalsecurity-org.xml",
            "http://askakorean.blogspot.com/feeds/posts/default",
            "http://www.anandtech.com/rss/",
            "http://aberstudentmedia.com/feed/",
            "http://brown-moses.blogspot.com/feeds/posts/default",
            "http://www.venganza.org/feed/",
            "http://www.vg.no/rss/create.php",
            "http://www.nrk.no/nyheiter/siste.rss",
            "http://www.dagbladet.no/rss/forsida/",
            "http://www.aftenposten.no/rss/?kat=nyheter_uriks",
            "http://www.aftenposten.no/rss/?kat=nyheter_iriks",
            "http://www.theregister.co.uk/headlines.atom",
            "http://rss.slashdot.org/Slashdot/slashdot",
            "http://www.phoronix.com/rss.php",
            "http://kranglefant.tumblr.com/rss",
            "http://feeds.feedburner.com/kjempekjektcom",
            "http://feeds.aigamedev.com/AiGameDev",
            "http://zerosecurity.org/feed/",
            "http://www.xylibox.com/feeds/posts/default"
        ]

        for feed in feeds:
            f = Feed(feed_url=feed, last_checked=1, subscribers=1, title=feed)
            db_session.add(f)

        db_session.commit()
        self.assertEqual(1, 1)


    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
