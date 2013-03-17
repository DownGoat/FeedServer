import time

__author__ = 'sis13'
import unittest
import Queue
import threading
import feedserver

from feedserver import feedstorer
from feedserver import  feedreader

class TestFeedstorer(unittest.TestCase):

    def setUp(self):
        self.result_q = Queue.Queue()
        self.feed_q = Queue.Queue()
        self.error_q = Queue.Queue()
        self.feed_url = "http://downgoat.net/feed/"
        self.pool = [feedstorer.FeedPersistenceThread(self.result_q) for x in range(1)]

        for t in self.pool:
            t.start()

    """def test_add(self):
        var = {'updated': 1462247373,

               'description': u'For a assignment I needed player/stage, and it turned out installing it is no easy task. A fellow student taking the module made a script for automating the installation, and it should work on Ubuntu 11.04, 12.04, 12.10 and Linux &#8230; <a href="http://downgoat.net/2013/03/02/installing-playerstage-ubuntulinux-mint/">Continue reading <span class="meta-nav">&#8594;</span></a>',

               'title': u'Installing Player/Stage Ubuntu/Linux Mint',

               'content': u'<p>For a assignment I needed player/stage, and it turned out installing it is no easy task.<br />\nA fellow student taking the module made a script for automating the installation, and it should work on Ubuntu 11.04, 12.04, 12.10 and Linux Mint 14.</p>\n<p>The script can be found on his GitHub <a href="https://github.com/samueljackson92/player-stage-install-script.git" title="https://github.com/samueljackson92/player-stage-install-script.git">https://github.com/samueljackson92/player-stage-install-script.git</a></p>\n<p>A mirror can be found here <a href="http://downgoat.net/wp-content/uploads/2013/03/player-stage-install-script-master.zip">player-stage-install-script-master</a>.</p>\n <p><a href="http://downgoat.net/?flattrss_redirect&amp;id=153&amp;md5=62b2a12f3159b180746b0228542d25aa" target="_blank" title="Flattr"><img alt="flattr this!" src="http://downgoat.net/wp-content/plugins/flattr/img/flattr-badge-large.png" /></a></p>',
               'link': "asd",
               'published': 1362247373.0,
               'id': 'http://downgoat.net/?p=153'}

        self.result_q.put((self.feed_url, [var]))"""

    def test_threader(self):
        # TODO write a real test for this.
        frt = feedreader.ReaderThread(self.feed_q, self.result_q, self.error_q)
        frt.start()

        self.feed_q.put(self.feed_url)
        time.sleep(10)
        self.assertTrue(True)


    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
