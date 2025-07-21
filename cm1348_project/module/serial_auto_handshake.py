import serial
import threading

def com1_listener(ser1, ser2):
    """
    监听COM1，收到握手命令后让COM2自动回复
    """
    while True:
        rx = ser1.read(10)
        if rx and list(rx) == [0x55, 0xAA, 0x0F, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]:
            # COM2发送握手应答
            reply = bytes([0x55, 0xAA, 0xF0, 0x01, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44])
            ser2.write(reply)
            print(f"COM2已向COM1发送应答: {list(reply)}")

if __name__ == "__main__":
    # 打开串口（根据实际端口号修改）
    ser1 = serial.Serial("COM1", 115200, timeout=1)
    # ser2 = serial.Serial("COM2", 115200, timeout=1)
    # 启动监听线程
    t = threading.Thread(target=com1_listener, args=ser1)
    t.daemon = True
    t.start()
    print("自动应答模块已启动。按Ctrl+C退出。")
    while True:
        pass


