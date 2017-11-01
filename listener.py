import json
from datetime import datetime

import tornado.gen
import tornado.iostream
import tornado.tcpserver
import tornadoredis

from utils.redis_connection import conn
from utils.tcpclient import TCPClient

c = tornadoredis.Client()
c.connect()

def serializer(line):
    bytes_line = line.strip()

    msg_number = int.from_bytes(bytes([bytes_line[1], bytes_line[2]]), byteorder='big')
    device_name = bytes_line[3:10].decode('ascii')
    status_id = int.from_bytes(bytes([bytes_line[11],]), byteorder='big')
    device_status = ''
    if status_id == 1:
        device_status = 'IDLE'
    elif status_id == 2:
        device_status = 'ACTIVE'
    elif status_id == 3:
        device_status = 'RECHARGE'
    numfields = int.from_bytes(bytes([bytes_line[12],]), byteorder='big')

    start_byte = 13
    messages = {}
    for _ in range(numfields):
        chunk = bytes_line[start_byte:start_byte+12]
        messages.update({chunk[:8].decode('ascii'): int.from_bytes(bytes([x for x in chunk[4:]]), byteorder='big')})
        if not _ == numfields-1:
            start_byte += 12

    xor_byte = bytes_line[start_byte+1]

    return (
        msg_number, device_name, device_status, numfields, messages, xor_byte
    )



class TCPListenerClient(TCPClient):
    client_id = 0

    def __init__(self, stream):
        super().__init__(stream)
        TCPListenerClient.client_id += 1
        self.id = TCPListenerClient.client_id

    @tornado.gen.coroutine
    def dispatch_client(self):
        try:
            while True:
                line = yield self.stream.read_until(b'\n')
                message = serializer(line)
                self.device_name = message[1]
                if message and message[0]:
                    answer = b'\x11'+message[0].to_bytes(2, byteorder='big')
                    if not conn.hgetall('device_'+message[1]):
                        conn.hmset('device_'+message[1], {
                            'device_name': message[1],
                            'id': message[0],
                            'status': message[2],
                            'time': datetime.now()
                        })
                    else:
                        conn.hset('device_'+message[1], 'id', message[0])
                        conn.hset('device_'+message[1], 'status', message[2])
                        conn.hset('device_'+message[1], 'time', datetime.now())
                else:
                    answer = b'\x12\x00\x00'
                yield self.stream.write(answer)
                c.publish('cnodr_pipe', json.dumps(message))
        except tornado.iostream.StreamClosedError:
            pass

    @tornado.gen.coroutine
    def on_disconnect(self):
        self.log("disconnected")
        conn.hdel('device_'+self.device_name, 'device_name', 'id', 'status', 'time')
        yield []

class TCPListenerServer(tornado.tcpserver.TCPServer):

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        """
        Called for each new connection, stream.socket is
        a reference to socket object
        """
        connection = TCPListenerClient(stream)
        yield connection.on_connect()