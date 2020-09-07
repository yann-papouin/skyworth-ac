"""

UDP BROADCAST To port 1995
DATA = 0000   be 01
"\xbe\x01"
char packet_bytes[] = {
  0xbe, 0x01
};

"""

import socket
import struct

TCP_IP = '192.168.10.22'
TCP_PORT = 1998
BUFFER_SIZE = 1024


def byte2sbyte(value):
    if value > 127:
        return (256 - value) * (-1)
    else:
        return value


def sbyte2byte(value):
    if value < 0:
        return 256 + value
    else:
        return value


def barray2sblist(value):
    return [byte2sbyte(x) for x in list(value)]


test = [0x7a, 0x7a, 0x21, 0xd5, 0x0c, 0x00, 0x00, 0xa2, 0x0a, 0x0a, 0xfe, 0x29]

MESSAGE = bytearray(test)

light_on = [
    0x7a, 0x7a, 0x21, 0xd5, 0x18, 0x00, 0x00, 0xa1, 0x0a, 0x0a, 0x00, 0x00,
    0x04, 0x48, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa3, 0x3a
]

MESSAGE = bytearray(light_on)

light_off = [
    0x7a, 0x7a, 0x21, 0xd5, 0x18, 0x00, 0x00, 0xa1, 0x0a, 0x0a, 0x00, 0x00,
    0x04, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x6b, 0xbb
]

MESSAGE = bytearray(light_off)

print("MESSAGE:", barray2sblist(MESSAGE))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
#s.shutdown(socket.SHUT_WR)
data = s.recv(BUFFER_SIZE)
s.close()

LIGHTOFF = 121
LIGHTON = 120
AirConditionADDR = 33
WIFIADDR = -47


print("received data:", barray2sblist(data))
