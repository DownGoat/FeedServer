from sqlalchemy.exc import ProgrammingError
from feedserver.models.feed import Feed

__author__ = 'sis13'
import logging
import threading
import Queue
import time

from feedserver.config import config
from feedserver.database import db_session
from feedserver.models.entry import Entry

logger = logging.getLogger(config.get("log_app"))


def add_entry(entry, feed_id):
    stored_ent = db_session.query(Entry).filter_by(link=entry.get("link")).first()

    #Even if it is in db it might be updated since last time.
    if stored_ent is not None and stored_ent.updated == entry.get("updated"):
        return

    if stored_ent:
        db_session.query(Entry).filter_by(id=stored_ent.id).update(
            {
                "published": entry.get("published"),
                "updated": entry.get("updated"),
                "title": entry.get("title"),
                "content": entry.get("content"),
                "description": entry.get("description"),
                "link": entry.get("link"),
                "remote_id": entry.get("id"),
                "feed_id": feed_id,
                })

        logger.debug("Updating entry with id: {0}".format(entry.get("id")))

        db_session.commit()

    else:
        new_entry = Entry(
            published=entry.get("published"),
            updated=entry.get("updated"),
            title=entry.get("title"),
            content=entry.get("content"),
            description=entry.get("description"),
            link=entry.get("link"),
            remote_id=entry.get("id"),
            feed_id=feed_id
            )

        logger.debug(u"Adding new entry with id: {0}".format(entry.get("id")))

        db_session.add(new_entry)
        db_session.commit()


class FeedPersistenceThread(threading.Thread):
    """
        This is the database thread. It will take any results that are in the results queue and store the entries in the
        database. The class does not have the functionality to store the entries itself, but it calls the add_entry
        function to persist the data.
    """
    def __init__(self, result_q):
        super(FeedPersistenceThread, self).__init__()
        self.result_q = result_q
        self.stoprequest = threading.Event()
        logger.debug("FeedPersistenceThread ID:{0} started.".format(threading.current_thread()))

    def run(self):
        while not self.stoprequest.isSet():
            try:
                entries = self.result_q.get(True, 0.05)

                feed = None
                try:
                    feed = db_session.query(Feed).filter_by(feed_url=entries[0]).first()
                except ProgrammingError as errno:
                    logger.critical("SQL error, Traceback:\n{0}".format(errno))
                    continue

                if feed is None:
                    logger.error("No feed ID found for feed {0}".format(entries[0]))
                    continue

                for entry in entries[1]:
                    add_entry(entry, feed.id)

            except Queue.Empty:
                continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(FeedPersistenceThread, self).join(timeout)

