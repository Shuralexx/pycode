# import socket
# #此为远程服务器 （远端IP（PC））
# # # 创建UDP套接字                                                                                     class SerialAchieve:
#                                                                                                         def __init__(self):
#                                                                                                             self.ser = None
#                                                                                                             self.port = None
#                                                                                                             self.port_list = list(serial.tools.list_ports_windows.comports()) # 获取串口列表
#                                                                                                             #assert (len(self.port_list) != 0), '无可用串口'
#                                                                                                             self.bold_rate = 115200 # 设置波特率

#                                                                                                         def port_get(self):
#                                                                                                             return self.port_list

#                                                                                                         def open_port(self):
#                                                                                                             if self.port is None:
#                                                                                                                 print("错误：没有选择串口！")
#                                                                                                                 return
                                                                                                            
#                                                                                                             try:
#                                                                                                                 if self.ser is None:
#                                                                                                                     self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
#                                                                                                                 if self.ser.is_open:
#                                                                                                                     print(f"{self.port} + 串口已经打开！")
#                                                                                                                 else:
#                                                                                                                     self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
#                                                                                                                     print(f"{self.port} + 串口已经打开！")
#                                                                                                             except serial.SerialException as e:
#                                                                                                                 print(f"打开串口失败: {e}")

#                                                                                                         def close_port(self):
#                                                                                                             if self.ser is not None and self.ser.is_open:
#                                                                                                                 self.ser.close()
#                                                                                                                 if self.ser.is_open:
#                                                                                                                     print("串口关闭失败！")
#                                                                                                                 else:
#                                                                                                                     print("串口成功关闭！")
#                                                                                                             else:
                                                                                                                # print("串口未打开，无需关闭。")
# server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)           

# # 绑定地址和端口
# server_address = ('localhost', 8000)
# server_socket.bind(server_address)

# print(f"UDP服务器启动，监听 {server_address}")

# while True:
#     # 接收数据
#     data, client_address = server_socket.recvfrom(4096)#接收最多4096字节的数据包
#     print(f"接收到来自 {client_address} 的数据: {data.decode()}")
#     # 如果接收到的数据为"exit"则退出服务器
#     if data.decode().lower() == "exit":
#         print("服务器关闭")
#         break
#     # 可以发送响应数据
#     server_socket.sendto("data has been received".encode(), client_address)

# # 关闭服务器
# server_socket.close()
import socket
class UdpAchieve:
    def __init__(self):
        self.server_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.server_address=('127.0.0.1',8000)
    def open(self):
        print('Successfully Open !')
        self.server_socket.bind(self.server_address)
    def read(self):
        while True:
            data,client_address = self.server_socket.recvfrom(4096)
            print(f"接收到来自 {client_address} 的数据: {data.decode()}")

    def close(self):
        self.server_socket.close()
