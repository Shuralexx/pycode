import serial
import threading

def com1_listener(ser, ser2):
    """
    监听COM1,收到握手命令后让COM2自动回复
    """
    import time
    while True:
        if ser.in_waiting >= 10:
            rx = ser.read(10)
            print("[com1_listener] 收到数据:", list(rx))  # 调试输出
            # 补全命令长度为10字节
            handshake_cmd = [0x55, 0xAA, 0x0F, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44, 0x00]
            reply = bytes([0x55, 0xAA, 0xF0, 0x01, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44, 0x00])
            if list(rx) == handshake_cmd:
                ser2.write(reply)
                print(f"COM2已向COM1发送应答: {list(reply)}")
        else:
            time.sleep(0.01)

