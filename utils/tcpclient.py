import socket

import tornado.gen


class TCPClient(object):

    def __init__(self, stream):
        super().__init__()
        self.stream = stream

        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.SO_KEEPALIVE, 1)
        self.stream.set_close_callback(self.on_disconnect)


    @tornado.gen.coroutine
    def on_disconnect(self):
        self.log("disconnected")
        yield []

    @tornado.gen.coroutine
    def dispatch_client(self):
        pass

    @tornado.gen.coroutine
    def on_connect(self):
        raddr = 'closed'
        try:
            raddr = '%s:%d' % self.stream.socket.getpeername()
        except Exception:
            pass
        self.log('new, %s' % raddr)

        yield self.dispatch_client()

    def log(self, msg, *args, **kwargs):
        print('[listener connection %d] %s' % (self.id, msg.format(*args, **kwargs)))