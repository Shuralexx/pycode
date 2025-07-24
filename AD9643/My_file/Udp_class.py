import socket
class UdpAchieve:
    def __init__(self):
        self.server_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.server_address=('10.32.30.159',8000)
    def open(self):
        print('Successfully Open !')
        self.server_socket.bind(self.server_address)
    def read(self):
        while True:
            data,client_address = self.server_socket.recvfrom(4096)
            print(f"接收到来自 {client_address} 的数据: {data.hex(' ').upper()}")

    def close(self):
        self.server_socket.close()
