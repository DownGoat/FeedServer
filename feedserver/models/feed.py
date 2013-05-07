__author__ = 'sis13'

from feedserver.database import Model
from sqlalchemy import Column, Integer, String, Float


class Feed(Model):
    __tablename__ = "feed"
    id = Column('id', Integer, primary_key=True)
    feed_url = Column(String(1024))
    last_checked = Column(Integer)
    subscribers = Column(Integer)
    title = Column(String(128))
    update_frequency = Column(Integer)
    favicon = Column(String(1024))
    metadata_update = Column(Integer)

    def __init__(self, update_frequency, favicon, feed_url=None, last_checked=1, subscribers=1, title=u"Some feed",
                 metadata_update=1):
        self.feed_url = feed_url
        self.last_checked = last_checked
        self.subscribers = subscribers
        self.title = title
        self.update_frequency = update_frequency
        self.favicon = favicon
        self.metadata_update = metadata_update
