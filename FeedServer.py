__author__ = 'sis13'

from feedserver import FeedServer


if __name__ == "__main__":
    app = FeedServer.FeedServer()
    app.startup()
    app.run()