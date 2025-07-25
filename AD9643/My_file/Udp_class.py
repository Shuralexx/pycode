import socket

class UdpAchieve:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('10.32.30.159', 8000)
        self.rx_data = []           # 新增：用于保存最后一帧ADC原始数据
        self.latest_hex = ""        # 可选：记录原始hex字符串

    def open(self):
        print('Successfully Open !')
        self.server_socket.bind(self.server_address)

    def read(self):
        while True:
            data, client_address = self.server_socket.recvfrom(4096)
            print(f"接收到来自 {client_address} 的数据: {data.hex(' ').upper()}")
            self.latest_hex = data.hex(' ').upper()
            # 假定data就是原始ADC数据（如字节流），下面将其转为int列表
            # 你需要根据你的数据格式决定解码方式，下面假设每2字节为1个采样点（16bit），高字节在前
            if len(data) % 2 == 0:
                self.rx_data = [int.from_bytes(data[i:i+2], byteorder='big', signed=True)
                                for i in range(0, len(data), 2)]
            else:
                # 数据长度不是偶数时，不解码
                self.rx_data = []

    def close(self):
        self.server_socket.close()

