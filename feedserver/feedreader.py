from xml.sax import SAXException
import threading
import Queue
import time
from urlparse import urlparse
import logging
import feedparser
from feedserver.config import config
from feedserver.database import engine
from sqlalchemy.orm import scoped_session, sessionmaker

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
        logger.info("{0}, Bozo error: {1}.\n".format(feed_url, d.bozo_exception))

        if not bozo_checker(d.bozo_exception):
            return None

    post_list = []
    for entry in d.entries:

        try:
            post = {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", "#"),
                "id": entry.get("id", "No Id"),
                "published": time_parser(entry.get("published_parsed")),
                "updated": time_parser(entry.get("updated_parsed"), update_time=True),
                "description": entry.get("description", ""),
                "content": entry.get("content", [{}])[0].get("value", entry.get("description", "")),
            }
        except Exception as errno:
            logger.error("Something went wrong in feed_requester: {0}".format(errno))

            continue

        post_list.append(post)

    feed_data = {"parser_object": d, "posts": post_list}

    return feed_data


def time_parser(time_str, update_time=False):
    """
    This function parses the time str from feedparser. Feeds may not
    always include the time for update, and published. So if it is
    in the feed the current time will be set for those values.

    If the update time is missing for the feed the function will set it
    to 1. If the current time is used it will end up wrong in the DB if
    the entry already exist in the DB.

    :param time_str The time str to be parsed.

    :param update_time Set to true if it is the update time that is parsed.

    :return UNIX timestamp
    """

    if time_str is None:
        if update_time:
            return 1
        else:
            return time.time()

    else:
        return time.mktime(time_str)


def bozo_checker(bozo_exception):
    """
    This function checks if the bozo exception is a critical exception or
    a exception that can be ignored.

    :param bozo_exception The bozo exception to test.
    """
    # Will return false by default, so only whitelisted exceptions will
    # return true.
    return_val = False

    # This exception is raised when the feed was decoded and parsed using a different encoding than what the server/feed
    # itself claimed it to be.
    if isinstance(bozo_exception, feedparser.CharacterEncodingOverride):
        return_val = True

    return return_val


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

        self.db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

        logger.debug("ReaderThread ID:{0} started.".format(threading.current_thread()))

    def run(self):
        """
            Run method for the thread, takes a item of the queue here.
        """
        while not self.stoprequest.isSet():
            try:
                feed = self.feed_q.get(True, 0.05)[1]
                self.db_session.add(feed)
                feed_url = feed.feed_url

                feed_data = feed_requester(feed_url)

                if feed_data is not None and feed_data.get("posts"):
                    #The feed persister expects the data in (feed_url, post_list) format.
                    self.result_q.put((feed_url, feed_data.get("posts")))

                    #Check if the feed is a new feed.
                    if feed.metadata_update is 1:
                        logger.debug("{0} is a new feed.".format(feed_url))
                        self.update_metadata(feed, feed_data)

                    elif self.days_since(time.time(), feed.metadata_update) >= config.get("metadata_update"):
                        self.update_metadata(feed, feed_data)
                else:
                    self.error_q.put(feed_url)

            except Queue.Empty:
                continue

            finally:
                self.db_session.commit()

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
        self.db_session.commit()

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