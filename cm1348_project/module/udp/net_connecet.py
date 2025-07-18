import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('0.0.0.0', 8000)  # 监听所有网卡
server_socket.bind(server_address)

print(f"UDP服务器启动,监听 {server_address}")

while True:
    data, client_address = server_socket.recvfrom(4096)
    print(f"接收到来自 {client_address} 的数据: {data.hex()}")

    # 处理本地IP配置命令
    if data == bytes([0xAA, 0x30, 0x00, 0x04, 0x00, 0x0A, 0x20, 0x1E, 0x32, 0x00]):#AA 30 00 04 00 0A 20 1E 32 00
        reply = bytes([0x55, 0x30, 0x00, 0x01, 0x00, 0x00, 0x62])
        server_socket.sendto(reply, client_address)
        print("已回复本地IP配置应答")
    # 处理远端IP配置命令
    elif data == bytes([0xAA, 0x31, 0x00, 0x04, 0x00, 0x0A, 0x20, 0x1E, 0x33, 0x00]):#AA 31 00 04 00 0A 20 1E 33 00
        reply = bytes([0x55, 0x31, 0x00, 0x01, 0x00, 0x00, 0x63])
        server_socket.sendto(reply, client_address)
        print("已回复远端IP配置应答")
    # 退出命令
    elif data.decode(errors='ignore').lower() == "exit":
        print("服务器关闭")
        break
    else:
        server_socket.sendto(b"data has been received".encode(), client_address)

server_socket.close()