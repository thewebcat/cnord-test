import tornado.gen
import tornado.ioloop
import tornado.iostream
import tornado.tcpserver

from listener import TCPListenerServer
from sender import TCPSenderServer


def main():
    # configuration
    host = '0.0.0.0'
    listener_port = 7777
    sender_port = 7779

    # tcp server
    listener_server = TCPListenerServer()
    listener_server.listen(listener_port, host)
    # tcp server
    sender_server = TCPSenderServer()
    sender_server.listen(sender_port, host)
    print("Listening on %s:%d..." % (host, listener_port))
    print("Listening on %s:%d..." % (host, sender_port))

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    main()
