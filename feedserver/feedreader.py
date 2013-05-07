from xml.sax import SAXException
import threading
import Queue
import time
from urlparse import urlparse
import logging
import feedparser
from time import mktime
from feedserver.config import config
from feedserver.database import db_session

__author__ = 'Sindre Smistad'


logger = logging.getLogger(config.get("log_app"))


def feed_requester(feed_url):
    """ This function handles the requesting and parsing of the feed. The feed is requested and parsed using feedparser.
        If the function is successful it will return a list of dicts for each entry in the feed. If the function is not
        successful it shall return None.

        :param feed_url The url of the feed to retrieve.
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

    feed_data = {"parser_object": d, "posts": post_list}

    return feed_data


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
                feed = self.feed_q.get(True, 0.05)
                feed_url = feed.feed_url

                feed_data = feed_requester(feed_url)

                if feed_data.get("posts"):
                    #The feed persister expects the data in (feed_url, post_list) format.
                    self.result_q.put((feed_url, feed_data.get("posts")))

                else:
                    self.error_q.put(feed_url)

                #Check if the feed is a new feed.
                if feed.metadata_update == 1:
                    logger.debug("{0} is a new feed.".format(feed_url))
                    self.update_metadata(feed, feed_data)

                elif self.days_since(time.time(), feed.metadata_update) >= config.get("metadata_update"):
                    self.update_metadata(feed, feed_data)

            except Queue.Empty:
                continue

    def update_metadata(self, feed, feed_data):
        """
        This method updates the metadata of a feed, this function should be called if the feed is a feed that newly has
        been added to the system, or if it has been longer than n days since last update. N days is defined in the
        config. This method returns nothing.

        :param feed The feed object to change the metadata for.

        :param feed_data The resulting dict from a feed_requester call.
        """
        parser = feed_data.get("parser_object")
        feed.last_checked = time.time()
        feed.metadata_update = time.time()
        feed.subscribers = 1
        feed.title = parser.feed.get("title", "Unknown title")

        #Some feeds has a update frequency data, lets have FeedServer be nice and try and follow this.
        feed.update_frequency = parser.feed.get("sy_updatefrequency", None)
        if not feed.update_frequency:
            logger.debug("{0} has not set a updateFrequency.".format(feed.feed_url))
            feed.update_frequency = 2

        else:
            try:
                feed.update_frequency = int(feed.update_frequency)
            except ValueError:
                logger.error("Invalid update_frequency value {0} for {1}").format(feed.update_frequency, feed.feed_url)

        netloc = urlparse(feed.feed_url)
        feed.favicon = "{0}/favicon.ico".format(netloc.netloc)

        # This commit seems to be useless? Does not actually update the feed record.
        db_session.commit()

    def days_since(self, t1, t2):
        """
        Returns the number of days between the two timestamps.

        :param t1 Time one.
        :param t2 Time two.
        """
        seconds_diff = t1 - t2
        return int(seconds_diff / 86400)  # 86400 is the number of seconds in a day.


def join(self, timeout=None):
        self.stoprequest.set()
        super(ReaderThread, self).join(timeout)