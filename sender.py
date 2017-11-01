import json
from datetime import datetime

import tornado.gen
import tornado.tcpserver
import tornadoredis

from listener import TCPListenerClient
from utils.redis_connection import conn
from utils.tcpclient import TCPClient


class TCPSenderClient(TCPClient):
    client_id = 0

    def __init__(self, stream):
        super().__init__(stream)
        TCPSenderClient.client_id += 1
        self.id = TCPSenderClient.client_id
        self.client = tornadoredis.Client()
        self.client.connect()

    def show_new_message(self, result):
        if result.body == 1:
            msg = ''
            connections_keys = conn.keys('device_*')
            print(connections_keys)
            if connections_keys:
                for item in connections_keys:
                    connection = conn.hgetall(item)
                    timedelta = datetime.now() - datetime.strptime(connection[b'time'].decode(), "%Y-%m-%d %H:%M:%S.%f")
                    msg += '[{0}] {1} | {2} | {3}\n'.format(
                        connection[b'device_name'],
                        connection[b'id'],
                        connection[b'status'],
                        timedelta.microseconds
                    )
            else:
                msg = 'Hello clinet, there are: {0} connected devices\n'.format(str(TCPListenerClient.client_id))
            self.stream.write(bytes(msg, 'utf-8'))
        else:
            response = json.loads(result.body)
            kv_list = ''
            for key, value in response[4].items():
                kv_list += '{0} {1}\n'.format(key, value)
            self.stream.write(bytes(response[1] + '\n' + kv_list, 'utf-8'))

    @tornado.gen.coroutine
    def on_connect(self):
        raddr = 'closed'
        try:
            raddr = '%s:%d' % self.stream.socket.getpeername()
        except Exception:
            pass
        self.log('new, %s' % raddr)
        yield tornado.gen.Task(self.client.subscribe, 'cnodr_pipe')
        self.client.listen(self.show_new_message)

    def log(self, msg, *args, **kwargs):
        print('[sender connection %d] %s' % (self.id, msg.format(*args, **kwargs)))


class TCPSenderServer(tornado.tcpserver.TCPServer):

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        """
        Called for each new connection, stream.socket is
        a reference to socket object
        """
        connection = TCPSenderClient(stream)
        yield connection.on_connect()