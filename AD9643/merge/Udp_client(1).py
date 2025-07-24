import socket
import time
# def main():
#     # udp 通信地址，IP+端口号
#     udp_addr = ('127.0.0.1', 9999)
#     udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#     # 发送数据到指定的ip和端口,每隔1s发送一次，发送10次
#     for i in range(10):
#         udp_socket.sendto(("Hello,I am a UDP socket for: " + str(i)) .encode('utf-8'), udp_addr)
#         print("send %d message" % i)
#         sleep(1)

#     # 5. 关闭套接字
#     udp_socket.close()
class Udpclient:
    def __init__(self):
        self.ClientSocket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp_addr =('127.0.0.1',8000)
    def send(self):
        for i in range(10):
            self.ClientSocket.sendto(("Hello,I am a UDP socket for: " + str(i)) .encode('utf-8'), self.udp_addr)
            print("send %d message"%i)
            time.sleep(1)
