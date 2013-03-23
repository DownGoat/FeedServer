FeedServer
==========

FeedServer is a server application for monitoring several RSS/Atom feeds, and storing entries made in a database.
The project was started after Google announced the death of Google Reader, which was awesome. The FeedServer will
be the back end of a similar type of application, although currently it is not yet there. As for now it is a hobby
project and will continue to be so for quite a while.

TODO
====
It needs more testing firstly, a lot of cases has not been tested yet, epsecially how it will preform when encountering 
malformed feeds, unicode (japanese/chinese characters), and security. All of theese needs to be tested to see how the 
application preforms. The plan is todo some of the testing when the PyFeedReader is up and running on a basic level,
(Can fetch and display feed entries from DB).

How it works
============
The feeds you wish to monitor is entered into the database, FeedServer can not enter feeds into the database itself,
and will not get the feature todo so. It is meant to be a application that simply monitors and stores new entries
from feeds.

The server currently consists of 3 parts, the reader threads, the database thread , and the main thread.
The reader and database threads are started when the server starts, then the main thread pulls feeds that
needs to be updated from the database and puts them on the feed queue. The reader threads then pulls any feeds
of the feed queue and attempts to requests the feeds, if it successful any results are stored on a result queue.
The database thread then monitors the result queue and will add or update any entries to the database.

The server can be configured by editing the config.py file where the database settings,
and threads settings are stored.

How to run it
=============
Requirements:
Python 2.7  		            Only tested python version, might work on others.

feedparser			            http://code.google.com/p/feedparser/

MySQL or other database.	    only tested with MySQL so far.

SQLAlchemy			            http://www.sqlalchemy.org/

To create the database first edit the settings in config.py, then open the python interpreter in FeedServer
directory and do:

from feedserver import database

database.init_db()


After that you will need to enter any feeds you wish to monitor into the feed table.

The server can be started by simply running the FeedServer.py file in the FeedServer directory.
