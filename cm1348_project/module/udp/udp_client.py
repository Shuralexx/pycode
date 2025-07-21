import socket

# 创建UDP套接字
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 服务器地址
server_address = ('localhost', 8000)

# 发送数据
message = "Hello, Server!"
client_socket.sendto(message.encode(), server_address)

# 接收服务器响应
data, server = client_socket.recvfrom(4096)
print(f"接收到服务器响应: {data.decode()}")

# 关闭客户端
client_socket.close()
