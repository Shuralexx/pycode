import serial
import serial.tools.list_ports_windows


class SerialAchieve:
    def __init__(self):
        self.ser = None
        self.port = None
        self.port_list = list(serial.tools.list_ports_windows.comports())
        #assert (len(self.port_list) != 0), '无可用串口'
        self.bold_rate = 115200

    def port_get(self):
        return self.port_list

    def open_port(self):
        if self.ser is None:
            self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
        if self.ser.is_open:
            print(self.port + "串口已经打开！")
        else:
            self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
            print(self.port + "串口已经打开！")

    def close_port(self):
        if self.ser.is_open:
            self.ser.close()
            if self.ser.is_open:
                print("串口关闭失败！")
            else:
                print("串口成功关闭！")
