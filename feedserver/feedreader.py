from xml.sax import SAXException

__author__ = 'sis13'

import threading
import Queue
import time

import logging
import feedparser
from time import mktime
from feedserver.config import config


logger = logging.getLogger(config.get("log_app"))


def feed_requester(feed_url):
    """ This function handles the requesting and parsing of the feed. The feed is requested and parsed using feedparser.
        If the function is successful it will return a list of dicts for each entry in the feed. If the function is not
        successful it shall return None.
    """
    d = None
    try:
        d = feedparser.parse(feed_url, agent=config.get("User-agent"))
    except SAXException as errno:
        logger.debug("Failed to retrive {0}\nTraceback:\n{1}".format(feed_url, errno))

    if not d:
        logger.debug("Failed to retrive {0}\n".format(feed_url))
        return None

    if d.bozo:
        logger.debug("Failed to retrive {0}, Bozo error.\n".format(feed_url))
        return None

    post_list = []
    for entry in d.entries:

        try:
            post = {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", "#"),
                "id": entry.get("id", "No Id"),
                "published": mktime(entry.get("published_parsed", time.struct_time)),
                "updated": mktime(entry.get("updated_parsed", time.struct_time)),
                "description": entry.get("description", ""),
                "content": entry.get("content", [{}])[0].get("value", entry.get("description", "")),
            }
        except Exception as errno:
            logger.error(errno)

            continue

        post_list.append(post)

    return feed_url, post_list


class ReaderThread(threading.Thread):
    """ FeedReader is a worker thread that takes a feed url from the
        feed queue. It attempts to request and parse the feed and
        will place the result dict in the result queue if successful.
        If the worker can not successfully retrieve the feed or parse
        it, the feed url will be added to the error queue.
    """
    def __init__(self, feed_q, result_q, error_q):
        super(ReaderThread, self).__init__()
        self.feed_q = feed_q
        self.result_q = result_q
        self.error_q = error_q
        self.stoprequest = threading.Event()
        logger.debug("ReaderThread ID:{0} started.".format(threading.current_thread()))

    def run(self):
        """
            Run method for the thread, takes a item of the queue here.
        """
        while not self.stoprequest.isSet():
            try:
                feed_url = self.feed_q.get(True, 0.05)

                feed_data = feed_requester(feed_url)

                if feed_data:
                    self.result_q.put(feed_data)

                else:
                    self.error_q.put(feed_url)

            except Queue.Empty:
                continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(ReaderThread, self).join(timeout)