import socket
#此为远程服务器 （远端IP（PC））
# 创建UDP套接字
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定地址和端口
server_address = ('localhost', 8000)
server_socket.bind(server_address)

print(f"UDP服务器启动，监听 {server_address}")

while True:
    # 接收数据
    data, client_address = server_socket.recvfrom(4096)#接收最多4096字节的数据包
    print(f"接收到来自 {client_address} 的数据: {data.decode()}")
    # 如果接收到的数据为"exit"则退出服务器
    if data.decode().lower() == "exit":
        print("服务器关闭")
        break
    # 可以发送响应数据
    server_socket.sendto("data has been received".encode(), client_address)

# 关闭服务器
server_socket.close()
