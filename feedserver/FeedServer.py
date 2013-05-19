__author__ = 'sis13'

import Queue
import logging
import time
import threading

from feedserver.config import config
from feedserver.database import db_session
import feedreader
import feedstorer
from feedserver.models.entry import Entry
from feedserver.models.feed import Feed

logger = logging.getLogger(config.get("log_app"))


class FeedServer():
    def __init__(self):
        pass

    def start_reader_thread(self):
        t = feedreader.ReaderThread(self.feed_q, self.result_q, self.error_q)
        t.start()
        self.reader_pool.append(t)

    def startup(self):
        """
            This method is does the startup routine for the application. It will launch the threads and set up the
            queues. The number of threads to use is defined in the config (config.py).
        """
        logger.info("Server is now starting.")
        self.result_q = Queue.Queue()
        self.feed_q = Queue.PriorityQueue()
        self.error_q = Queue.Queue()

        #Start the reader threads.
        self.reader_pool = []
        for x in range(config.get("reader_threads")):
            self.start_reader_thread()

        logger.info("Started {0} ReaderThread threads.".format(config.get("reader_threads")))

        #Start db thread.
        self.db_thread = feedstorer.FeedPersistenceThread(self.result_q)
        self.db_thread.start()
        logger.info("Started FeedPersistenceThread.")

        logger.info("Server has now started.")

    def get_feeds(self):
        """
            Gets feeds that needs to be updated from the database. The update frequency aka how many minutes between
            each time to request the feed, is defined in the config (config.py). The method will update the last_checked
            column of the feed after is has put it on the queue.
        """
        # Get the unix timestamp used to filter feeds.
        # Any feed with last checked value less than this need to be updated.

        update_time = (time.time()) - (config.get("update_frequency") * 60)

        #TODO add exception handling here. IF NEEDED!
        feeds = db_session.query(Feed).filter(Feed.last_checked <= int(update_time)).all()

        for feed in feeds:
            logger.debug("Putting feed on the queue: {0} with priority {1}.".format(feed.feed_url, feed.last_checked))
            db_session.expunge(feed)
            self.feed_q.put((feed.last_checked, feed))

            db_session.query(Feed).filter_by(id=feed.id).update({
                "last_checked": time.time(),
            })

            logger.debug("Updating feed last_checked: {0}".format(feed.feed_url))

            db_session.commit()

    def run(self):
        """
            Run method for the application. Will try and fetch feeds to update once every second..
        """
        while True:
            logger.debug("Fetching feeds to update.")
            self.get_feeds()

            logger.debug("There are {0} threads currently active.".format(threading.active_count()))

            #Check if threads are still up and running.
            for frt in self.reader_pool:
                if not frt.is_alive():
                    logger.debug("Thread is not alive, starting a new one. Dead thread:{0}".format(frt))

                    if threading.active_count() <= config.get("reader_threads") + 2:
                        self.start_reader_thread()

                    frt.join()

            if not self.db_thread.is_alive():
                logger.debug("DB thread is not alive, starting new one. Old: {0}".format(self.db_thread))
                self.db_thread = feedstorer.FeedPersistenceThread(self.result_q)
                self.db_thread.start()

            time.sleep(1)

